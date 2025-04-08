from flask import Blueprint, request, jsonify, redirect, url_for, flash, render_template
from flask_login import login_user, logout_user, login_required, current_user
from models.user import User, Role, ROLES, Invitation
from models import db
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, verify_jwt_in_request, JWTManager
import jwt
from datetime import datetime, timedelta
from functools import wraps
from services.email_service import EmailService
import os

auth = Blueprint('auth', __name__)

# List of valid signup codes - you can modify these as needed
VALID_SIGNUP_CODES = ['SAVAGE2024']  # Single code for simplicity

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            # Add debug logging
            auth_header = request.headers.get('Authorization')
            print(f"Auth header received: {auth_header}")
            
            verify_jwt_in_request()
            user_id = get_jwt_identity()
            print(f"JWT identity: {user_id}")
            
            # Convert string ID back to integer
            user_id = int(user_id)
            current_user = User.query.get(user_id)
            
            if not current_user:
                print(f"No user found for id: {user_id}")
                return jsonify({'error': 'User not found'}), 401
                
            print(f"User found: {current_user.username}")
            return f(current_user, *args, **kwargs)
        except Exception as e:
            print(f"Token validation error: {str(e)}")
            return jsonify({'error': 'Token is invalid'}), 401
            
    return decorated

def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        user_id = get_jwt_identity()
        current_user = User.query.get(user_id)
        
        if not current_user or not current_user.is_admin():
            return jsonify({'error': 'Admin privileges required'}), 403
            
        return fn(*args, **kwargs)
    return wrapper

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

@auth.route('/invite', methods=['POST'])
@admin_required
def create_invitation(current_user):
    data = request.get_json()
    
    if not all(k in data for k in ['email', 'role']):
        return jsonify({'error': 'Missing required fields'}), 400
        
    if data['role'] not in ROLES:
        return jsonify({'error': 'Invalid role'}), 400
        
    # Check if user already exists
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'User with this email already exists'}), 400
        
    # Get or create role
    role = Role.query.filter_by(name=data['role']).first()
    if not role:
        role = Role(
            name=data['role'],
            description=ROLES[data['role']]['description'],
            permissions=ROLES[data['role']]['permissions']
        )
        db.session.add(role)
        db.session.flush()
    
    # Create invitation
    invitation = Invitation(
        email=data['email'],
        role=role,
        expires_in_days=data.get('expires_in_days', 7)
    )
    db.session.add(invitation)
    db.session.commit()
    
    # Generate invitation link
    invite_link = f"{request.host_url}signup?code={invitation.code}"
    
    # Send invitation email
    email_service = EmailService()
    try:
        email_service.send_invitation(
            email=data['email'],
            invite_link=invite_link,
            expires_in_days=invitation.expires_at - datetime.utcnow()
        )
    except Exception as e:
        print(f"Error sending invitation email: {str(e)}")
        # Don't return error here, just log it
    
    return jsonify({
        'message': 'Invitation sent successfully',
        'invitation': {
            'code': invitation.code,
            'email': invitation.email,
            'role': role.name,
            'expires_at': invitation.expires_at.isoformat()
        }
    })

@auth.route('/signup', methods=['POST'])
def signup():
    try:
        data = request.get_json()
        
        # Check if all required fields are present
        required_fields = ['username', 'password', 'email', 'signup_code']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400
            
        # Validate signup code
        if data['signup_code'] not in VALID_SIGNUP_CODES:
            return jsonify({'error': 'Invalid signup code'}), 400
            
        username = data['username']
        password = data['password']
        email = data['email']
        
        # Check if username already exists
        if User.query.filter_by(username=username).first():
            return jsonify({'error': 'Username already exists'}), 400
            
        # Check if email already exists
        if User.query.filter_by(email=email).first():
            return jsonify({'error': 'Email already exists'}), 400
            
        # Get or create viewer role
        viewer_role = Role.query.filter_by(name='viewer').first()
        if not viewer_role:
            viewer_role = Role(
                name='viewer',
                description=ROLES['viewer']['description'],
                permissions=ROLES['viewer']['permissions']
            )
            db.session.add(viewer_role)
            db.session.flush()
            
        # Create new user with viewer role
        new_user = User(
            username=username,
            email=email,
            role=viewer_role  # Set role to viewer
        )
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()
        
        return jsonify({'message': 'User created successfully'}), 201
        
    except Exception as e:
        print(f"Error in signup: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    # Get form data
    username = request.form.get('username')
    password = request.form.get('password')

    print(f"Login attempt for username: {username}")
    
    if not username or not password:
        return jsonify({'error': 'Missing username or password'}), 400

    user = User.query.filter_by(username=username).first()
    
    if user and user.check_password(password):
        login_user(user)
        # Create JWT token with string identity
        token = create_access_token(identity=str(user.id))
        print(f"Created token for user {user.username} with ID {user.id}")
        return jsonify({
            'message': 'Login successful',
            'token': token,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role.name if user.role else None
            }
        })
    
    return jsonify({'error': 'Invalid username or password'}), 401

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return jsonify({'message': 'Logged out successfully'})

@auth.route('/users', methods=['GET'])
@token_required
def get_users(current_user):
    try:
        if not current_user.is_admin():
            return jsonify({'error': 'Admin privileges required'}), 403
            
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

@auth.route('/validate', methods=['GET'])
@token_required
def validate_token(current_user):
    try:
        print(f"Validating token for user: {current_user.username}")
        return jsonify({
            'valid': True,
            'user': {
                'id': current_user.id,
                'username': current_user.username,
                'email': current_user.email,
                'role': current_user.role.name if current_user.role else None
            }
        })
    except Exception as e:
        print(f"Error in validate_token: {str(e)}")
        return jsonify({'error': str(e)}), 500

@auth.route('/user/<int:user_id>', methods=['PUT'])
@token_required
def update_user(current_user, user_id):
    try:
        if not current_user.is_admin():
            return jsonify({'error': 'Admin privileges required'}), 403
            
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
            
        # Check if username is being changed and is not taken
        if 'username' in data and data['username'] != user.username:
            if User.query.filter_by(username=data['username']).first():
                return jsonify({'error': 'Username already exists'}), 400
            user.username = data['username']
            
        # Check if email is being changed and is not taken
        if 'email' in data and data['email'] != user.email:
            if User.query.filter_by(email=data['email']).first():
                return jsonify({'error': 'Email already exists'}), 400
            user.email = data['email']
            
        # Update password if provided
        if 'password' in data:
            user.set_password(data['password'])
            
        db.session.commit()
        
        return jsonify({
            'message': 'User updated successfully',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role.name if user.role else None
            }
        }), 200
    except Exception as e:
        print(f"Error updating user: {str(e)}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
