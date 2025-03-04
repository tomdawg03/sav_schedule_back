from app import app, db

print("Starting database initialization...")

with app.app_context():
    print("Dropping all existing tables...")
    db.drop_all()
    print("Creating new tables...")
    db.create_all()
    print("Database initialized successfully!") 