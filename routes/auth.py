from flask import Blueprint, request, jsonify
<<<<<<< HEAD
from flask_login import login_user, logout_user, login_required, current_user
from models.user import User, Role, ROLES
from models import db
import jwt
from datetime import datetime, timedelta
from functools import wraps

auth = Blueprint('auth', __name__)

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split(" ")[1]
        
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        
        try:
            data = jwt.decode(token, 'your-secret-key', algorithms=["HS256"])
            current_user = User.query.get(data['user_id'])
        except:
            return jsonify({'error': 'Token is invalid'}), 401
            
        return f(current_user, *args, **kwargs)
    
    return decorated

@auth.route('/create-admin', methods=['POST'])
def create_admin():
    # Check if any users exist
    if User.query.first():
        return jsonify({'error': 'Admin user already exists'}), 400
        
    data = request.get_json()
    
    # Validate required fields
    if not all(k in data for k in ['username', 'email', 'password']):
        return jsonify({'error': 'Missing required fields'}), 400

    # Create admin role if it doesn't exist
    admin_role = Role.query.filter_by(name='admin').first()
    if not admin_role:
        admin_role = Role(
            name='admin',
            description=ROLES['admin']['description'],
            permissions=ROLES['admin']['permissions']
        )
        db.session.add(admin_role)
        db.session.flush()

    # Create new admin user
    user = User(
        username=data['username'],
        email=data['email'],
        role=admin_role
    )
    user.set_password(data['password'])

    db.session.add(user)
    db.session.commit()

    return jsonify({'message': 'Admin user created successfully'}), 201

=======
from flask_login import login_user, logout_user, login_required
from models.user import User, db

auth = Blueprint('auth', __name__)

>>>>>>> 9e888cc9d22dfe916ed96e30e883c8cbf60cef19
@auth.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    
    # Validate required fields
    if not all(k in data for k in ['username', 'email', 'password']):
        return jsonify({'error': 'Missing required fields'}), 400

    # Check if user already exists
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Username already exists'}), 400
    
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already exists'}), 400

    # Create new user
    user = User(
        username=data['username'],
        email=data['email']
    )
    user.set_password(data['password'])

    db.session.add(user)
    db.session.commit()

    return jsonify({'message': 'User created successfully'}), 201

@auth.route('/login', methods=['POST'])
def login():
<<<<<<< HEAD
    # Handle both JSON and form data
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form

    print(f"Login attempt with data: {data}")
=======
    data = request.get_json()
>>>>>>> 9e888cc9d22dfe916ed96e30e883c8cbf60cef19
    
    if not all(k in data for k in ['username', 'password']):
        return jsonify({'error': 'Missing username or password'}), 400

    user = User.query.filter_by(username=data['username']).first()

    if user and user.check_password(data['password']):
        login_user(user)
<<<<<<< HEAD
        
        # Generate token
        token = jwt.encode({
            'user_id': user.id,
            'exp': datetime.utcnow() + timedelta(days=1)
        }, 'your-secret-key', algorithm="HS256")
        
=======
>>>>>>> 9e888cc9d22dfe916ed96e30e883c8cbf60cef19
        return jsonify({
            'success': True,
            'user': {
                'id': user.id,
                'username': user.username,
<<<<<<< HEAD
                'email': user.email,
                'role': user.role.name if user.role else None,
                'permissions': user.role.permissions if user.role else 0,
                'token': token
=======
                'email': user.email
>>>>>>> 9e888cc9d22dfe916ed96e30e883c8cbf60cef19
            }
        }), 200
    
    return jsonify({'error': 'Invalid username or password'}), 401

@auth.route('/logout')
@login_required
def logout():
    logout_user()
<<<<<<< HEAD
    return jsonify({'message': 'Logged out successfully'})

@auth.route('/users', methods=['GET'])
def get_users():
    try:
        users = User.query.all()
        return jsonify([{
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.role.name if user.role else None
        } for user in users]), 200
    except Exception as e:
        print(f"Error fetching users: {str(e)}")
        return jsonify({'error': 'Failed to fetch users'}), 500

@auth.route('/roles', methods=['GET'])
def get_roles():
    try:
        roles = Role.query.all()
        return jsonify([{
            'id': role.id,
            'name': role.name,
            'description': role.description
        } for role in roles]), 200
    except Exception as e:
        print(f"Error fetching roles: {str(e)}")
        return jsonify({'error': 'Failed to fetch roles'}), 500

@auth.route('/users/<int:user_id>/role', methods=['PUT'])
@login_required
def update_user_role(user_id):
    try:
        data = request.get_json()
        if not data or 'role' not in data:
            return jsonify({'error': 'Role is required'}), 400

        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        role = Role.query.filter_by(name=data['role']).first()
        if not role:
            return jsonify({'error': 'Invalid role'}), 400

        user.role = role
        db.session.commit()

        return jsonify({
            'message': 'User role updated successfully',
            'user': {
                'id': user.id,
                'username': user.username,
                'role': user.role.name
            }
        }), 200
    except Exception as e:
        print(f"Error updating user role: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Failed to update user role'}), 500 
=======
    return jsonify({'message': 'Logged out successfully'}) 
>>>>>>> 9e888cc9d22dfe916ed96e30e883c8cbf60cef19
