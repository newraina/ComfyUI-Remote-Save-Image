"""
ComfyUI-Remote-Save-Image
A custom node for ComfyUI that allows uploading generated images to any HTTP endpoint.
"""

from .remote_image_saver import RemoteImageSaver

NODE_CLASS_MAPPINGS = {
    "RemoteImageSaver": RemoteImageSaver
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "RemoteImageSaver": "Remote Save Image"
}
