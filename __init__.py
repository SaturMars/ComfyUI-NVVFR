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
                "video_path": ("STRING", {"default": ""}),
                "output_prefix": ("STRING", {"default": "ComfyUI"}),
                "codec": (["h264", "h265"], {"default": "h265"}),
                "quality": (["high", "medium", "low"], {"default": "high"}),
                "enable_superres": ("BOOLEAN", {"default": True}),
                "superres_strength": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 1.0, "step": 0.1}),
                "enable_double_frame": ("BOOLEAN", {"default": False}),
                "width": ("INT", {"default": 1920, "min": 64, "max": 8192}),
                "height": ("INT", {"default": 1080, "min": 64, "max": 8192}),
                "depth": (["8bit", "10bit"], {"default": "10bit"}),                
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("output_path",)
    FUNCTION = "process_video"
    CATEGORY = "video/processing"

    OUTPUT_NODE = True
    
    def process_video(self, video_path, output_prefix, codec, quality, enable_superres, enable_double_frame, 
                     width=1920, height=1080, depth="10bit", superres_strength=1.0):
        """
        处理视频文件
        """
        # 检查NVEncC64.exe是否存在
        if not os.path.exists(self.nvenc_path):
            raise FileNotFoundError(f"NVEncC64.exe not found at {self.nvenc_path}")
        
        # 检查输入视频文件是否存在
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Input video file not found: {video_path}")
        
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

WEB_DIRECTORY = "./js"

# 节点注册
NODE_CLASS_MAPPINGS = {
    "NVVFR": NVVFRNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "NVVFR": "NVVFR Video Processor"
}

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
