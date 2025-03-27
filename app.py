from flask import Flask, request, jsonify
<<<<<<< HEAD
from flask_login import LoginManager, current_user, login_required
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
=======
from flask_login import LoginManager
from flask_cors import CORS
from config import Config
from models import db, init_app
from models.user import User
from routes.auth import auth
from models.customer import Customer
from services.sms_service import SMSService
>>>>>>> 9e888cc9d22dfe916ed96e30e883c8cbf60cef19
import json
from datetime import datetime
import uuid
from models.project import Project
import csv
from io import StringIO

app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
<<<<<<< HEAD
CORS(app, supports_credentials=True, resources={
    r"/*": {
        "origins": ["http://localhost:5000"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True
    }
})
init_app(app)

# Initialize Login Manager
=======
CORS(app)
init_app(app)

>>>>>>> 9e888cc9d22dfe916ed96e30e883c8cbf60cef19
login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

<<<<<<< HEAD
# Register blueprints
app.register_blueprint(auth, url_prefix='/auth')
app.register_blueprint(user_management, url_prefix='/user-management')
app.register_blueprint(projects_bp, url_prefix='/api/projects')
=======
# Register blueprints - remove the url_prefix
app.register_blueprint(auth)

# Create database tables
with app.app_context():
    db.create_all()

# This is temporary storage for projects
projects = {
    'northern': [],
    'southern': []
}

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    user = User.query.filter_by(username=username).first()
    if user and user.check_password(password):
        return jsonify({'username': username}), 200
    
    return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/projects/<region>', methods=['GET'])
def get_projects(region):
    print(f"GET request received for {region} projects")  # Debug print
    region_projects = projects.get(region, [])
    print(f"Returning projects: {region_projects}")  # Debug print
    return jsonify(region_projects)

@app.route('/projects/<region>', methods=['POST'])
def create_project(region):
    try:
        print(f"Received project creation request for region: {region}")  # Debug log
        project_data = request.json
        print(f"Project data received: {project_data}")  # Debug log
        
        # Check if customer already exists
        customer = Customer.query.filter_by(
            phone=project_data['customer_phone']
        ).first()
        
        if not customer:
            print(f"Creating new customer: {project_data['customer_name']}")  # Debug log
            # Create new customer
            customer = Customer(
                name=project_data['customer_name'],
                phone=project_data['customer_phone'],
                email=project_data.get('customer_email')
            )
            db.session.add(customer)
            db.session.flush()
        else:
            print(f"Found existing customer: {customer.name}")  # Debug log

        # Create new project
        project = Project(
            id=str(uuid.uuid4()),
            date=datetime.strptime(project_data['date'], '%Y-%m-%d').date(),
            po=project_data.get('po'),
            address=project_data['address'],
            city=project_data.get('city'),
            subdivision=project_data.get('subdivision'),
            lot_number=project_data.get('lot_number'),
            square_footage=project_data.get('square_footage'),
            job_cost_type=','.join(project_data.get('job_cost_type', [])),
            work_type=','.join(project_data.get('work_type', [])),
            notes=project_data.get('notes'),
            region=region,
            customer_id=customer.id
        )
        
        db.session.add(project)
        print(f"Created project with ID: {project.id}")  # Debug log
        
        # Also store in the projects dictionary for calendar display
        if region not in projects:
            projects[region] = []
        
        projects[region].append({
            "id": project.id,
            "date": project_data['date'],
            "po": project_data.get('po'),  # Include PO in the projects dictionary
            "customer_name": customer.name,
            "customer_phone": customer.phone,
            "customer_email": customer.email,
            "address": project.address,
            "city": project.city,
            "subdivision": project.subdivision,
            "lot_number": project.lot_number,
            "square_footage": project.square_footage,
            "job_cost_type": project_data.get('job_cost_type', []),
            "work_type": project_data.get('work_type', []),
            "notes": project.notes,
            "region": region
        })
        
        # Schedule SMS notification
        sms_service = SMSService()
        try:
            print(f"Attempting to send SMS to {customer.phone}")  # Debug log
            sms_service.schedule_project_notification(
                phone_number=customer.phone,
                customer_name=customer.name,
                project_date=project_data['date'],
                address=project_data['address']
            )
        except Exception as e:
            print(f"Error scheduling SMS: {str(e)}")  # Debug log
        
        db.session.commit()
        print("Project saved successfully")
        
        return jsonify({
            "message": "Project created successfully",
            "project": {
                "id": project.id,
                "date": project_data['date'],
                "po": project_data.get('po'),  # Include PO in the response
                "customer_name": customer.name,
                "customer_phone": customer.phone,
                "customer_email": customer.email,
                "address": project.address,
                "city": project.city,
                "subdivision": project.subdivision,
                "lot_number": project.lot_number,
                "square_footage": project.square_footage,
                "job_cost_type": project_data.get('job_cost_type', []),
                "work_type": project_data.get('work_type', []),
                "notes": project.notes,
                "region": region
            }
        })
    except Exception as e:
        db.session.rollback()
        print(f"Error creating project: {str(e)}")  # Debug log
        return jsonify({"error": str(e)}), 500

@app.route('/projects/<region>/<project_id>', methods=['GET'])
def get_project(region, project_id):
    for project in projects[region]:
        if project['id'] == project_id:
            return jsonify(project)
    return "Project not found", 404

@app.route('/projects/<region>/<project_id>', methods=['PUT'])
def update_project(region, project_id):
    for i, project in enumerate(projects[region]):
        if project['id'] == project_id:
            projects[region][i] = request.json
            return jsonify({"message": "Project updated successfully"})
    return "Project not found", 404

@app.route('/customers', methods=['GET'])
def get_customers():
    customers = Customer.query.all()
    return jsonify([{
        'id': c.id,
        'name': c.name,
        'phone': c.phone,
        'email': c.email
    } for c in customers])

@app.route('/customers/<int:customer_id>', methods=['GET'])
def get_customer(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    return jsonify({
        'id': customer.id,
        'name': customer.name,
        'phone': customer.phone,
        'email': customer.email,
        'projects': [{
            'date': p.date,
            'address': p.address,
            'region': p.region
        } for p in customer.projects]
    })
>>>>>>> 9e888cc9d22dfe916ed96e30e883c8cbf60cef19

@app.route('/import-customers', methods=['POST'])
def import_customers():
    try:
        if 'file' not in request.files:
<<<<<<< HEAD
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        if not file.filename.endswith('.csv'):
            return jsonify({"error": "File must be a CSV"}), 400
        
        # Read CSV file
        stream = StringIO(file.stream.read().decode("UTF8"), newline=None)
        csv_reader = csv.DictReader(stream)
        
        imported_count = 0
        for row in csv_reader:
            # Check if customer already exists by phone number
            existing_customer = Customer.query.filter_by(phone=row.get('phone')).first()
            if not existing_customer:
                customer = Customer(
                    name=row.get('name'),
                    phone=row.get('phone'),
                    email=row.get('email')
=======
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not file.filename.endswith('.csv'):
            return jsonify({'error': 'File must be a CSV'}), 400
        
        # Read the CSV file
        stream = StringIO(file.stream.read().decode("UTF8"), newline=None)
        csv_data = csv.DictReader(stream)
        
        imported_count = 0
        for row in csv_data:
            # Check if customer already exists by phone number
            existing_customer = Customer.query.filter_by(phone=row.get('Phone')).first()
            if not existing_customer:
                customer = Customer(
                    name=row.get('Customer', ''),
                    first_name=row.get('First_Name', ''),
                    last_name=row.get('Last_Name', ''),
                    phone=row.get('Phone', ''),
                    email=row.get('Main_Email', '')
>>>>>>> 9e888cc9d22dfe916ed96e30e883c8cbf60cef19
                )
                db.session.add(customer)
                imported_count += 1
        
        db.session.commit()
<<<<<<< HEAD
        return jsonify({"message": f"Successfully imported {imported_count} customers"})
        
    except Exception as e:
        print(f"Error importing customers: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/search-customers')
def search_customers():
    try:
        query = request.args.get('q', '')
        print(f"Received search query: {query}")
        if not query:
            return jsonify([])

        # Search for customers where name or phone contains the query
        customers = Customer.query.filter(
            (Customer.name.ilike(f'%{query}%')) |
            (Customer.phone.ilike(f'%{query}%'))
        ).all()
        
        print(f"Found {len(customers)} customers matching query")
        
        # Convert to list of dictionaries
        results = [{
            'id': customer.id,
            'name': customer.name,
            'phone': customer.phone,
            'email': customer.email
        } for customer in customers]
        
        print(f"Search results: {results}")
        return jsonify(results)
    except Exception as e:
        print(f"Error searching customers: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Create database tables and initialize roles
with app.app_context():
    print("Creating database tables...")
    db.create_all()
    
    # Initialize roles if they don't exist
    for role_name, role_data in ROLES.items():
        role = Role.query.filter_by(name=role_name).first()
        if not role:
            role = Role(
                name=role_name,
                description=role_data['description'],
                permissions=role_data['permissions']
            )
            db.session.add(role)
    
    # Delete all existing customers and import fresh from CSV
    try:
        print("Deleting existing customers...")
        Customer.query.delete()
        db.session.commit()
        print("Importing customers from CSV...")
        with open('data/cust_list.csv', 'r') as file:
            csv_reader = csv.DictReader(file)
            imported_count = 0
            for row in csv_reader:
                # Use company name if available, otherwise combine first and last name
                name = row['Customer'] if row['Customer'] else f"{row['First_Name']} {row['Last_Name']}".strip()
                customer = Customer(
                    name=name,
                    phone=row['Phone'],
                    email=row['Main_Email']
                )
                db.session.add(customer)
                imported_count += 1
            
            db.session.commit()
            print(f"Successfully imported {imported_count} customers from cust_list.csv")
            
            # Verify the import
            final_count = Customer.query.count()
            print(f"Final customer count in database: {final_count}")
            
            # Print first few customers as sample
            sample_customers = Customer.query.limit(5).all()
            print("Sample of imported customers:")
            for c in sample_customers:
                print(f"- {c.name} ({c.phone})")
    except Exception as e:
        print(f"Error importing customers from CSV: {str(e)}")
        print(f"Error details: {type(e).__name__}")
        import traceback
        traceback.print_exc()
    
    db.session.commit()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
=======
        return jsonify({'message': f'Successfully imported {imported_count} customers'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/search-customers', methods=['GET'])
def search_customers():
    try:
        search_term = request.args.get('q', '')
        if not search_term:
            return jsonify([])
            
        # Search by name, phone, or email
        customers = Customer.query.filter(
            db.or_(
                Customer.name.ilike(f'%{search_term}%'),
                Customer.last_name.ilike(f'%{search_term}%'),
                Customer.phone.ilike(f'%{search_term}%'),
                Customer.email.ilike(f'%{search_term}%')
            )
        ).limit(10).all()
        
        return jsonify([{
            'id': c.id,
            'name': c.name,
            'last_name': c.last_name,
            'phone': c.phone,
            'email': c.email
        } for c in customers])
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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

if __name__ == '__main__':
    app.run(port=5001, debug=True)
>>>>>>> 9e888cc9d22dfe916ed96e30e883c8cbf60cef19
