# ComfyUI Remote Save Image

A custom node for ComfyUI that allows uploading generated images to any HTTP endpoint.

## Overview

This custom node provides a flexible solution for saving images generated in ComfyUI workflows to any web server or API that accepts file uploads via HTTP POST requests. Unlike nodes that are tied to specific cloud providers (AWS S3, GCS, Azure Blob), this node works with any service that can receive files via HTTP.

The node functions as an output node, similar to the standard SaveImage node, allowing it to be used as the final node in your workflow while displaying upload results in the ComfyUI interface.

## Features

- Upload images to any URL endpoint that accepts `multipart/form-data` POST requests
- Customize the field name used for the image file in the request
- Add custom HTTP headers (e.g., for authentication)
- Include additional form data with the request
- Convert images to different formats (PNG, JPEG, WEBP) before uploading
- Control image quality for JPEG and WEBP formats

## Installation

1. Clone this repository into your ComfyUI's `custom_nodes` directory:
   ```
   cd /path/to/ComfyUI/custom_nodes
   git clone https://github.com/yourusername/ComfyUI-Remote-Save-Image.git
   ```

2. Install the required dependencies:
   ```
   cd ComfyUI-Remote-Save-Image
   pip install -r requirements.txt
   ```

3. Restart ComfyUI

## Usage

After installation, you'll find the "Remote Save Image" node in the "image/upload" category in the ComfyUI node menu.

### Node Parameters

- **images**: Connect this to the output of an image-generating node
- **upload_url**: The full URL where the image will be uploaded (e.g., "https://your-api.com/upload")
- **image_field_name**: The form field name for the image file (default: "file")
- **filename_prefix**: Prefix for the generated filename (default: "ComfyUI")
- **image_format**: Format to save the image as (PNG, JPEG, WEBP)
- **headers_json**: JSON string containing headers to include in the request (e.g., for authentication)
- **extra_data_json**: JSON string containing additional form data to include in the request
- **quality**: Quality setting for JPEG and WEBP formats (1-100)

### Example Workflow

1. Create a standard image generation workflow in ComfyUI
2. Add the "Remote Save Image" node
3. Connect the output of your image-generating node to the "images" input
4. Configure the upload URL and other parameters
5. Run the workflow

The node will upload the images to the specified URL and display the server responses in the ComfyUI interface. It can be used as a direct replacement for the standard SaveImage node when you want to upload images to a remote server instead of saving them locally.

## API Response Format

To properly display uploaded images in the ComfyUI interface (similar to the standard SaveImage node), your API endpoint should return a JSON response that includes a URL to the uploaded image. The node will attempt to extract the URL from the response in the following ways:

1. Direct URL field: The response should include a `url` field at the root level:
   ```json
   {
     "url": "https://your-server.com/path/to/uploaded/image.png",
     "other_fields": "..."
   }
   ```

2. Nested URL field: Alternatively, the URL can be nested in a `data` object:
   ```json
   {
     "data": {
       "url": "https://your-server.com/path/to/uploaded/image.png",
       "other_fields": "..."
     },
     "status": "success"
   }
   ```

If the node can extract a valid URL from the response, it will be included in the return value and can be used by other nodes in your workflow. If no URL is found, the node will still display the full response text in the ComfyUI interface.

## Return Value Structure

The Remote Save Image node now returns a value structure compatible with the standard SaveImage node:

```json
{
  "ui": {
    "images": [
      {
        "filename": "remote_image_1",
        "subfolder": "",
        "type": "remote",
        "url": "https://your-server.com/path/to/uploaded/image.png",
        "status": "success",
        "message": "Image 1 uploaded successfully: {...}"
      }
    ]
  }
}
```

This structure allows the node to be used as a drop-in replacement for the SaveImage node in workflows that expect that format.

## Security Considerations

- **API Keys and Tokens**: Be careful with sensitive information in the `headers_json` field. Consider using environment variables or a secure method to manage your credentials.
- **Data Privacy**: Be mindful of what data you're sending in the `extra_data_json` field, especially if it contains personal or sensitive information.

## License

[MIT License](LICENSE)