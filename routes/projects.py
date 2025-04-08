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
    try:
        print(f"Getting projects for region: {region}")
        # Use subquery to ensure we get unique projects
        subquery = db.session.query(Project.id).filter_by(region=region).group_by(Project.id).subquery()
        projects = Project.query.filter(Project.id.in_(subquery)).order_by(Project.date).all()
        print(f"Found {len(projects)} projects")
        
        project_list = []
        seen_ids = set()  # Extra safety check
        
        for project in projects:
            if project.id not in seen_ids:  # Extra safety check
                seen_ids.add(project.id)
                print(f"Project {project.id}: Found customer {project.customer.name if project.customer else 'Unknown'}")
                
                project_dict = {
                    'id': project.id,
                    'date': project.date.strftime('%Y-%m-%d'),
                    'po': project.po,
                    'customer_name': project.customer.name if project.customer else "Unknown",
                    'customer_phone': project.customer.phone if project.customer else "",
                    'customer_email': project.customer.email if project.customer else "",
                    'address': project.address,
                    'city': project.city,
                    'subdivision': project.subdivision,
                    'lot_number': project.lot_number,
                    'square_footage': project.square_footage,
                    'job_cost_type': project.job_cost_type.split(',') if project.job_cost_type else [],
                    'work_type': project.work_type.split(',') if project.work_type else [],
                    'notes': project.notes,
                    'region': project.region
                }
                project_list.append(project_dict)
        
        print(f"Returning {len(project_list)} unique projects")
        return jsonify(project_list)
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
def create_project(region):
    try:
        print(f"\n=== Creating Project in {region} Region ===")
        project_data = request.json
        print(f"Project data received:")
        print(f"  Work Types: {project_data.get('work_type', [])}")
        print(f"  Job Cost Types: {project_data.get('job_cost_type', [])}")
        
        # Check if customer already exists
        customer = Customer.query.filter_by(
            phone=project_data['customer_phone']
        ).first()
        
        # Create new customer if:
        # 1. Customer doesn't exist, or
        # 2. Customer exists but has a different name
        if not customer or customer.name != project_data['customer_name']:
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
            # Only update email if provided and different
            if project_data.get('customer_email') and project_data.get('customer_email') != customer.email:
                customer.email = project_data.get('customer_email')

        # Create new project
        work_type_str = ','.join(project_data.get('work_type', []))
        job_cost_type_str = ','.join(project_data.get('job_cost_type', []))
        
        print("\nCreating project with types:")
        print(f"  Work Types (raw): {project_data.get('work_type', [])}")
        print(f"  Work Types (joined): {work_type_str}")
        print(f"  Job Cost Types (raw): {project_data.get('job_cost_type', [])}")
        print(f"  Job Cost Types (joined): {job_cost_type_str}")
        
        project = Project(
            id=str(uuid.uuid4()),
            date=datetime.strptime(project_data['date'], '%Y-%m-%d').date(),
            po=project_data.get('po'),
            address=project_data['address'],
            city=project_data.get('city'),
            subdivision=project_data.get('subdivision'),
            lot_number=project_data.get('lot_number'),
            square_footage=project_data.get('square_footage'),
            job_cost_type=job_cost_type_str,
            work_type=work_type_str,
            notes=project_data.get('notes'),
            region=region,
            customer_id=customer.id
        )
        
        db.session.add(project)
        db.session.commit()
        print(f"\nCreated project with ID: {project.id}")
        
        # Send email confirmation if customer has email
        if customer.email:
            try:
                print(f"Attempting to send email to {customer.email}")
                email_service = EmailService()
                email_service.send_project_confirmation(
                    customer_email=customer.email,
                    customer_name=customer.name,
                    project_date=project_data['date'],
                    address=project_data['address'],
                    work_type=project_data.get('work_type', []),
                    job_cost_type=project_data.get('job_cost_type', []),
                    city=project_data.get('city'),
                    subdivision=project_data.get('subdivision'),
                    lot_number=project_data.get('lot_number'),
                    square_footage=project_data.get('square_footage'),
                    notes=project_data.get('notes'),
                    customer_phone=project_data.get('customer_phone'),
                    region=region
                )
            except Exception as e:
                print(f"Error sending email: {str(e)}")
        
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
            print(f"Error sending SMS: {str(e)}")
            # Don't fail the request if SMS fails
        
        # Export project to CSV
        try:
            export_region_projects(region)
        except Exception as e:
            print(f"Error exporting project: {str(e)}")
        
        return jsonify({
            'message': 'Project created successfully',
            'project': {
                'id': project.id,
                'date': project.date.strftime('%Y-%m-%d'),
                'customer_name': customer.name,
                'address': project.address
            }
        })
        
    except Exception as e:
        print(f"Error creating project: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

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
@token_required
def update_project(current_user, region, project_id):
    try:
        print(f"Received update request for project {project_id} in region {region}")
        project_data = request.json
        print(f"Update data received: {project_data}")
        
        project = Project.query.get(project_id)
        if not project:
            print(f"Project {project_id} not found")
            return jsonify({"error": "Project not found"}), 404
        
        if project.region != region:
            print(f"Project {project_id} belongs to region {project.region}, not {region}")
            return jsonify({"error": "Project does not belong to this region"}), 400

        # Update project details
        try:
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
            print(f"Updated project details for {project_id}")
        except KeyError as e:
            print(f"Missing required field: {str(e)}")
            return jsonify({"error": f"Missing required field: {str(e)}"}), 400
        except Exception as e:
            print(f"Error updating project details: {str(e)}")
            return jsonify({"error": f"Error updating project details: {str(e)}"}), 500

        # Handle customer updates
        try:
            current_customer = Customer.query.get(project.customer_id)
            
            # If customer name or phone has changed, create a new customer
            if (current_customer.name != project_data['customer_name'] or 
                current_customer.phone != project_data['customer_phone']):
                print(f"Customer details changed, creating new customer record")
                new_customer = Customer(
                    name=project_data['customer_name'],
                    phone=project_data['customer_phone'],
                    email=project_data.get('customer_email')
                )
                db.session.add(new_customer)
                db.session.flush()  # Get the new customer ID
                project.customer_id = new_customer.id
                customer = new_customer
            else:
                # Only update email if it changed
                if project_data.get('customer_email') and project_data['customer_email'] != current_customer.email:
                    current_customer.email = project_data['customer_email']
                customer = current_customer
                
            print(f"Updated customer details for project {project_id}")
        except KeyError as e:
            print(f"Missing required customer field: {str(e)}")
            return jsonify({"error": f"Missing required customer field: {str(e)}"}), 400
        except Exception as e:
            print(f"Error updating customer details: {str(e)}")
            return jsonify({"error": f"Error updating customer details: {str(e)}"}), 500

        # Send update email if customer has email
        if customer and customer.email:
            email_service = EmailService()
            try:
                print(f"Attempting to send update email to {customer.email}")
                email_service.send_project_update(
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
                print("Update email sent successfully")
            except Exception as e:
                print(f"Error sending update email: {str(e)}")
                # Don't return error here, just log it

        try:
            db.session.commit()
            print(f"Successfully committed updates for project {project_id}")
            
            # Export updated projects to CSV after update
            try:
                print(f"Exporting projects for region {region} to CSV...")
                export_region_projects(region)
                print("CSV export completed successfully")
            except Exception as e:
                print(f"Warning: Failed to export to CSV: {str(e)}")
            
            return jsonify({
                "message": "Project updated successfully",
                "project": {
                    "id": project.id,
                    "date": project.date.strftime('%Y-%m-%d'),
                    "po": project.po,
                    "customer_name": customer.name,
                    "customer_phone": customer.phone,
                    "customer_email": customer.email,
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
            })
        except Exception as e:
            db.session.rollback()
            print(f"Error committing updates: {str(e)}")
            return jsonify({"error": f"Error saving updates: {str(e)}"}), 500
            
    except Exception as e:
        db.session.rollback()
        print(f"Unexpected error updating project: {str(e)}")
        return jsonify({"error": str(e)}), 500

@projects_bp.route('/<project_id>', methods=['DELETE'])
@token_required
def delete_project(current_user, project_id):
    try:
        project = Project.query.get(project_id)
        if not project:
            return jsonify({"error": "Project not found"}), 404

        # Store region and customer ID before deleting project
        region = project.region
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

        # Export updated projects to CSV after deletion
        try:
            print(f"Exporting projects for region {region} to CSV...")
            export_region_projects(region)
            print("CSV export completed successfully")
        except Exception as e:
            print(f"Warning: Failed to export to CSV: {str(e)}")
        
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

@projects_bp.route('/<region>/latest', methods=['GET'])
def get_latest_project(region):
    try:
        print(f"Getting latest project for region: {region}")
        # Get the most recent project for the region
        project = Project.query.filter_by(region=region).order_by(Project.created_at.desc()).first()
        
        if not project:
            return jsonify({"error": "No projects found"}), 404
            
        print(f"Found latest project {project.id}")
        
        project_dict = {
            'id': project.id,
            'date': project.date.strftime('%Y-%m-%d'),
            'po': project.po,
            'customer_name': project.customer.name if project.customer else "Unknown",
            'customer_phone': project.customer.phone if project.customer else "",
            'customer_email': project.customer.email if project.customer else "",
            'address': project.address,
            'city': project.city,
            'subdivision': project.subdivision,
            'lot_number': project.lot_number,
            'square_footage': project.square_footage,
            'job_cost_type': project.job_cost_type.split(',') if project.job_cost_type else [],
            'work_type': project.work_type.split(',') if project.work_type else [],
            'notes': project.notes,
            'region': project.region
        }
        
        print(f"Returning latest project data")
        return jsonify(project_dict)
    except Exception as e:
        print(f"Error getting latest project: {str(e)}")
        return jsonify({"error": str(e)}), 500

@projects_bp.route('/<region>/date/<date>', methods=['GET'])
def get_projects_by_date(region, date):
    try:
        print(f"Getting projects for region {region} on date {date}")
        # Parse the date string to a datetime object
        target_date = datetime.strptime(date, '%Y-%m-%d').date()
        
        # Query projects for the specific date and region
        projects = Project.query.filter_by(
            region=region,
            date=target_date
        ).all()
        
        print(f"Found {len(projects)} projects")
        project_list = []
        
        for project in projects:
            print(f"Processing project {project.id}")
            project_dict = {
                'id': project.id,
                'date': project.date.strftime('%Y-%m-%d'),
                'po': project.po,
                'customer_name': project.customer.name if project.customer else "Unknown",
                'customer_phone': project.customer.phone if project.customer else "",
                'customer_email': project.customer.email if project.customer else "",
                'address': project.address,
                'city': project.city,
                'subdivision': project.subdivision,
                'lot_number': project.lot_number,
                'square_footage': project.square_footage,
                'job_cost_type': project.job_cost_type.split(',') if project.job_cost_type else [],
                'work_type': project.work_type.split(',') if project.work_type else [],
                'notes': project.notes,
                'region': project.region
            }
            project_list.append(project_dict)
        
        print(f"Returning {len(project_list)} projects")
        return jsonify(project_list)
    except Exception as e:
        print(f"Error getting projects by date: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(port=5001, debug=True) 