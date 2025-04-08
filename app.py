from flask import Flask, request, jsonify, render_template, send_file, redirect, url_for, session
from flask_login import LoginManager, current_user, login_required, login_user, logout_user
from flask_cors import CORS
from config import Config
from models import db, init_app
from models.user import User, PERMISSIONS, Role, ROLES
from routes.auth import auth
from routes.user_management import user_management
from routes.projects import projects_bp
from models.customer import Customer
from services.sms_service import SMSService
from services.email_service import EmailService
from services.scheduler_service import SchedulerService
from flask_jwt_extended import JWTManager
import json
from datetime import datetime, timedelta
import uuid
from models.project import Project
import csv
from io import StringIO
import os
from dotenv import load_dotenv
from routes.analytics import analytics
from services.csv_service import import_customers_from_csv
import requests
import atexit

# Load environment variables from .env file
load_dotenv()

# Create data directory if it doesn't exist
data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'data'))
if not os.path.exists(data_dir):
    os.makedirs(data_dir)
    print(f"Created data directory at: {data_dir}")

# Initialize Flask app
app = Flask(__name__, 
           template_folder='../sav_schedule_front/templates',
           static_folder='../sav_schedule_front/static',
           static_url_path='/static')
app.config.from_object(Config)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///scheduler.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize JWT with additional configuration
jwt = JWTManager(app)
app.config['JWT_TOKEN_LOCATION'] = ['headers']
app.config['JWT_HEADER_NAME'] = 'Authorization'
app.config['JWT_HEADER_TYPE'] = 'Bearer'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)

# Initialize CORS with support for credentials
CORS(app, resources={
    r"/*": {
        "origins": ["http://127.0.0.1:5000", "http://localhost:5000"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True,
        "allow_credentials": True
    }
})

# Initialize database
db.init_app(app)

# Initialize Login Manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Register blueprints
app.register_blueprint(auth, url_prefix='/auth')
app.register_blueprint(analytics, url_prefix='/analytics')
app.register_blueprint(projects_bp, url_prefix='/projects')
app.register_blueprint(user_management, url_prefix='/auth')  # Add auth prefix

def init_database():
    """Initialize the database with required tables and initial data."""
    with app.app_context():
        # Create all tables
        print("Creating database tables...")
        db.create_all()

        # Initialize roles
        print("Initializing roles...")
        for role_name, role_data in ROLES.items():
            try:
                role = Role.query.filter_by(name=role_name).first()
                if not role:
                    print(f"Creating role: {role_name}")
                    role = Role(
                        name=role_name,
                        description=role_data['description'],
                        permissions=role_data['permissions']
                    )
                    db.session.add(role)
                    db.session.commit()
            except Exception as e:
                db.session.rollback()
                print(f"Error creating role {role_name}: {str(e)}")
                raise

        # Import customers if CSV exists
        csv_path = os.path.join(data_dir, 'cust_list.csv')
        if os.path.exists(csv_path):
            print("Importing customers from CSV...")
            try:
                with open(csv_path, 'r') as file:
                    csv_reader = csv.DictReader(file)
                    imported_count = 0
                    for row in csv_reader:
                        try:
                            name = row.get('Customer', '').strip()
                            if not name:
                                name = f"{row.get('First_Name', '')} {row.get('Last_Name', '')}".strip()
                            
                            if name and row.get('Phone'):
                                customer = Customer(
                                    name=name,
                                    phone=row.get('Phone'),
                                    email=row.get('Main_Email', '')
                                )
                                db.session.add(customer)
                                imported_count += 1
                        except Exception as e:
                            print(f"Error importing customer: {str(e)}")
                            continue
                    
                    db.session.commit()
                    print(f"Successfully imported {imported_count} customers")
            except Exception as e:
                db.session.rollback()
                print(f"Error during customer import: {str(e)}")
        else:
            print(f"Customer CSV file not found at {csv_path}")

# Initialize database
init_database()

# Initialize scheduler service
scheduler_service = SchedulerService(app)

# Register shutdown function
@atexit.register
def shutdown_scheduler():
    scheduler_service.shutdown()

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('auth.login'))

@app.route('/login')
def login_redirect():
    return redirect(url_for('auth.login'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', 
                        username=current_user.username,
                        role=current_user.role.name if current_user.role else None)

@app.route('/calendar/<region>')
@login_required
def calendar(region):
    try:
        # Get projects for this region
        projects = Project.query.filter_by(region=region).all()
        
        # Format projects for the calendar
        projects_list = []
        for project in projects:
            customer = Customer.query.get(project.customer_id)
            project_data = {
                'id': project.id,
                'date': project.date.strftime('%Y-%m-%d'),
                'customer_name': customer.name if customer else 'Unknown',
                'address': project.address,
                'city': project.city,
                'work_type': project.work_type.split(',') if project.work_type else [],
                'job_cost_type': project.job_cost_type.split(',') if project.job_cost_type else []
            }
            projects_list.append(project_data)
        
        # Convert to JSON for the template
        projects_json = json.dumps(projects_list)
        
        return render_template('calendar.html',
                            region=region,
                            username=current_user.username,
                            role=current_user.role.name if current_user.role else None,
                            projects=projects_list,
                            projects_json=projects_json)
    except Exception as e:
        print(f"Exception in calendar route: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return render_template('calendar.html',
                            region=region,
                            username=current_user.username,
                            role=current_user.role.name if current_user.role else None,
                            projects=[],
                            projects_json='[]')

@app.route('/import-customers', methods=['POST'])
def import_customers():
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        if not file.filename.endswith('.csv'):
            return jsonify({"error": "File must be a CSV"}), 400
        
        # Read the CSV file
        stream = StringIO(file.stream.read().decode("UTF8"), newline=None)
        csv_data = csv.DictReader(stream)
        
        imported_count = 0
        for row in csv_data:
            # Check if customer already exists by phone number
            existing_customer = Customer.query.filter_by(phone=row.get('phone')).first()
            if not existing_customer:
                customer = Customer(
                    name=row.get('name'),
                    phone=row.get('phone'),
                    email=row.get('email')
                )
                db.session.add(customer)
                imported_count += 1
        
        db.session.commit()
        return jsonify({"message": f"Successfully imported {imported_count} customers"})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route('/search-customers', methods=['GET'])
def search_customers():
    try:
        search_term = request.args.get('q', '')
        print(f"Received search request with term: {search_term}")
        
        if not search_term:
            print("No search term provided, returning empty list")
            return jsonify([])
        
        # Search by name, phone, or email
        customers = Customer.query.filter(
            db.or_(
                Customer.name.ilike(f'%{search_term}%'),
                Customer.phone.ilike(f'%{search_term}%'),
                Customer.email.ilike(f'%{search_term}%')
            )
        ).limit(10).all()
        
        print(f"Found {len(customers)} matching customers")
        result = [{
            'id': c.id,
            'name': c.name,
            'phone': c.phone,
            'email': c.email
        } for c in customers]
        print(f"Returning results: {result}")
        return jsonify(result)
        
    except Exception as e:
        print(f"Error in search_customers: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/import-customers-from-csv', methods=['GET'])
def import_customers_from_csv():
    try:
        csv_path = 'data/cust_list.csv'
        imported_count = 0
        updated_count = 0
        
        with open(csv_path, 'r', encoding='utf-8') as file:
            csv_data = csv.DictReader(file)
            # Print headers to verify what we're reading
            print(f"CSV Headers: {csv_data.fieldnames}")
            
            for row in csv_data:
                # Print first row to see the data structure
                if imported_count == 0:
                    print(f"First row data: {row}")
                
                # Check if customer already exists by phone number
                phone = row.get('Phone', '').strip()  # Remove any whitespace
                if not phone:  # Skip rows without phone numbers
                    continue
                    
                existing_customer = Customer.query.filter_by(phone=phone).first()
                
                if existing_customer:
                    # Update existing customer
                    existing_customer.name = row.get('Customer', '')
                    existing_customer.first_name = row.get('First_Name', '')
                    existing_customer.last_name = row.get('Last_Name', '')
                    existing_customer.email = row.get('Main_Email', '')
                    updated_count += 1
                else:
                    # Create new customer
                    customer = Customer(
                        name=row.get('Customer', ''),
                        first_name=row.get('First_Name', ''),
                        last_name=row.get('Last_Name', ''),
                        phone=phone,
                        email=row.get('Main_Email', '')
                    )
                    db.session.add(customer)
                    imported_count += 1
        
        db.session.commit()
        return jsonify({
            'message': f'Successfully imported {imported_count} new customers and updated {updated_count} existing customers'
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Error importing customers: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/confirmation/<region>', methods=['GET'])
def confirmation(region):
    if 'user' not in session:
        return redirect(url_for('auth.login'))
    
    try:
        # Get the most recently created project from the backend
        response = requests.get(
            f'{BACKEND_URL}/projects/{region}/latest',
            headers={'Authorization': f"Bearer {session['user']['token']}"}
        )
        
        if response.ok:
            project_data = response.json()
            return render_template('confirmation.html', project=project_data, region=region)
        else:
            return redirect(url_for('create_project', region=region))
            
    except Exception as e:
        print(f"Error in confirmation route: {str(e)}")
        return redirect(url_for('create_project', region=region))

@app.route('/create-project/<region>', methods=['GET', 'POST'])
@login_required
def create_project(region):
    if 'user' not in session:
        return redirect(url_for('auth.login'))
    return render_template('create_project.html', region=region)

@app.route('/analytics')
@login_required
def analytics_page():
    if not current_user.is_admin():
        return redirect(url_for('dashboard'))
    return render_template('analytics.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
