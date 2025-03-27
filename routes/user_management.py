from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from models.user import User, Role, ROLES, PERMISSIONS
from models import db

user_management = Blueprint('user_management', __name__)

def admin_required(f):
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin():
            return jsonify({'error': 'Admin privileges required'}), 403
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@user_management.route('/users', methods=['GET'], endpoint='list_users')
@admin_required
def get_users():
    print("GET /users endpoint called")
    print(f"Current user: {current_user}")
    
    try:
        users = User.query.all()
        print(f"Found {len(users)} users")
        user_list = [{
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.role.name if user.role else None,
            'is_active': user.is_active
        } for user in users]
        
        if not user_list:
            # Return an empty list instead of an error when there are no other users
            return jsonify([])
            
        print(f"Returning user list: {user_list}")
        return jsonify(user_list)
    except Exception as e:
        print(f"Error in get_users: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@user_management.route('/users/<int:user_id>/role', methods=['PUT'], endpoint='update_role')
@admin_required
def update_user_role(user_id):
    user = User.query.get_or_404(user_id)
    data = request.get_json()
    
    if 'role' not in data:
        return jsonify({'error': 'Role is required'}), 400
        
    role_name = data['role']
    if role_name not in ROLES:
        return jsonify({'error': 'Invalid role'}), 400
        
    role = Role.query.filter_by(name=role_name).first()
    if not role:
        # Create role if it doesn't exist
        role = Role(
            name=role_name,
            description=ROLES[role_name]['description'],
            permissions=ROLES[role_name]['permissions']
        )
        db.session.add(role)
        db.session.flush()
    
    user.role = role
    db.session.commit()
    
    return jsonify({
        'message': 'User role updated successfully',
        'user': {
            'id': user.id,
            'username': user.username,
            'role': role.name
        }
    })

@user_management.route('/users/<int:user_id>/status', methods=['PUT'], endpoint='update_status')
@admin_required
def update_user_status(user_id):
    user = User.query.get_or_404(user_id)
    data = request.get_json()
    
    if 'is_active' not in data:
        return jsonify({'error': 'Status is required'}), 400
        
    user.is_active = data['is_active']
    db.session.commit()
    
    return jsonify({
        'message': 'User status updated successfully',
        'user': {
            'id': user.id,
            'username': user.username,
            'is_active': user.is_active
        }
    })

@user_management.route('/roles', methods=['GET'], endpoint='list_roles')
@admin_required
def get_roles():
    print("GET /roles endpoint called")
    print(f"Current user: {current_user}")
    print(f"Is authenticated: {current_user.is_authenticated}")
    
    try:
        roles = Role.query.all()
        print(f"Found {len(roles)} roles")
        role_list = [{
            'name': role.name,
            'description': role.description,
            'permissions': role.permissions
        } for role in roles]
        print(f"Returning role list: {role_list}")
        return jsonify(role_list)
    except Exception as e:
        print(f"Error in get_roles: {str(e)}")
        return jsonify({'error': str(e)}), 500 