#!/usr/bin/env python3
import os
import os.path as osp
import smtplib
from email.message import EmailMessage

SERVER = os.environ.get('EMAIL_SERVER', 'localhost')
PORT = os.environ.get('EMAIL_PORT', 25)
USERNAME = os.environ.get('EMAIL')
PASSWORD_FILE = os.environ.get('EMAIL_PASSWORD_FILE')

def send_email(to_addr, subject, content, from_addr=None, user=USERNAME,
               password=None, password_file=PASSWORD_FILE, server=SERVER,
               port=PORT):
    from_addr = from_addr or user
    if not from_addr:
        raise ValueError('either from_addr or user must be supplied')
    if user and not password:
        password = password_file and open(password_file).read().strip()
    if isinstance(to_addr, (list, tuple)):
        to_addr = ', '.join(to_addr)

    if isinstance(content, EmailMessage):
        msg = content
    else:
        msg = EmailMessage()
        msg.set_content(content)

    msg['To'] = to_addr
    msg['From'] = from_addr
    msg['Subject'] = subject

    with smtplib.SMTP(server, port) as s:
        if user and password:
            s.starttls()
            s.login(user, password)
        s.send_message(msg)

if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('to_addr')
    p.add_argument('subject')
    p.add_argument('content')
    p.add_argument('-f', '--from-addr')
    p.add_argument('-u', '--user', default=USERNAME)
    p.add_argument('-p', '--password')
    p.add_argument('-s', '--server', default=SERVER)
    p.add_argument('-P', '--port', default=PORT)
    args = p.parse_args()
    send_email(**vars(args))
