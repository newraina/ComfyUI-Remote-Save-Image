import json
import io
import time
import requests
from PIL import Image
import torch
import numpy as np
import os
import logging
import sys
import traceback
import folder_paths
from comfy.cli_args import args

# Configure logging system
logger = logging.getLogger('RemoteImageSaver')
logger.setLevel(logging.DEBUG)

# Create console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Create file handler
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
os.makedirs(log_dir, exist_ok=True)
file_handler = logging.FileHandler(os.path.join(log_dir, 'remote_image_saver.log'))
file_handler.setLevel(logging.DEBUG)

# Create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

# Add handlers to logger
logger.addHandler(console_handler)
logger.addHandler(file_handler)


class RemoteImageSaver:
    """
    A custom node for ComfyUI that allows uploading generated images to any HTTP endpoint.

    This node provides a flexible solution for saving images generated in ComfyUI workflows
    to any web server or API that accepts file uploads via HTTP POST requests.
    """

    def __init__(self):
        self.output_dir = folder_paths.get_output_directory()
        self.type = "output"
        self.prefix_append = ""
        self.compress_level = 4
        logger.info("RemoteImageSaver initialized, output directory: %s", self.output_dir)

    @classmethod
    def INPUT_TYPES(cls):
        """
        Define the input parameters for the node.
        """
        return {
            "required": {
                "images": ("IMAGE",),
                "upload_url": ("STRING", {
                    "default": "https://your-api-endpoint.com/upload",
                    "multiline": False,
                }),
                "image_field_name": ("STRING", {
                    "default": "file",
                    "multiline": False,
                }),
                "filename_prefix": ("STRING", {
                    "default": "ComfyUI",
                    "multiline": False,
                }),
                "image_format": (["PNG", "JPEG", "WEBP"], {
                    "default": "PNG"
                }),
            },
            "optional": {
                "headers_json": ("STRING", {
                    "default": '{"Authorization": "Bearer YOUR_API_KEY"}',
                    "multiline": True,
                }),
                "extra_data_json": ("STRING", {
                    "default": '{"source": "ComfyUI"}',
                    "multiline": True,
                }),
                "quality": ("INT", {
                    "default": 95,
                    "min": 1,
                    "max": 100,
                    "step": 1,
                    "display": "slider",
                    "note": "Only applicable for JPEG and WEBP formats. Not used for PNG format."
                }),
            },
            "hidden": {
                "prompt": "PROMPT",
                "extra_pnginfo": "EXTRA_PNGINFO"
            }
        }

    RETURN_TYPES = ()
    FUNCTION = "upload_via_http"
    OUTPUT_NODE = True
    CATEGORY = "image/upload"

    def upload_via_http(self, images, upload_url, image_field_name, filename_prefix, image_format,
                        headers_json=None, extra_data_json=None, quality=95, prompt=None, extra_pnginfo=None):
        """
        Upload images to a remote server via HTTP POST request.

        Args:
            images: Tensor containing the images to upload
            upload_url: The URL to upload the images to
            image_field_name: The field name for the image in the multipart/form-data request
            filename_prefix: Prefix for the generated filename
            image_format: Format to save the image as (PNG, JPEG, WEBP)
            headers_json: JSON string containing headers to include in the request
            extra_data_json: JSON string containing additional form data to include in the request
            quality: Quality setting for JPEG and WEBP formats (1-100)
            prompt: The prompt used to generate the image (hidden parameter)
            extra_pnginfo: Additional metadata for the image (hidden parameter)

        Returns:
            A dictionary containing UI information for display in ComfyUI
        """
        logger.info("Starting image upload process, total images: %d, upload URL: %s", len(images), upload_url)
        # Only log quality parameter for non-PNG formats
        if image_format != "PNG":
            logger.debug("Upload parameters - field name: %s, file prefix: %s, image format: %s, quality: %d",
                       image_field_name, filename_prefix, image_format, quality)
        else:
            logger.debug("Upload parameters - field name: %s, file prefix: %s, image format: %s",
                       image_field_name, filename_prefix, image_format)
        results = []

        # Parse JSON inputs
        try:
            headers = json.loads(headers_json) if headers_json else {}
            logger.debug("Parsed headers: %s", headers)
        except json.JSONDecodeError as e:
            error_msg = f"Failed to parse headers JSON: {str(e)}"
            logger.error(error_msg)
            return (error_msg,)

        try:
            extra_data = json.loads(extra_data_json) if extra_data_json else {}
            logger.debug("Parsed extra data: %s", extra_data)
        except json.JSONDecodeError as e:
            error_msg = f"Failed to parse extra data JSON: {str(e)}"
            logger.error(error_msg)
            return (error_msg,)

        # Process each image in the batch
        for i, image_tensor in enumerate(images):
            try:
                logger.info("Processing image %d", i + 1)
                # Convert from PyTorch tensor to PIL Image
                logger.debug("Image tensor shape: %s, type: %s", image_tensor.shape, image_tensor.dtype)
                image = tensor_to_pil(image_tensor)
                logger.debug("Converted to PIL image: size=%s, mode=%s", image.size, image.mode)

                # Create a BytesIO object to hold the image data
                image_bytes = io.BytesIO()

                # Save the image to the BytesIO object in the specified format
                mime_type = f"image/{image_format.lower()}"
                logger.debug("Saving image as %s format, MIME type: %s", image_format, mime_type)
                if image_format == "PNG":
                    image.save(image_bytes, format="PNG")
                    logger.debug("Image saved in PNG format")
                elif image_format == "JPEG":
                    # For JPEG format, use quality parameter
                    image.save(image_bytes, format="JPEG", quality=quality)
                    logger.debug("Image saved in JPEG format, quality: %d", quality)
                elif image_format == "WEBP":
                    # For WEBP format, use quality parameter
                    image.save(image_bytes, format="WEBP", quality=quality)
                    logger.debug("Image saved in WEBP format, quality: %d", quality)

                # Reset the BytesIO object's position to the beginning
                image_bytes.seek(0)
                image_size = len(image_bytes.getvalue())
                logger.debug("Image data size: %d bytes", image_size)

                # Generate a unique filename
                timestamp = int(time.time())
                filename = f"{filename_prefix}_{timestamp}_{i}.{image_format.lower()}"
                logger.debug("Generated filename: %s", filename)

                # Prepare the files and data for the request
                files = {
                    image_field_name: (filename, image_bytes, mime_type)
                }
                logger.debug("Preparing to upload file, field name: %s", image_field_name)

                # Send the HTTP POST request
                logger.info("Starting HTTP request to %s", upload_url)
                try:
                    response = requests.post(
                        url=upload_url,
                        files=files,
                        data=extra_data,
                        headers=headers,
                        timeout=60
                    )
                    logger.debug("HTTP request sent, status code: %d", response.status_code)

                    # Check if the request was successful
                    response.raise_for_status()
                    logger.info("HTTP request successful, status code: %d", response.status_code)

                    # Try to parse the response as JSON, fall back to text if that fails
                    try:
                        response_data = response.json()
                        response_text = json.dumps(response_data)
                        logger.debug("Response parsed as JSON: %s", response_text)

                        # Try to extract URL from JSON response
                        image_url = None
                        if isinstance(response_data, dict) and 'url' in response_data:
                            image_url = response_data['url']
                        elif isinstance(response_data, dict) and 'data' in response_data and isinstance(response_data['data'], dict) and 'url' in response_data['data']:
                            image_url = response_data['data']['url']
                    except json.JSONDecodeError:
                        response_text = response.text
                        logger.debug("Response is not JSON format, using text: %s", response_text)
                        image_url = None

                    success_msg = f"Image {i + 1} uploaded successfully: {response_text}"
                    logger.info("Image %d uploaded successfully", i + 1)

                    # Store both the message and the URL (if available)
                    result_info = {
                        "message": success_msg,
                        "url": image_url,
                        "status": "success"
                    }
                    results.append(result_info)
                except requests.exceptions.Timeout:
                    error_msg = f"Error uploading image {i + 1}: Request timed out after 60 seconds"
                    logger.error("Image %d upload timed out", i + 1)
                    result_info = {
                        "message": error_msg,
                        "url": None,
                        "status": "error"
                    }
                    results.append(result_info)
                    continue

            except requests.RequestException as e:
                error_msg = f"Error uploading image {i + 1}: {str(e)}"
                logger.error("Image %d upload request exception: %s", i + 1, str(e))
                logger.debug("Request exception details: %s", traceback.format_exc())
                result_info = {
                    "message": error_msg,
                    "url": None,
                    "status": "error"
                }
                results.append(result_info)
            except Exception as e:
                error_msg = f"Unexpected error uploading image {i + 1}: {str(e)}"
                logger.error("Unexpected error during image %d upload: %s", i + 1, str(e))
                logger.debug("Exception details: %s", traceback.format_exc())
                result_info = {
                    "message": error_msg,
                    "url": None,
                    "status": "error"
                }
                results.append(result_info)

        # Process results for UI display
        logger.info("All images processed, total: %d images", len(images))

        # Format results in a way compatible with SaveImage node
        ui_results = []
        for i, result in enumerate(results):
            if isinstance(result, dict):
                # For structured results
                url = result.get("url")
                status = result.get("status")
                message = result.get("message", "")

                # Create a result entry similar to SaveImage
                ui_result = {
                    "filename": f"remote_image_{i+1}",  # Placeholder filename
                    "subfolder": "",                  # No subfolder for remote images
                    "type": "remote"                  # Mark as remote type
                }

                # Add URL if available
                if url:
                    ui_result["url"] = url

                # Add status and message for display
                ui_result["status"] = status
                ui_result["message"] = message
            else:
                # For string results (fallback)
                ui_result = {
                    "filename": f"remote_image_{i+1}",
                    "subfolder": "",
                    "type": "remote",
                    "status": "unknown",
                    "message": str(result)
                }

            ui_results.append(ui_result)

        # Return UI info in a format similar to SaveImage node
        logger.debug("Returning UI info with %d results", len(ui_results))
        return {"ui": {"images": ui_results}}


def tensor_to_pil(image_tensor):
    """
    Convert a PyTorch tensor to a PIL Image.

    Args:
        image_tensor: PyTorch tensor of shape [H, W, C] in range [0, 1]

    Returns:
        PIL Image
    """
    try:
        logger.debug("Converting tensor to PIL image, tensor shape: %s", image_tensor.shape)
        # Convert to numpy array and ensure values are in [0, 255] range
        image_np = (image_tensor.cpu().numpy() * 255).astype(np.uint8)
        logger.debug("Converted to numpy array, shape: %s, type: %s", image_np.shape, image_np.dtype)

        # Create PIL Image
        image = Image.fromarray(image_np)
        logger.debug("PIL image created successfully, size: %s, mode: %s", image.size, image.mode)
        return image
    except Exception as e:
        logger.error("Failed to convert tensor to PIL image: %s", str(e))
        logger.debug("Exception details: %s", traceback.format_exc())
        raise
