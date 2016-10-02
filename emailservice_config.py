import os

SENDGRID_API_KEY = os.environ['SENDGRID_API_KEY'] if 'SENDGRID_API_KEY' in os.environ else None
MANDRILL_API_KEY = os.environ['MANDRILL_API_KEY'] if 'MANDRILL_API_KEY' in os.environ else None

MAILSERVICE_SENDER_EMAIL = 'no-reply@martindam.dk'
MAILSERVICE_SENDER_NAME = 'MD Mail Service'
