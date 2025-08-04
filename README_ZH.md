# ComfyUI-NVVFR

ComfyUI节点，使用NVEncC进行视频超分补帧处理。

## 功能特性

- 使用NVEncC进行视频超分和补帧处理
- 支持H.264/H.265编码
- 支持超分辨率处理
- 支持帧率转换（双倍帧率）

## 安装方法

1. 将此节点文件夹复制到ComfyUI的`custom_nodes`目录中，或使用 git clone 命令。
2. 下载NVEnc二进制依赖包：
   - 前往 [NVEnc Releases页面](https://github.com/rigaya/NVEnc/releases)
   - 下载x64版本
   - 将压缩包内容解压到节点目录的`nvenc`文件夹中
   - 形如 `ComfyUI\custom_nodes\ComfyUI-NVVFR\nvenc`
3. 重启ComfyUI
4. 在节点列表中找到"NVVFR Video Processor"节点

## 使用方法

1. 添加"NVVFR Video Processor"节点到工作流
2. 设置输入视频路径
3. 配置输出参数：
   - 输出前缀：输出文件名前缀
   - 编码器：H.264或H.265
   - 质量：高、中、低
   - 超分辨率：启用/禁用，可调节强度
   - 双倍帧率：启用/禁用帧率转换
   - 输出分辨率：设置宽度和高度
   - 色深：8bit或10bit
4. 运行节点，处理完成后会自动显示视频预览

## 参数说明

### 输入参数

- **video_path**：输入视频文件路径
- **output_prefix**：输出文件名前缀
- **codec**：视频编码器（H.264/H.265）
- **quality**：编码质量（high/medium/low）
- **enable_superres**：是否启用超分辨率
- **superres_strength**：超分辨率强度（0.0-1.0）
- **enable_double_frame**：是否启用双倍补帧
- **width**：输出视频宽度
- **height**：输出视频高度
- **depth**：色深（8bit/10bit）

### 输出参数

- **video_path**：输出视频文件路径
- **视频预览**：HTML视频预览界面

## 注意事项

1. 确保系统已安装NVEncC并包含在nvenc文件夹中
2. H.264编码器不支持10bit色深，会自动降级到8bit
3. 视频预览功能需要现代浏览器支持HTML5 video
4. 输出文件保存在ComfyUI的output目录中

## 故障排除

### 视频预览不显示

1. 检查浏览器控制台是否有JavaScript错误
2. 确认视频文件已成功生成
3. 刷新ComfyUI页面重试
4. 确保浏览器支持HTML5 video

### 视频无法播放

1. 检查视频文件格式是否支持
2. 确认视频文件路径正确
3. 检查浏览器是否支持该视频编码格式

### 编码失败

1. 确认NVEncC64.exe文件存在于nvenc文件夹中
2. 检查输入视频文件是否存在且可读
3. 查看控制台输出的错误信息

## 更新日志

### v1.0.0
- 初始版本发布
- 基本视频处理功能
- 支持超分辨率和双倍补帧

## 致谢

本项目基于 [NVEnc](https://github.com/rigaya/NVEnc) 项目开发，感谢 rigaya 提供的强大视频编码和处理工具。

## 许可证

本项目遵循MIT许可证。
