import csv
from models import db
from models.customer import Customer

def import_customers_from_csv(csv_path):
    """Import customers from a CSV file."""
    try:
        imported_count = 0
        updated_count = 0
        
        with open(csv_path, 'r', encoding='utf-8') as file:
            csv_data = csv.DictReader(file)
            print(f"CSV Headers: {csv_data.fieldnames}")
            
            for row in csv_data:
                if imported_count == 0:
                    print(f"First row data: {row}")
                
                phone = row.get('Phone', '').strip()
                if not phone:
                    continue
                    
                existing_customer = Customer.query.filter_by(phone=phone).first()
                
                if existing_customer:
                    existing_customer.name = row.get('Customer', '')
                    existing_customer.first_name = row.get('First_Name', '')
                    existing_customer.last_name = row.get('Last_Name', '')
                    existing_customer.email = row.get('Main_Email', '')
                    updated_count += 1
                else:
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
        return {
            'imported': imported_count,
            'updated': updated_count,
            'success': True,
            'message': f'Successfully imported {imported_count} new customers and updated {updated_count} existing customers'
        }
        
    except Exception as e:
        db.session.rollback()
        print(f"Error importing customers: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        } 