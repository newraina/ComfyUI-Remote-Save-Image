# ComfyUI 远程保存图像

一个用于 ComfyUI 的自定义节点，允许将生成的图像上传到任何 HTTP 端点。

## 概述

这个自定义节点为在 ComfyUI 工作流中生成的图像提供了一个灵活的保存解决方案，可以将图像保存到任何通过 HTTP POST 请求接受文件上传的网络服务器或 API。与绑定到特定云服务提供商（AWS S3、GCS、Azure Blob）的节点不同，此节点可与任何通过 HTTP 接收文件的服务一起使用。

该节点作为输出节点运行，类似于标准的 SaveImage 节点，允许它作为工作流的最终节点使用，同时在 ComfyUI 界面中显示上传结果。

## 特性

- 将图像上传到任何接受 `multipart/form-data` POST 请求的 URL 端点
- 自定义请求中图像文件的字段名
- 添加自定义 HTTP 头（例如，用于身份验证）
- 在请求中包含额外的表单数据
- 在上传前将图像转换为不同格式（PNG、JPEG、WEBP）
- 控制 JPEG 和 WEBP 格式的图像质量

## 安装

1. 将此仓库克隆到您的 ComfyUI 的 `custom_nodes` 目录中：
   ```
   cd /path/to/ComfyUI/custom_nodes
   git clone https://github.com/yourusername/ComfyUI-Remote-Save-Image.git
   ```

2. 安装所需的依赖项：
   ```
   cd ComfyUI-Remote-Save-Image
   pip install -r requirements.txt
   ```

3. 重启 ComfyUI

## 使用方法

安装后，您将在 ComfyUI 节点菜单的 "image/upload" 类别中找到 "Remote Save Image" 节点。

### 节点参数

- **images**：连接到图像生成节点的输出
- **upload_url**：图像将被上传的完整 URL（例如，"https://your-api.com/upload"）
- **image_field_name**：图像文件的表单字段名（默认："file"）
- **filename_prefix**：生成的文件名前缀（默认："ComfyUI"）
- **image_format**：保存图像的格式（PNG、JPEG、WEBP）
- **headers_json**：包含要在请求中包含的头部的 JSON 字符串（例如，用于身份验证）
- **extra_data_json**：包含要在请求中包含的额外表单数据的 JSON 字符串
- **quality**：JPEG 和 WEBP 格式的质量设置（1-100）

### 示例工作流

1. 在 ComfyUI 中创建标准图像生成工作流
2. 添加 "Remote Save Image" 节点
3. 将图像生成节点的输出连接到 "images" 输入
4. 配置上传 URL 和其他参数
5. 运行工作流

节点将图像上传到指定的 URL 并在 ComfyUI 界面中显示服务器响应。当您想将图像上传到远程服务器而不是本地保存时，它可以直接替代标准的 SaveImage 节点使用。

## 安全考虑

- **API 密钥和令牌**：在 `headers_json` 字段中小心处理敏感信息。考虑使用环境变量或安全方法来管理凭据。
- **数据隐私**：注意您在 `extra_data_json` 字段中发送的数据，特别是个人或敏感信息。

## 许可证

[MIT 许可证](LICENSE)
