import os
import requests

class EmailService:
    def __init__(self):
        try:
            self.api_key = os.environ.get('SENDGRID_API_KEY')
            print(f"Initializing SendGrid with API key: {self.api_key[:5]}...")  # Only print first 5 chars for security
            if not self.api_key:
                raise ValueError("SendGrid API key not found in environment")
            print("EmailService initialized successfully")
        except Exception as e:
            print(f"Error initializing EmailService: {str(e)}")
            print(f"Error type: {type(e).__name__}")
            print(f"Full error details: {str(e)}")
            raise

    def send_project_confirmation(self, customer_email, customer_name, project_date, address, customer_phone=None, po=None, city=None, subdivision=None, lot_number=None, square_footage=None, job_cost_type=None, work_type=None, notes=None, region=None):
        if not customer_email:
            print("No email provided, skipping email notification")
            return False

        try:
            print(f"Preparing to send confirmation email to {customer_email}")
            
            # Format work types and job cost types
            def format_type(type_str):
                # Replace underscores with spaces and capitalize each word
                return type_str.replace('_', ' ').title()
            
            # Format lists for display
            job_cost_types_display = ", ".join(format_type(t) for t in job_cost_type) if isinstance(job_cost_type, list) else "Not specified"
            work_types_display = ", ".join(format_type(t) for t in work_type) if isinstance(work_type, list) else "Not specified"
            
            data = {
                "personalizations": [
                    {
                        "to": [{"email": customer_email}]
                    }
                ],
                "from": {"email": "savageut@savageut.com"},
                "subject": "Project Confirmation - Savage Conveying",
                "content": [{
                    "type": "text/html",
                    "value": f"""
                    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                        <div style="text-align: center; margin-bottom: 30px;">
                            <h1 style="color: #333; margin-bottom: 10px;">Project Confirmation</h1>
                            <p style="color: #666; font-size: 16px;">Thank you for choosing Savage Conveying</p>
                        </div>

                        <div style="background-color: #f7f7f7; padding: 20px; border-radius: 5px; margin-bottom: 20px;">
                            <h2 style="color: #333; margin-bottom: 15px;">Project Details</h2>
                            <table style="width: 100%; border-collapse: collapse;">
                                <tr>
                                    <td style="padding: 8px 0; color: #666;"><strong>Customer Name:</strong></td>
                                    <td style="padding: 8px 0; color: #333;">{customer_name}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 8px 0; color: #666;"><strong>Project Date:</strong></td>
                                    <td style="padding: 8px 0; color: #333;">{project_date}</td>
                                </tr>
                                {f'''<tr>
                                    <td style="padding: 8px 0; color: #666;"><strong>PO Number:</strong></td>
                                    <td style="padding: 8px 0; color: #333;">{po}</td>
                                </tr>''' if po else ''}
                                {f'''<tr>
                                    <td style="padding: 8px 0; color: #666;"><strong>Phone:</strong></td>
                                    <td style="padding: 8px 0; color: #333;">{customer_phone}</td>
                                </tr>''' if customer_phone else ''}
                                <tr>
                                    <td style="padding: 8px 0; color: #666;"><strong>Address:</strong></td>
                                    <td style="padding: 8px 0; color: #333;">{address}</td>
                                </tr>
                                {f'''<tr>
                                    <td style="padding: 8px 0; color: #666;"><strong>City:</strong></td>
                                    <td style="padding: 8px 0; color: #333;">{city}</td>
                                </tr>''' if city else ''}
                                {f'''<tr>
                                    <td style="padding: 8px 0; color: #666;"><strong>Subdivision:</strong></td>
                                    <td style="padding: 8px 0; color: #333;">{subdivision}</td>
                                </tr>''' if subdivision else ''}
                                {f'''<tr>
                                    <td style="padding: 8px 0; color: #666;"><strong>Lot Number:</strong></td>
                                    <td style="padding: 8px 0; color: #333;">{lot_number}</td>
                                </tr>''' if lot_number else ''}
                                {f'''<tr>
                                    <td style="padding: 8px 0; color: #666;"><strong>Square Footage:</strong></td>
                                    <td style="padding: 8px 0; color: #333;">{square_footage}</td>
                                </tr>''' if square_footage else ''}
                            </table>
                        </div>

                        <div style="background-color: #f7f7f7; padding: 20px; border-radius: 5px; margin-bottom: 20px;">
                            <h2 style="color: #333; margin-bottom: 15px;">Work Details</h2>
                            <table style="width: 100%; border-collapse: collapse;">
                                <tr>
                                    <td style="padding: 8px 0; color: #666;"><strong>Job Cost Type:</strong></td>
                                    <td style="padding: 8px 0; color: #333;">{job_cost_types_display}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 8px 0; color: #666;"><strong>Work Type:</strong></td>
                                    <td style="padding: 8px 0; color: #333;">{work_types_display}</td>
                                </tr>
                                {f'''<tr>
                                    <td style="padding: 8px 0; color: #666;"><strong>Additional Notes:</strong></td>
                                    <td style="padding: 8px 0; color: #333;">{notes}</td>
                                </tr>''' if notes else ''}
                            </table>
                        </div>

                        <div style="margin-top: 20px; padding: 20px; border: 1px solid #ddd; border-radius: 5px;">
                            <h3 style="color: #333; margin-bottom: 15px;">Important Information</h3>
                            <ul style="color: #666; padding-left: 20px; margin-bottom: 20px;">
                                <li>Please ensure all necessary inspections are completed before the scheduled date</li>
                                <li>Please ensure the work area is accessible on the scheduled date</li>
                                <li>Remove any vehicles or obstacles from the work area</li>
                                <li>Our team will arrive on the scheduled date</li>
                            </ul>
                        </div>

                        <div style="margin-top: 30px; text-align: center; color: #666;">
                            <p>If you have any questions or need to make changes, please contact us:</p>
                            <p style="margin: 5px 0;">Phone: (801) 571-0533</p>
                            <p style="margin: 5px 0;">Email: savageut@savageut.com</p>
                        </div>

                        <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; text-align: center; color: #999; font-size: 12px;">
                            <p>This is an automated message from Savage Concrete</p>
                        </div>
                    </div>
                    """
                }]
            }
            
            print(f"Using SendGrid API key: {self.api_key[:5]}...")
            print("Sending email via SendGrid API...")
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            response = requests.post(
                "https://api.sendgrid.com/v3/mail/send",
                headers=headers,
                json=data
            )
            print(f"SendGrid API Response Status Code: {response.status_code}")
            if response.status_code != 202:  # SendGrid returns 202 for successful sends
                print(f"SendGrid API Error Response: {response.text}")
                return False
            print("Email sent successfully")
            return True
            
        except Exception as e:
            print(f"Error sending email: {str(e)}")
            print(f"Error type: {type(e).__name__}")
            if hasattr(e, 'response'):
                print(f"Response status code: {e.response.status_code}")
                print(f"Response text: {e.response.text}")
            return False

    def send_project_update(self, customer_email, customer_name, project_date, address, customer_phone=None, po=None, city=None, subdivision=None, lot_number=None, square_footage=None, job_cost_type=None, work_type=None, notes=None, region=None, update_type="modification"):
        if not customer_email:
            print("No email provided for update, skipping")
            return False

        try:
            print(f"Preparing to send update email to {customer_email}")
            
            # Format work types and job cost types
            def format_type(type_str):
                # Replace underscores with spaces and capitalize each word
                return type_str.replace('_', ' ').title()
            
            # Format lists for display
            job_cost_types_display = ", ".join(format_type(t) for t in job_cost_type) if isinstance(job_cost_type, list) else "Not specified"
            work_types_display = ", ".join(format_type(t) for t in work_type) if isinstance(work_type, list) else "Not specified"
            
            data = {
                "personalizations": [
                    {
                        "to": [{"email": customer_email}]
                    }
                ],
                "from": {"email": "savageut@savageut.com"},
                "subject": f"Project {update_type.title()} - Savage Conveying",
                "content": [{
                    "type": "text/html",
                    "value": f"""
                    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                        <div style="text-align: center; margin-bottom: 30px;">
                            <h1 style="color: #333; margin-bottom: 10px;">Project Update</h1>
                            <p style="color: #666; font-size: 16px;">Your project has been {update_type}</p>
                        </div>

                        <div style="background-color: #f7f7f7; padding: 20px; border-radius: 5px; margin-bottom: 20px;">
                            <h2 style="color: #333; margin-bottom: 15px;">Updated Project Details</h2>
                            <table style="width: 100%; border-collapse: collapse;">
                                <tr>
                                    <td style="padding: 8px 0; color: #666;"><strong>Customer Name:</strong></td>
                                    <td style="padding: 8px 0; color: #333;">{customer_name}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 8px 0; color: #666;"><strong>Project Date:</strong></td>
                                    <td style="padding: 8px 0; color: #333;">{project_date}</td>
                                </tr>
                                {f'''<tr>
                                    <td style="padding: 8px 0; color: #666;"><strong>PO Number:</strong></td>
                                    <td style="padding: 8px 0; color: #333;">{po}</td>
                                </tr>''' if po else ''}
                                {f'''<tr>
                                    <td style="padding: 8px 0; color: #666;"><strong>Phone:</strong></td>
                                    <td style="padding: 8px 0; color: #333;">{customer_phone}</td>
                                </tr>''' if customer_phone else ''}
                                <tr>
                                    <td style="padding: 8px 0; color: #666;"><strong>Address:</strong></td>
                                    <td style="padding: 8px 0; color: #333;">{address}</td>
                                </tr>
                                {f'''<tr>
                                    <td style="padding: 8px 0; color: #666;"><strong>City:</strong></td>
                                    <td style="padding: 8px 0; color: #333;">{city}</td>
                                </tr>''' if city else ''}
                                {f'''<tr>
                                    <td style="padding: 8px 0; color: #666;"><strong>Subdivision:</strong></td>
                                    <td style="padding: 8px 0; color: #333;">{subdivision}</td>
                                </tr>''' if subdivision else ''}
                                {f'''<tr>
                                    <td style="padding: 8px 0; color: #666;"><strong>Lot Number:</strong></td>
                                    <td style="padding: 8px 0; color: #333;">{lot_number}</td>
                                </tr>''' if lot_number else ''}
                                {f'''<tr>
                                    <td style="padding: 8px 0; color: #666;"><strong>Square Footage:</strong></td>
                                    <td style="padding: 8px 0; color: #333;">{square_footage}</td>
                                </tr>''' if square_footage else ''}
                            </table>
                        </div>

                        <div style="background-color: #f7f7f7; padding: 20px; border-radius: 5px; margin-bottom: 20px;">
                            <h2 style="color: #333; margin-bottom: 15px;">Work Details</h2>
                            <table style="width: 100%; border-collapse: collapse;">
                                <tr>
                                    <td style="padding: 8px 0; color: #666;"><strong>Job Cost Type:</strong></td>
                                    <td style="padding: 8px 0; color: #333;">{job_cost_types_display}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 8px 0; color: #666;"><strong>Work Type:</strong></td>
                                    <td style="padding: 8px 0; color: #333;">{work_types_display}</td>
                                </tr>
                                {f'''<tr>
                                    <td style="padding: 8px 0; color: #666;"><strong>Additional Notes:</strong></td>
                                    <td style="padding: 8px 0; color: #333;">{notes}</td>
                                </tr>''' if notes else ''}
                            </table>
                        </div>

                        <div style="margin-top: 20px; padding: 20px; border: 1px solid #ddd; border-radius: 5px;">
                            <h3 style="color: #333; margin-bottom: 15px;">Important Information</h3>
                            <ul style="color: #666; padding-left: 20px; margin-bottom: 20px;">
                                <li>Please ensure all necessary inspections are completed before the scheduled date</li>
                                <li>Please ensure the work area is accessible on the scheduled date</li>
                                <li>Remove any vehicles or obstacles from the work area</li>
                                <li>Our team will arrive on the scheduled date</li>
                            </ul>
                        </div>

                        <div style="margin-top: 30px; text-align: center; color: #666;">
                            <p>If you have any questions or concerns, please contact us:</p>
                            <p style="margin: 5px 0;">Phone: (801) 571-0533</p>
                            <p style="margin: 5px 0;">Email: savageut@savageut.com</p>
                        </div>

                        <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; text-align: center; color: #999; font-size: 12px;">
                            <p>This is an automated message from Savage Concrete</p>
                        </div>
                    </div>
                    """
                }]
            }
            
            print("Sending update email via SendGrid API...")
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            response = requests.post(
                "https://api.sendgrid.com/v3/mail/send",
                headers=headers,
                json=data
            )
            print(f"Update email sent successfully with status code {response.status_code}")
            return True
            
        except Exception as e:
            print(f"Error sending update email: {str(e)}")
            print(f"Full error details: {type(e).__name__}")
            return False 

    def send_project_reminder(self, customer_email, customer_name, project_date, address, customer_phone=None, po=None, city=None, subdivision=None, lot_number=None, square_footage=None, job_cost_type=None, work_type=None, notes=None, region=None):
        if not customer_email:
            print("No email provided, skipping reminder email")
            return False

        try:
            print(f"Preparing to send reminder email to {customer_email}")
            
            # Format lists for display
            job_cost_types_display = ", ".join(job_cost_type) if isinstance(job_cost_type, list) else str(job_cost_type) if job_cost_type else "Not specified"
            work_types_display = ", ".join(work_type) if isinstance(work_type, list) else str(work_type) if work_type else "Not specified"
            
            data = {
                "personalizations": [
                    {
                        "to": [{"email": customer_email}]
                    }
                ],
                "from": {"email": "savageut@savageut.com"},
                "subject": "Project Reminder - Savage Concrete",
                "content": [{
                    "type": "text/html",
                    "value": f"""
                    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                        <div style="text-align: center; margin-bottom: 30px;">
                            <h1 style="color: #333; margin-bottom: 10px;">Project Reminder</h1>
                            <p style="color: #666; font-size: 16px;">Your project with Savage Concrete is scheduled for tomorrow</p>
                        </div>

                        <div style="background-color: #f7f7f7; padding: 20px; border-radius: 5px; margin-bottom: 20px;">
                            <h2 style="color: #333; margin-bottom: 15px;">Project Details</h2>
                            <table style="width: 100%; border-collapse: collapse;">
                                <tr>
                                    <td style="padding: 8px 0; color: #666;"><strong>Customer Name:</strong></td>
                                    <td style="padding: 8px 0; color: #333;">{customer_name}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 8px 0; color: #666;"><strong>Project Date:</strong></td>
                                    <td style="padding: 8px 0; color: #333;">{project_date}</td>
                                </tr>
                                {f'''<tr>
                                    <td style="padding: 8px 0; color: #666;"><strong>PO Number:</strong></td>
                                    <td style="padding: 8px 0; color: #333;">{po}</td>
                                </tr>''' if po else ''}
                                {f'''<tr>
                                    <td style="padding: 8px 0; color: #666;"><strong>Phone:</strong></td>
                                    <td style="padding: 8px 0; color: #333;">{customer_phone}</td>
                                </tr>''' if customer_phone else ''}
                                <tr>
                                    <td style="padding: 8px 0; color: #666;"><strong>Address:</strong></td>
                                    <td style="padding: 8px 0; color: #333;">{address}</td>
                                </tr>
                                {f'''<tr>
                                    <td style="padding: 8px 0; color: #666;"><strong>City:</strong></td>
                                    <td style="padding: 8px 0; color: #333;">{city}</td>
                                </tr>''' if city else ''}
                                {f'''<tr>
                                    <td style="padding: 8px 0; color: #666;"><strong>Subdivision:</strong></td>
                                    <td style="padding: 8px 0; color: #333;">{subdivision}</td>
                                </tr>''' if subdivision else ''}
                                {f'''<tr>
                                    <td style="padding: 8px 0; color: #666;"><strong>Lot Number:</strong></td>
                                    <td style="padding: 8px 0; color: #333;">{lot_number}</td>
                                </tr>''' if lot_number else ''}
                                {f'''<tr>
                                    <td style="padding: 8px 0; color: #666;"><strong>Square Footage:</strong></td>
                                    <td style="padding: 8px 0; color: #333;">{square_footage}</td>
                                </tr>''' if square_footage else ''}
                            </table>
                        </div>

                        <div style="background-color: #f7f7f7; padding: 20px; border-radius: 5px; margin-bottom: 20px;">
                            <h2 style="color: #333; margin-bottom: 15px;">Work Details</h2>
                            <table style="width: 100%; border-collapse: collapse;">
                                <tr>
                                    <td style="padding: 8px 0; color: #666;"><strong>Job Cost Type:</strong></td>
                                    <td style="padding: 8px 0; color: #333;">{job_cost_types_display}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 8px 0; color: #666;"><strong>Work Type:</strong></td>
                                    <td style="padding: 8px 0; color: #333;">{work_types_display}</td>
                                </tr>
                                {f'''<tr>
                                    <td style="padding: 8px 0; color: #666;"><strong>Additional Notes:</strong></td>
                                    <td style="padding: 8px 0; color: #333;">{notes}</td>
                                </tr>''' if notes else ''}
                            </table>
                        </div>

                        <div style="margin-top: 20px; padding: 20px; border: 1px solid #ddd; border-radius: 5px;">
                            <h3 style="color: #333; margin-bottom: 15px;">Important Reminders</h3>
                            <ul style="color: #666; padding-left: 20px; margin-bottom: 20px;">
                                <li>Please ensure all necessary inspections are completed</li>
                                <li>Please ensure the work area is accessible</li>
                                <li>Remove any vehicles or obstacles from the work area</li>
                                <li>Our team will arrive tomorrow as scheduled</li>
                            </ul>
                        </div>

                        <div style="margin-top: 30px; text-align: center; color: #666;">
                            <p>If you need to make any changes or have questions, please contact us immediately:</p>
                            <p style="margin: 5px 0;">Phone: (801) 571-0533</p>
                            <p style="margin: 5px 0;">Email: savageut@savageut.com</p>
                        </div>

                        <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; text-align: center; color: #999; font-size: 12px;">
                            <p>This is an automated reminder from Savage Concrete</p>
                        </div>
                    </div>
                    """
                }]
            }
            
            print(f"Using SendGrid API key: {self.api_key[:5]}...")
            print("Sending reminder email via SendGrid API...")
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            response = requests.post(
                "https://api.sendgrid.com/v3/mail/send",
                headers=headers,
                json=data
            )
            print(f"SendGrid API Response Status Code: {response.status_code}")
            if response.status_code != 202:  # SendGrid returns 202 for successful sends
                print(f"SendGrid API Error Response: {response.text}")
                return False
            print("Reminder email sent successfully")
            return True
            
        except Exception as e:
            print(f"Error sending reminder email: {str(e)}")
            print(f"Error type: {type(e).__name__}")
            if hasattr(e, 'response'):
                print(f"Response status code: {e.response.status_code}")
                print(f"Response text: {e.response.text}")
            return False 