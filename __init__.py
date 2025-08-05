import os
import subprocess
import folder_paths
import re
from pathlib import Path

class NVVFRNode:
    """
    ComfyUI NVVFR节点 - 使用NVEncC进行视频超分补帧
    """
    
    def __init__(self):
        self.nvenc_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "nvenc", "NVEncC64.exe")
        self.output_dir = folder_paths.get_output_directory()
        
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "output_prefix": ("STRING", {"default": "ComfyUI"}),
                "codec": (["h264", "h265"], {"default": "h265"}),
                "quality": (["high", "medium", "low"], {"default": "high"}),
                "enable_superres": ("BOOLEAN", {"default": True}),
                "superres_strength": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 1.0, "step": 0.1}),
                "enable_double_frame": ("BOOLEAN", {"default": False}),
                "width": ("INT", {"default": 1920, "min": 64, "max": 8192}),
                "height": ("INT", {"default": 1080, "min": 64, "max": 8192}),
                "depth": (["8bit", "10bit"], {"default": "10bit"}),                
            },
            "optional": {
                "video_path": ("STRING", {"default": ""}),
                "imagelist": ("STRING", {"default": ""}),
                "original_frame_rate": ("FLOAT", {"default": 30.0, "min": 1.0, "max": 120.0, "step": 0.1}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("output_path",)
    FUNCTION = "process_video"
    CATEGORY = "video/processing"

    OUTPUT_NODE = True
    
    def process_video(self, video_path, output_prefix, codec, quality, enable_superres, enable_double_frame, 
                     width=1920, height=1080, depth="10bit", superres_strength=1.0, imagelist="", original_frame_rate=30.0):
        """
        处理视频文件或图像序列
        """
        # 检查NVEncC64.exe是否存在
        if not os.path.exists(self.nvenc_path):
            raise FileNotFoundError(f"NVEncC64.exe not found at {self.nvenc_path}")
        
        # 检查video_path和imagelist不能同时为空
        if not video_path and not imagelist:
            raise ValueError("Either video_path or imagelist must be provided")
        
        # 如果有imagelist，检查original_frame_rate是否为空
        if imagelist and original_frame_rate <= 0:
            raise ValueError("original_frame_rate must be provided when imagelist is used")
        
        # 如果有video_path，检查文件是否存在
        if video_path and not os.path.exists(video_path):
            raise FileNotFoundError(f"Input video file not found: {video_path}")
        
        avs_file_path = None
        # 如果有imagelist，生成avs文件
        if imagelist:
            # 解析imagelist（假设是逗号分隔的图像路径）
            image_paths = [path.strip() for path in imagelist.split(',') if path.strip()]
            
            if not image_paths:
                raise ValueError("imagelist must contain valid image paths")
            
            # 检查图像文件是否存在
            for img_path in image_paths:
                if not os.path.exists(img_path):
                    raise FileNotFoundError(f"Image file not found: {img_path}")
            
            # 在ComfyUI临时文件夹创建avs文件
            temp_dir = folder_paths.get_temp_directory()
            avs_file_path = os.path.join(temp_dir, f"{output_prefix}_input.avs")
            
            # 生成avs文件内容（UTF-8编码）
            # 使用ImageSource处理图像序列
            if len(image_paths) == 1:
                # 单张图像
                avs_content = f"ImageSource(\"{image_paths[0]}\", fps={original_frame_rate})\n"
            else:
                # 多张图像序列
                # 提取公共路径和文件名模式
                first_path = image_paths[0]
                last_path = image_paths[-1]
                
                # 尝试提取文件名模式（假设文件名有数字序列）
                import glob
                dir_path = os.path.dirname(first_path)
                if not dir_path:
                    dir_path = "."
                
                # 获取目录中所有匹配的图像文件
                pattern = os.path.join(dir_path, "*.png")  # 支持PNG
                image_files = sorted(glob.glob(pattern))
                if not image_files:
                    pattern = os.path.join(dir_path, "*.jpg")  # 支持JPG
                    image_files = sorted(glob.glob(pattern))
                if not image_files:
                    pattern = os.path.join(dir_path, "*.jpeg")  # 支持JPEG
                    image_files = sorted(glob.glob(pattern))
                if not image_files:
                    pattern = os.path.join(dir_path, "*.bmp")  # 支持BMP
                    image_files = sorted(glob.glob(pattern))
                
                if image_files:
                    # 使用ImageSource的序列模式
                    avs_content = f"ImageSource(\"{image_files[0]}\", end={len(image_files)}, fps={original_frame_rate})\n"
                else:
                    # 回退到使用Interleave
                    avs_content = "Interleave(\n"
                    for i, img_path in enumerate(image_paths):
                        avs_content += f"  ImageSource(\"{img_path}\", fps={original_frame_rate})"
                        if i < len(image_paths) - 1:
                            avs_content += ",\n"
                        else:
                            avs_content += "\n"
                    avs_content += ")\n"
            
            # 写入avs文件（UTF-8编码）
            with open(avs_file_path, 'w', encoding='utf-8') as f:
                f.write(avs_content)
            
            print(f"Generated AVS file: {avs_file_path}")
        
        # 检查编码器和深度的兼容性
        if codec.lower() == "h264" and depth.lower() == "10bit":
            print("Warning: H.264 codec does not support 10-bit depth. Forcing to 8-bit depth.")
            depth = "8bit"

        max_counter = 0

        # Loop through the existing files
        matcher = re.compile(f"{re.escape(output_prefix)}_(\\d+)\\D*\\..+", re.IGNORECASE)
        for existing_file in os.listdir(self.output_dir):
            # Check if the file matches the expected format
            match = matcher.fullmatch(existing_file)
            if match:
                # Extract the numeric portion of the filename
                file_counter = int(match.group(1))
                # Update the maximum counter value if necessary
                if file_counter > max_counter:
                    max_counter = file_counter

        counter = max_counter + 1
        file_name = f"{output_prefix}_{counter:05}"
        output_filename = f"{output_prefix}_{counter:05}.mp4"
        output_path = os.path.join(self.output_dir, output_filename)
        
        # 构建命令行参数
        cmd = [self.nvenc_path]
        
        # 添加编码器参数
        if codec.lower() == "h265":
            cmd.extend(["-c", "hevc"])
        else:  # h264
            cmd.extend(["-c", "h264"])
        
        # 添加质量参数
        if quality.lower() == "quality":
            cmd.extend(["-u", "P7"])
        elif quality.lower() == "medium":
            cmd.extend(["-u", "P4"])
        else:
            cmd.extend(["-u", "P1"]) 
        
        # 添加输出分辨率
        output_resolution = f"{width}x{height}"
        cmd.extend(["--output-res", output_resolution])
        
        # 添加输出深度
        if depth.lower() == "8bit":
            cmd.extend(["--output-depth", "8"])
        else:
            cmd.extend(["--output-depth", "10"])

        # 添加超分辨率参数
        if enable_superres:
            cmd.extend(["--vpp-resize", f"algo=nvvfx-superres,superres-mode=1,superres-strength={superres_strength}"])
        
        # 添加帧率转换参数
        if enable_double_frame:
            cmd.extend(["--vpp-fruc", "double"])
        
        # 添加输入和输出文件
        if avs_file_path:
            cmd.extend(["--avs", avs_file_path])
        else:
            cmd.extend(["-i", video_path])
        cmd.extend(["--output", output_path])
        
        try:
            # 在后台执行命令
            print(f"Executing command: {' '.join(cmd)}")
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            # 等待进程完成
            stdout, stderr = process.communicate()
            
            if process.returncode != 0:
                raise RuntimeError(f"NVEncC failed with return code {process.returncode}. Error: {stderr.decode('utf-8')}")
            
            print(f"Video processing completed successfully. Output saved to: {output_path}")
            
            # 返回输出路径给前端用于预览
            return {"ui": {"output_path": ((output_path),)}, "result": ((output_path),)}

        except Exception as e:
            raise RuntimeError(f"Error processing video: {str(e)}")
        
        finally:
            # 清理临时avs文件
            if avs_file_path and os.path.exists(avs_file_path):
                try:
                    os.remove(avs_file_path)
                    print(f"Cleaned up temporary AVS file: {avs_file_path}")
                except Exception as e:
                    print(f"Warning: Failed to remove temporary AVS file: {e}")

WEB_DIRECTORY = "./js"

# 节点注册
NODE_CLASS_MAPPINGS = {
    "NVVFR": NVVFRNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "NVVFR": "NVVFR Video Processor"
}

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
