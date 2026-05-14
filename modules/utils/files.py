from fastapi import UploadFile
from base64 import b64decode
from datetime import datetime
import cloudinary
import cloudinary.uploader
import cloudinary.api
import requests
from settings.config import load_env_config

config = load_env_config()

cloudinary.config(
    cloud_name=config['cloudinary_cloud_name'],
    api_key=config['cloudinary_api_key'],
    api_secret=config['cloudinary_api_secret'],
    secure = True
)

def upload_request_file_to_cloudinary(file: UploadFile):
    try:
        if file is None:
            return {
                'status': False,
                'message': 'File cannot be empty ' + str(file),
                'data': None,
            }
        upload_result = cloudinary.uploader.upload(
            file.file,
            folder="upteek",
            quality="auto:best",        # Automatically optimize quality, prioritize lossless compression
            # fetch_format="auto",        # Automatically choose the best format for the file
            # flags="lossless"            # Ensure lossless compression
        )
        uploaded_url = upload_result['secure_url']
        public_id = upload_result['public_id']
        return {
            'status': True,
            'message': 'Success',
            'data': {
                'uploaded_url': uploaded_url,
                'public_id': public_id,
            }
        }
    except Exception as e:
        return {
            'status': False,
            'message':  f"Error uploading file to Cloudinary: {str(e)}",
            'data': None
        }


def upload_base64_to_cloudinary(base64_string: str=None):
    try:
        if "base64," in base64_string:
            base64_string = base64_string.split("base64,")[1]
        image_bytes = b64decode(base64_string)
        upload_result = cloudinary.uploader.upload(
            image_bytes,
            resource_type="image",
            folder="upteek",
        )
        uploaded_url = upload_result['secure_url']
        public_id = upload_result['public_id']
        return {
            'status': True,
            'message': 'Success',
            'data': {
                'uploaded_url': uploaded_url,
                'public_id': public_id,
            }
        }
    except Exception as e:
        return {
            'status': False,
            'message':  f"Error uploading file to Cloudinary: {str(e)}",
            'data': None
        }