class Config:
    SECRET_KEY = 'your-secret-key-here'  # Change this in production!
    SQLALCHEMY_DATABASE_URI = 'sqlite:///users.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TWILIO_ACCOUNT_SID = 'MG3428ae50f09a945d50ef730154165533'
    TWILIO_AUTH_TOKEN = '9c0e4a7a407ea1bc989c4a88168a495b'
    TWILIO_PHONE_NUMBER = '+18338631177'