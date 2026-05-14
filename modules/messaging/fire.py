from typing import Dict, List
from modules.external.firebase import send_push, send_push_multi

def fb_welcome(token: str=None, data: Dict={}):
    data['name'] = "new_user"
    title = "Welcome!!!"
    body = "Welcome, we're thrilled to have you on board!"
    return send_push(token=token, title=title, body=body, data=data)
