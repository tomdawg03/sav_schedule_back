from flask import Flask, request, jsonify
from flask_login import LoginManager
from flask_cors import CORS
from config import Config
from models import db
from models.user import User
from routes.auth import auth
from models.customer import Customer
from services.sms_service import SMSService
import json
from datetime import datetime
import uuid  # Add this at the top of your file
from models.project import Project

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize extensions
    CORS(app)  # Enable CORS for all routes
    db.init_app(app)
    
    login_manager = LoginManager()
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register blueprints
    app.register_blueprint(auth, url_prefix='/api/auth')

    # Create database tables
    with app.app_context():
        db.create_all()

    # This is temporary storage - you'd typically use a database
    users = {}
    projects = {
        'northern': [],
        'southern': []
    }

    @app.route('/signup', methods=['POST'])
    def signup():
        try:
            data = request.json
            if not data:
                return jsonify({'error': 'No data received'}), 400

            username = data.get('username')
            password = data.get('password')

            if not username or not password:
                return jsonify({'error': 'Username and password are required'}), 400
            
            # Validate password
            if len(password) < 6:
                return jsonify({'error': 'Password must be at least 6 characters long'}), 400
            
            if not any(char.isdigit() for char in password):
                return jsonify({'error': 'Password must contain at least one number'}), 400
            
            if username in users:
                return jsonify({'error': 'Username already exists'}), 400
            
            users[username] = password
            return jsonify({'message': 'User created successfully'}), 200
            
        except Exception as e:
            print(f"Signup error: {str(e)}")  # Server-side logging
            return jsonify({'error': f'Server error: {str(e)}'}), 500

    @app.route('/login', methods=['POST'])
    def login():
        data = request.json
        username = data.get('username')
        password = data.get('password')
        
        if username in users and users[username] == password:
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
            print("Project saved successfully")  # Debug log
            
            return jsonify({
                "message": "Project created successfully",
                "project": {
                    "id": project.id,
                    "date": project_data['date'],
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

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(port=5001, debug=True)