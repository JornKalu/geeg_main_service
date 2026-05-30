from typing import Dict
import requests
import phonenumbers
from sqlalchemy.sql.functions import count
import certifi
from io import BytesIO
from fastapi import UploadFile
from settings.config import load_env_config
import cloudinary
from cloudinary.uploader import upload
from email_validator import validate_email, EmailNotValidError

config = load_env_config()

cloudinary.config(
    cloud_name=config['cloudinary_cloud_name'],
    api_key=config['cloudinary_api_key'],
    api_secret=config['cloudinary_api_secret'],
    secure = True
)

def get_ip_info(ip_address: str=None):
    url = "http://www.geoplugin.net/json.gp?ip=" + str(ip_address)
    req = requests.get(url=url)
    return req.json()

def process_phone_number(phone_number: str=None, country_code: str=None) -> Dict:
    try:
        x = phonenumbers.parse(phone_number, country_code)
        x = phonenumbers.format_number(x, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
        x = str(x).replace(" ", "")
        return {
            'status': True,
            'phone_number': x,
            'message': 'success'
        }
    except (phonenumbers.phonenumberutil.NumberParseException, Exception) as e:
        return {
            'status': False,
            'phone_number': None,
            'message': str(e)
        }


def check_phone_number_validity(phone_number: str=None, country_code: str=None):
    try:
        x = phonenumbers.parse(phone_number, country_code)
        return phonenumbers.is_possible_number(x)
    except (phonenumbers.phonenumberutil.NumberParseException, Exception) as e:
        return False

def cloudinary_upload_file(image: UploadFile):
    try:
        upload_result = upload(image.file)
        file_url = upload_result['secure_url']
        return {
            'status': True,
            'message': 'Success',
            'data': file_url,
        }
    except Exception as e:
        return {
            'status': False,
            'message': str(e),
            'data': None
        }
    
def cloudinary_upload_base64(base64_str: str=None):
    try:
        if base64_str is None or base64_str == '':
            raise Exception("Base64 string cannot be empty")
        else:
            upload_result = upload(base64_str)
            file_url = upload_result['secure_url']
            return {
                'status': True,
                'message': 'Success',
                'data': file_url,
            }
    except Exception as e:
        return {
            'status': False,
            'message': str(e),
            'data': None
        }

def send_to_geocode(data: str = None):
    global config
    url = config['geocode_url']
    data['api_key'] = config['geocode_key']
    # send get request and pass data as query parameters
    response = requests.get(url=url, params=data)
    return response.json()

def get_geocode_info(val: str=None):
    data = {
        'q': val
    }
    return send_to_geocode(data)

def get_list_of_nigerian_states_and_cities():
    url = "https://adminapi.fastfastapp.com/assets/state_cities_and_lga.json"
    resp = []
    try:
        req = requests.get(url=url)
        resp = req.json()
    except Exception as e:
        resp = []
    return resp

def validate_email_advanced(email: str=None):
    try:
        # Validate email and get normalized form
        emailinfo = validate_email(email, check_deliverability=False)
        return {
            'status': True,
            'message': f"Valid email: {emailinfo.normalized}",
        }
    except EmailNotValidError as e:
        return {
            'status': False,
            'message': f"Invalid email: {str(e)}",
        }