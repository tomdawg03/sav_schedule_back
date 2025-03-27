<<<<<<< HEAD
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-here')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///savage.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Twilio configuration
    TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
    TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
    TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER')
    
    # SendGrid configuration
    SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY')
=======
class Config:
    SECRET_KEY = 'your-secret-key-here'  # Change this in production!
    SQLALCHEMY_DATABASE_URI = 'sqlite:///savage.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TWILIO_ACCOUNT_SID = 'MG3428ae50f09a945d50ef730154165533'
    TWILIO_AUTH_TOKEN = '9c0e4a7a407ea1bc989c4a88168a495b'
    TWILIO_PHONE_NUMBER = '+18338631177'
>>>>>>> 9e888cc9d22dfe916ed96e30e883c8cbf60cef19
