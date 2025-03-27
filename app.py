from flask import Flask, request, jsonify
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
import json
from datetime import datetime
import uuid
from models.project import Project
import csv
from io import StringIO

app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
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
login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Register blueprints
app.register_blueprint(auth, url_prefix='/auth')
app.register_blueprint(user_management, url_prefix='/user-management')
app.register_blueprint(projects_bp, url_prefix='/api/projects')

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
        if not search_term:
            return jsonify([])
        
        # Search by name, phone, or email
        customers = Customer.query.filter(
            db.or_(
                Customer.name.ilike(f'%{search_term}%'),
                Customer.phone.ilike(f'%{search_term}%'),
                Customer.email.ilike(f'%{search_term}%')
            )
        ).limit(10).all()
        
        return jsonify([{
            'id': c.id,
            'name': c.name,
            'phone': c.phone,
            'email': c.email
        } for c in customers])
        
    except Exception as e:
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
