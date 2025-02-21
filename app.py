from flask import Flask, request, jsonify
from flask_login import LoginManager
from flask_cors import CORS
from config import Config
from models.user import db, User
from routes.auth import auth
import json
from datetime import datetime

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize extensions
    CORS(app)  # Enable CORS for all routes
    db.init_app(app)
    
    login_manager = LoginManager()
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register blueprints
    app.register_blueprint(auth, url_prefix='/api/auth')

    # Create database tables
    with app.app_context():
        db.create_all()

    # This is temporary storage - you'd typically use a database
    users = {}
    projects = {
        'northern': [],
        'southern': []
    }

    @app.route('/signup', methods=['POST'])
    def signup():
        data = request.json
        username = data.get('username')
        password = data.get('password')
        
        if username in users:
            return jsonify({'error': 'Username already exists'}), 400
        
        users[username] = password
        return jsonify({'message': 'User created successfully'}), 200

    @app.route('/login', methods=['POST'])
    def login():
        data = request.json
        username = data.get('username')
        password = data.get('password')
        
        if username in users and users[username] == password:
            return jsonify({'username': username}), 200
        
        return jsonify({'error': 'Invalid credentials'}), 401

    @app.route('/projects/<region>', methods=['GET'])
    def get_projects(region):
        print(f"GET request received for {region} projects")  # Debug print
        region_projects = projects.get(region, [])
        print(f"Returning projects: {region_projects}")  # Debug print
        return jsonify(region_projects)

    @app.route('/projects/<region>', methods=['POST'])
    def add_project(region):
        project = request.json
        print(f"Adding project to {region}: {project}")  # Debug print
        
        if region not in projects:
            projects[region] = []
        
        projects[region].append(project)
        print(f"Updated projects for {region}: {projects[region]}")  # Debug print
        
        return jsonify({'message': 'Project added successfully'}), 200

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(port=5001, debug=True)