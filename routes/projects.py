from flask import Blueprint, request, jsonify, send_file
from flask_login import current_user, login_required
from models import db
from models.project import Project
from models.customer import Customer
from services.sms_service import SMSService
from services.email_service import EmailService
from datetime import datetime
import uuid
from routes.auth import token_required
import csv
import io
import os

projects_bp = Blueprint('projects', __name__)

@projects_bp.route('/<region>', methods=['GET'])
def get_projects(region):
    print(f"GET request received for {region} projects")  # Debug print
    try:
        # Get projects from database
        db_projects = Project.query.filter_by(region=region).all()
        print(f"Found {len(db_projects)} projects in database for region {region}")
        
        # Convert to list of dictionaries
        projects_list = []
        for project in db_projects:
            customer = Customer.query.get(project.customer_id)
            project_dict = {
                "id": project.id,
                "date": project.date.strftime('%Y-%m-%d'),
                "po": project.po,
                "customer_name": customer.name if customer else "Unknown",
                "customer_phone": customer.phone if customer else None,
                "customer_email": customer.email if customer else None,
                "address": project.address,
                "city": project.city,
                "subdivision": project.subdivision,
                "lot_number": project.lot_number,
                "square_footage": project.square_footage,
                "job_cost_type": project.job_cost_type.split(',') if project.job_cost_type else [],
                "work_type": project.work_type.split(',') if project.work_type else [],
                "notes": project.notes,
                "region": project.region
            }
            projects_list.append(project_dict)
        
        print(f"Returning projects: {projects_list}")  # Debug print
        return jsonify(projects_list)
    except Exception as e:
        print(f"Error getting projects: {str(e)}")
        return jsonify({"error": str(e)}), 500

def export_region_projects(region):
    try:
        # Get all projects for the specific region
        projects = Project.query.filter_by(region=region).all()
        
        # Create export directory if it doesn't exist
        export_dir = 'exports'
        if not os.path.exists(export_dir):
            os.makedirs(export_dir)
        
        # Fixed filename for each region
        filepath = os.path.join(export_dir, f'projects_{region}.csv')
        
        # Check if file exists to determine if we need to write headers
        file_exists = os.path.exists(filepath)
        
        # Open file in append mode
        with open(filepath, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Write header only if file is new
            if not file_exists:
                writer.writerow([
                    'Project ID',
                    'Customer Name',
                    'Customer Email',
                    'Customer Phone',
                    'Date',
                    'PO',
                    'Address',
                    'City',
                    'Subdivision',
                    'Lot Number',
                    'Square Footage',
                    'Job Cost Type',
                    'Work Type',
                    'Notes',
                    'Created At',
                    'Updated At'
                ])
            
            # Write only the most recently added project
            latest_project = projects[-1] if projects else None
            if latest_project:
                writer.writerow([
                    latest_project.id,
                    latest_project.customer.name if latest_project.customer else 'N/A',
                    latest_project.customer.email if latest_project.customer else 'N/A',
                    latest_project.customer.phone if latest_project.customer else 'N/A',
                    latest_project.date.strftime('%Y-%m-%d'),
                    latest_project.po or 'N/A',
                    latest_project.address,
                    latest_project.city or 'N/A',
                    latest_project.subdivision or 'N/A',
                    latest_project.lot_number or 'N/A',
                    latest_project.square_footage or 'N/A',
                    latest_project.job_cost_type or 'N/A',
                    latest_project.work_type or 'N/A',
                    latest_project.notes or 'N/A',
                    latest_project.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    latest_project.updated_at.strftime('%Y-%m-%d %H:%M:%S')
                ])
            
        print(f"Added new project to {filepath}")
        
    except Exception as e:
        print(f"Error exporting {region} projects: {str(e)}")

@projects_bp.route('/<region>', methods=['POST'])
@token_required
def create_project(current_user, region):
    try:
        print(f"Received project creation request for region: {region}")
        project_data = request.json
        print(f"Project data received: {project_data}")
        
        # Check if customer already exists
        customer = Customer.query.filter_by(
            phone=project_data['customer_phone']
        ).first()
        
        if not customer:
            print(f"Creating new customer: {project_data['customer_name']}")
            customer = Customer(
                name=project_data['customer_name'],
                phone=project_data['customer_phone'],
                email=project_data.get('customer_email')
            )
            db.session.add(customer)
            db.session.flush()
        else:
            print(f"Found existing customer: {customer.name}")
            # Update customer email if provided
            if project_data.get('customer_email'):
                customer.email = project_data.get('customer_email')

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
        print(f"Created project with ID: {project.id}")
        
        # Schedule SMS notification
        sms_service = SMSService()
        try:
            print(f"Attempting to send SMS to {customer.phone}")
            sms_service.schedule_project_notification(
                phone_number=customer.phone,
                customer_name=customer.name,
                project_date=project_data['date'],
                address=project_data['address']
            )
        except Exception as e:
            print(f"Error scheduling SMS: {str(e)}")

        # Send confirmation email
        email_service = EmailService()
        try:
            print(f"Attempting to send confirmation email to {customer.email}")
            email_service.send_project_confirmation(
                customer_email=customer.email,
                customer_name=customer.name,
                project_date=project_data['date'],
                address=project_data['address'],
                customer_phone=customer.phone,
                po=project_data.get('po'),
                city=project_data.get('city'),
                subdivision=project_data.get('subdivision'),
                lot_number=project_data.get('lot_number'),
                square_footage=project_data.get('square_footage'),
                job_cost_type=project_data.get('job_cost_type', []),
                work_type=project_data.get('work_type', []),
                notes=project_data.get('notes'),
                region=region
            )
        except Exception as e:
            print(f"Error sending confirmation email: {str(e)}")
        
        db.session.commit()
        print("Project saved successfully")
        
        # Export updated CSV file only for the affected region
        export_region_projects(region)
        
        return jsonify({
            "message": "Project created successfully",
            "project": {
                "id": project.id,
                "date": project_data['date'],
                "po": project_data.get('po'),
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
        print(f"Error creating project: {str(e)}")
        return jsonify({"error": str(e)}), 500

@projects_bp.route('/<region>/<project_id>', methods=['GET'])
def get_project(region, project_id):
    try:
        project = Project.query.get(project_id)
        if not project or project.region != region:
            return jsonify({"error": "Project not found"}), 404
            
        customer = Customer.query.get(project.customer_id)
        project_dict = {
            "id": project.id,
            "date": project.date.strftime('%Y-%m-%d'),
            "po": project.po,
            "customer_name": customer.name if customer else "Unknown",
            "customer_phone": customer.phone if customer else None,
            "customer_email": customer.email if customer else None,
            "address": project.address,
            "city": project.city,
            "subdivision": project.subdivision,
            "lot_number": project.lot_number,
            "square_footage": project.square_footage,
            "job_cost_type": project.job_cost_type.split(',') if project.job_cost_type else [],
            "work_type": project.work_type.split(',') if project.work_type else [],
            "notes": project.notes,
            "region": project.region
        }
        return jsonify(project_dict)
    except Exception as e:
        print(f"Error getting project: {str(e)}")
        return jsonify({"error": str(e)}), 500

@projects_bp.route('/<region>/<project_id>', methods=['PUT'])
@login_required
def update_project(region, project_id):
    try:
        project_data = request.json
        project = Project.query.get(project_id)
        if not project:
            return "Project not found", 404

        # Update project details
        project.date = datetime.strptime(project_data['date'], '%Y-%m-%d').date()
        project.po = project_data.get('po')
        project.address = project_data['address']
        project.city = project_data.get('city')
        project.subdivision = project_data.get('subdivision')
        project.lot_number = project_data.get('lot_number')
        project.square_footage = project_data.get('square_footage')
        project.job_cost_type = ','.join(project_data.get('job_cost_type', []))
        project.work_type = ','.join(project_data.get('work_type', []))
        project.notes = project_data.get('notes')

        # Update customer details
        customer = Customer.query.get(project.customer_id)
        if customer:
            customer.name = project_data['customer_name']
            customer.phone = project_data['customer_phone']
            customer.email = project_data.get('customer_email')

            # Send update email
            email_service = EmailService()
            try:
                print(f"Attempting to send update email to {customer.email}")
                email_service.send_project_update(
                    customer_email=customer.email,
                    customer_name=customer.name,
                    project_date=project_data['date'],
                    address=project_data['address']
                )
            except Exception as e:
                print(f"Error sending update email: {str(e)}")

        db.session.commit()
        return jsonify({"message": "Project updated successfully"})
    except Exception as e:
        db.session.rollback()
        print(f"Error updating project: {str(e)}")
        return jsonify({"error": str(e)}), 500

@projects_bp.route('/<project_id>', methods=['DELETE'])
@token_required
def delete_project(current_user, project_id):
    try:
        project = Project.query.get(project_id)
        if not project:
            return jsonify({"error": "Project not found"}), 404

        # Store customer ID before deleting project
        customer_id = project.customer_id
        
        # Delete the project
        db.session.delete(project)
        
        # Check if customer has any other projects
        other_projects = Project.query.filter_by(customer_id=customer_id).count()
        if other_projects == 0:
            # If this was the customer's only project, delete the customer too
            customer = Customer.query.get(customer_id)
            if customer:
                db.session.delete(customer)
        
        db.session.commit()
        return jsonify({"message": "Project deleted successfully"})
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting project: {str(e)}")
        return jsonify({"error": str(e)}), 500

@projects_bp.route('/export', methods=['GET'])
def export_projects():
    try:
        # Get all projects with their customer information
        projects = Project.query.all()
        
        # Create a StringIO object to write CSV data
        si = io.StringIO()
        writer = csv.writer(si)
        
        # Write header
        writer.writerow([
            'Project ID',
            'Customer Name',
            'Customer Email',
            'Date',
            'Region',
            'Description',
            'Work Type',
            'Status',
            'Created At',
            'Updated At'
        ])
        
        # Write data
        for project in projects:
            writer.writerow([
                project.id,
                project.customer.name if project.customer else 'N/A',
                project.customer.email if project.customer else 'N/A',
                project.date.strftime('%Y-%m-%d'),
                project.region,
                project.description,
                project.work_type,
                project.status,
                project.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                project.updated_at.strftime('%Y-%m-%d %H:%M:%S')
            ])
        
        # Create the response
        output = si.getvalue()
        si.close()
        
        return send_file(
            io.BytesIO(output.encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'projects_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500 