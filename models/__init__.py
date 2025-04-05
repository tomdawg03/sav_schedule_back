from flask_sqlalchemy import SQLAlchemy
import os

db = SQLAlchemy()

def init_app(app):
    # Initialize the database
    db.init_app(app)
    
    # Create all tables
    with app.app_context():
        db.create_all()