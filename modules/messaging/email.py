from typing import List
import requests
import os
from settings.config import load_env_config

config = load_env_config()

def send_to_smtp2go(subject: str=None, recipients: str=None, text: str=None, html: str=None, attachments: List=[]):
    api_key = config['smtp2go_key']
    url = config['smtp2go_url'] + "email/send"
    headers = { "Content-Type": "application/json" }
    data = {
        "api_key": api_key,
        "sender": config['smtp2go_name'] + " <"+config['smtp2go_address']+">",
        "to": [recipients],
        "subject": subject,
        "text_body": text,
        "html_body": html,
        "attachments": attachments,
    }
    response = requests.post(url=url, headers=headers, json=data)
    return response.json()

def send_to_mailtrap(subject: str=None, recipient: str=None, recipient_name: str=None, text: str=None, html: str=None, attachments: List=[]):
    api_key = config['mailtrap_api_key']
    url = config['mailtrap_url'] + "send"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    data = {
        "from": {"email": config['mailtrap_from_email'], "name": config['mailtrap_from_name']},
        "to": [{"email": recipient, "name": recipient_name}],
        "subject": subject,
        "text": text,
        "html": html,
        "category": "Upteek Email",
    }
    if len(attachments) > 0:
        data['attachments'] = attachments
    try:
        response = requests.post(url, json=data, headers=headers)
        if response.status_code == 200:
            return {
                'status': True,
                'message': 'Success',
                'data': response.json(),
            }
        else:
            return {
                'status': False,
                'message': f"Failed to send email: {response.status_code} - {response.text}",
                'data': None,
            }
    except Exception as e:
        return {
            'status': False,
            'message': f"An error occurred: {e}",
            'data': None,
        }

def get_notification_string(title: str=None, sub_title: str=None, recipient_name: str=None, body: str=None, foot: str=None):
    if recipient_name is None:
        recipient_name = ""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.abspath(os.path.join(current_dir, "../../"))
    template_path = os.path.join(base_dir, "templates", "notifications.html")
    html = ""
    with open(template_path, "r", encoding="utf-8") as file:
        html = file.read()
    if html != "":
        html = html.replace("@title@", title)
        html = html.replace("@sub_title@", sub_title)
        html = html.replace("@recipient_name@", recipient_name)
        html = html.replace("@body@", body)
        html = html.replace("@foot@", foot)
    return html

def send_email(subject: str=None, recipients: str=None, recipient_name: str=None, title: str=None, sub_title: str=None, body: str=None, foot: str=None, attachments: List=[]):
    text = str(title) + "\n" + str(body) + "\n" + str(foot)
    html = get_notification_string(title=title, sub_title=sub_title, recipient_name=recipient_name, body=body, foot=foot)
    return send_to_smtp2go(subject=subject, recipients=recipients, text=text, html=html, attachments=attachments)
    # return send_to_mailtrap(subject=subject, recipient=recipients, text=text, html=html, attachments=attachments)

def e_send_token(username: str=None, email: str=None, token: str=None, minutes: int=0):
    title = "New Token"
    sub_title = "Temporary token"
    msg = "Use the code below to complete your action:<br><br>"+str(token)+"<br><br>The above token expires in " + str(minutes) + " minutes<br>If you didn't originate this please reach out to our support team at techsupport@geeg.com</p>"
    footnote = "💕 & ✨, Geeg."
    return send_email(subject=title, recipients=email, title=title, sub_title=sub_title, recipient_name=username, body=msg, foot=footnote)

def e_notification(email: str=None, title: str=None, sub_title: str=None, recipient_name: str=None, msg: str=None):
    msg = "<p>" + str(msg) + "</p>"
    footnote = "💕 & ✨, Geeg."
    return send_email(subject=title, recipients=email, title=title, sub_title=sub_title, recipient_name=recipient_name, body=msg, foot=footnote)
