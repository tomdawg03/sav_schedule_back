from twilio.rest import Client
from flask import current_app
from datetime import datetime, timedelta

class SMSService:
    def __init__(self):
        self.client = Client(
            current_app.config['TWILIO_ACCOUNT_SID'],
            current_app.config['TWILIO_AUTH_TOKEN']
        )

    def schedule_project_notification(self, phone_number, customer_name, project_date, address):
        try:
            # Format phone number if needed
            if not phone_number.startswith('+'):
                phone_number = '+1' + phone_number  # Add US country code if missing

            # Schedule message for day before project
            notification_date = datetime.strptime(project_date, '%Y-%m-%d') - timedelta(days=1)
            
            message = (
                f"Hello {customer_name}, this is Savage Scheduler reminding you "
                f"of your project tomorrow at {address}. "
                f"Please ensure the area is accessible. "
                f"If you have any questions, please contact us."
            )

            print(f"Attempting to send SMS to {phone_number}")  # Debug log
            print(f"Message content: {message}")  # Debug log
            print(f"Scheduled for: {notification_date}")  # Debug log

            # Send message immediately for testing
            message = self.client.messages.create(
                to=phone_number,
                from_=current_app.config['TWILIO_PHONE_NUMBER'],
                body=message
            )
            
            print(f"Message SID: {message.sid}")  # Debug log
            return True

        except Exception as e:
            print(f"Error sending SMS: {str(e)}")  # Debug log
            raise e 