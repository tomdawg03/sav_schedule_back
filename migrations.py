from app import app, db
from models.project import Project
from models.customer import Customer
from models.user import User, Role

def recreate_database():
    with app.app_context():
        # Drop all tables
        db.drop_all()
        
        # Create all tables with new schema
        db.create_all()
        
        # Initialize roles if needed
        from app import ROLES
        for role_name, role_data in ROLES.items():
            role = Role.query.filter_by(name=role_name).first()
            if not role:
                role = Role(
                    name=role_name,
                    description=role_data['description'],
                    permissions=role_data['permissions']
                )
                db.session.add(role)
        db.session.commit()

        # Create admin user if it doesn't exist
        admin_role = Role.query.filter_by(name='admin').first()
        if not User.query.filter_by(username='admin').first():
            admin_user = User(
                username='admin',
                email='admin@example.com',
                role=admin_role
            )
            admin_user.set_password('Coolio03!')
            db.session.add(admin_user)
            db.session.commit()
            print("Admin user created successfully!")

if __name__ == '__main__':
    recreate_database()
    print("Database recreated successfully!") 