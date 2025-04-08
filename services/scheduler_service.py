from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta
from models import db
from models.project import Project
from models.customer import Customer
from services.email_service import EmailService
import pytz

class SchedulerService:
    def __init__(self, app):
        self.app = app
        self.scheduler = BackgroundScheduler()
        self.email_service = EmailService()
        
        # Add job to check for upcoming projects and send reminders
        self.scheduler.add_job(
            func=self.check_upcoming_projects,
            trigger=CronTrigger(hour=9),  # Run at 9 AM daily
            id='check_upcoming_projects',
            name='Check for projects scheduled tomorrow and send reminders',
            replace_existing=True
        )
        
        # Start the scheduler
        self.scheduler.start()
        print("\n=== Scheduler Service Initialized ===")
        print("Production mode: checking for upcoming projects daily at 9:00 AM")
        print("Next check scheduled for: 9:00 AM tomorrow")
        print("=======================================\n")

    def check_upcoming_projects(self):
        """Check for projects scheduled for tomorrow and send reminder emails."""
        with self.app.app_context():
            try:
                # Get tomorrow's date
                tomorrow = datetime.now().date() + timedelta(days=1)
                print(f"\n=== Checking Projects [{datetime.now()}] ===")
                print(f"Looking for projects scheduled for: {tomorrow}")

                # Query for projects scheduled for tomorrow
                projects = Project.query.filter_by(date=tomorrow).all()
                print(f"Found {len(projects)} projects scheduled for tomorrow")

                # Send reminders for each project
                for project in projects:
                    try:
                        # Get customer details
                        customer = Customer.query.get(project.customer_id)
                        if not customer or not customer.email:
                            print(f"No customer or email found for project {project.id}")
                            continue

                        print(f"Sending reminder for project {project.id}")
                        print(f"Customer: {customer.name}")
                        print(f"Email: {customer.email}")
                        print(f"Project Date: {project.date}")
                        print(f"Address: {project.address}")
                        
                        # Send reminder email
                        self.email_service.send_project_reminder(
                            customer_email=customer.email,
                            customer_name=customer.name,
                            project_date=project.date.strftime('%Y-%m-%d'),
                            address=project.address,
                            customer_phone=customer.phone,
                            po=project.po,
                            city=project.city,
                            subdivision=project.subdivision,
                            lot_number=project.lot_number,
                            square_footage=project.square_footage,
                            job_cost_type=project.job_cost_type.split(',') if project.job_cost_type else [],
                            work_type=project.work_type.split(',') if project.work_type else [],
                            notes=project.notes,
                            region=project.region
                        )
                        print(f"✓ Reminder sent successfully for project {project.id}")

                    except Exception as e:
                        print(f"Error sending reminder for project {project.id}: {str(e)}")
                        continue

                print("=== Check Complete ===\n")

            except Exception as e:
                print(f"Error checking upcoming projects: {str(e)}")

    def shutdown(self):
        """Shut down the scheduler."""
        self.scheduler.shutdown()
        print("Scheduler shut down") 