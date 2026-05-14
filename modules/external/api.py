from typing import Dict
import requests

def send_external_request(url, headers: Dict={}, data: Dict={}, type: int=1, https: bool=False):
    try:
        if type == 1:
            if not data:
                response = requests.get(url, headers=headers, verify=not https)
            else:
                response = requests.get(url, headers=headers, params=data, verify=not https)
        elif type == 2:
            response = requests.post(url, headers=headers, json=data, allow_redirects=True, verify=not https)
        elif type == 3:
            response = requests.get(url, headers=headers, verify=not https)
        elif type == 4:
            response = requests.put(url, headers=headers, json=data, allow_redirects=True, verify=not https)
        elif type == 5:
            response = requests.delete(url, headers=headers, json=data, allow_redirects=True, verify=not https)
        elif type == 6:
            response = requests.patch(url, headers=headers, json=data, allow_redirects=True, verify=not https)
        else:
            return {
                'status': False,
                'message': 'Invalid type',
                'data': None,
                'status_code': 0,
            }
        return {
            'status': True,
            'message': 'Success',
            'data': response.json(),
            'status_code': response.status_code,
        }
    except requests.exceptions.RequestException as e:
        return {
            'status': False,
            'message': str(e),
            'data': None,
        }
