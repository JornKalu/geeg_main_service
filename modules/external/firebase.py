from typing import Dict, List
import firebase_admin
from firebase_admin import auth, credentials, messaging
import os
import traceback
import json

current_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.abspath(os.path.join(current_dir, "../../../"))
config_path = os.path.join(base_dir, "configs", "firebase.json")

# Initialize Firebase Admin SDK
cred = credentials.Certificate(config_path)
firebase_admin.initialize_app(cred)

def verify_token(token: str):
    try:
        decoded_token = auth.verify_id_token(token)
        data = {
            'id': decoded_token['uid'],
            'email': decoded_token.get('email', None),
            'name': decoded_token.get('name', None),
            'picture': decoded_token.get('picture', None),
        }
        return {
            'status': True,
            'message': 'Success',
            'data': data,
        }
    except Exception as e:
        return {
        'status': False,
        'message': f"{type(e).__name__}: {e}",
        'data': traceback.format_exc()
    }

def send_push(token: str, title: str, body: str, data: Dict={}):
    if token is None or token == '':
        return {
            'status': False,
            'message': 'Empty token',
            'data': None
        }
    else:
        try:
            data['icon'] = "ic_notification"
            data['click_action'] = "FLUTTER_NOTIFICATION_CLICK"
            message = messaging.Message(
                token=token,
                notification=messaging.Notification(
                    title=title,
                    body=body
                ),
                android=messaging.AndroidConfig(
                    notification=messaging.AndroidNotification(
                        icon="ic_notification",  # ✅ Must be in res/drawable folder in your Android app
                        # color="#f45342",         # optional: background color
                    )
                ),
                webpush=messaging.WebpushConfig(
                    notification=messaging.WebpushNotification(
                        icon="https://app.upteek.com/images/upteek_logo_full_main.png",
                        badge="https://app.upteek.com/images/icon.png"
                    )
                ),
                data=data
            )
            response = messaging.send(message)
            # return {"message_id": response}
            return {
                'status': True,
                'message': 'Success',
                'data': response,
            }
        except Exception as e:
            return {
                'status': False,
                'message': f"{type(e).__name__}: {e}",
                'data': traceback.format_exc()
            }

def send_push_multi(tokens: List[str], title: str, body: str, data: Dict={}):
    if len(tokens) == 0:
        return {
            'status': False,
            'message': 'Empty token',
            'data': None
        }
    else:
        try:
            data['icon'] = "ic_notification"
            data['click_action'] = "FLUTTER_NOTIFICATION_CLICK"
            # Construct the message to send to multiple devices
            message = messaging.MulticastMessage(
                tokens=tokens,  # List of up to 500 device FCM tokens
                notification=messaging.Notification(
                    title=title,
                    body=body
                ),
                android=messaging.AndroidConfig(
                    notification=messaging.AndroidNotification(
                        icon="ic_notification",  # ✅ Must be in res/drawable folder in your Android app
                        # color="#f45342",         # optional: background color
                    )
                ),
                webpush=messaging.WebpushConfig(
                    notification=messaging.WebpushNotification(
                        icon="https://app.upteek.com/images/upteek_logo_full_main.png",
                        badge="https://app.upteek.com/images/icon.png"
                    )
                ),
                data=data
            )
            response = messaging.send_multicast(message)
            resp_data =  {
                "success_count": response.success_count,
                "failure_count": response.failure_count,
                "responses": [r.__dict__ for r in response.responses]
            }
            return {
                'status': True,
                'message': 'Success',
                'data': resp_data,
            }
        except Exception as e:
            return {
                'status': False,
                'message': f"{type(e).__name__}: {e}",
                'data': traceback.format_exc()
            }
