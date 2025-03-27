from app import app
from models import db
from models.user import User, Role, ROLES

def init_db():
    with app.app_context():
        # Drop all existing tables
        print("Dropping existing tables...")
        db.drop_all()
        
        # Create tables
        print("Creating new tables...")
        db.create_all()
        
        # Create roles if they don't exist
        print("Creating roles...")
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
        print("Creating admin user...")
        admin_role = Role.query.filter_by(name='admin').first()
        if not admin_role:
            admin_role = Role(
                name='admin',
                description=ROLES['admin']['description'],
                permissions=ROLES['admin']['permissions']
            )
            db.session.add(admin_role)
            db.session.flush()
            print("Admin role created")

        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            admin_user = User(
                username='admin',
                email='admin@example.com',
                role=admin_role
            )
            admin_user.set_password('Coolio03!')
            db.session.add(admin_user)
            db.session.commit()
            print("Admin user created successfully")
            print("Login credentials:")
            print("Username: admin")
            print("Password: Coolio03!")
        else:
            print("Admin user already exists")

if __name__ == '__main__':
    init_db() 
