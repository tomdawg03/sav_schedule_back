from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

db = SQLAlchemy()
db.init_app(app)

with app.app_context():
    from models.user import User  # Import here to avoid circular import
    db.create_all()
    print("Database initialized successfully!") 