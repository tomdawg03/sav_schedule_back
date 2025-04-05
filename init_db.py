from flask import Flask
from models import db
from models.user import User, Role
from models.customer import Customer
from models.project import Project

def init_db():
    """Initialize the database with required data."""
    # Create Flask app and configure it
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///scheduler.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize the database with the app
    db.init_app(app)
    
    # Create an application context
    with app.app_context():
        print("\nInitializing database...")
        
        # Create tables if they don't exist
        db.create_all()
        print("Tables created")

        # Create roles if they don't exist
        admin_role = Role.query.filter_by(name='admin').first()
        if not admin_role:
            print("Creating admin role...")
            admin_role = Role(name='admin', permissions=0xFFFFFFFF)  # All permissions
            db.session.add(admin_role)
            db.session.commit()
            print("Admin role created")
        else:
            print("Admin role already exists")

        user_role = Role.query.filter_by(name='user').first()
        if not user_role:
            print("Creating user role...")
            user_role = Role(name='user', permissions=0x0000FFFF)  # Basic permissions
            db.session.add(user_role)
            db.session.commit()
            print("User role created")
        else:
            print("User role already exists")

        # Create admin user if it doesn't exist
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            print("Creating admin user...")
            admin_user = User(
                username='admin',
                email='admin@example.com',
                role=admin_role
            )
            admin_user.set_password('Coolio03!')
            db.session.add(admin_user)
            db.session.commit()
            print("Admin user created with password: Coolio03!")
        else:
            print("Admin user already exists")
            # Update admin password
            admin_user.set_password('Coolio03!')
            db.session.commit()
            print("Admin password updated")

        print("Database initialization complete!\n")

if __name__ == '__main__':
    init_db() 
