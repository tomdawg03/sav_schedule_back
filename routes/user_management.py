from flask import Blueprint, request, jsonify, render_template, redirect, url_for
from flask_login import current_user
from models.user import User, Role, ROLES, PERMISSIONS
from models import db
from routes.auth import token_required

user_management = Blueprint('user_management', __name__)

def admin_required(f):
    @token_required
    def decorated_function(current_user, *args, **kwargs):
        if not current_user.is_admin():
            return jsonify({'error': 'Admin privileges required'}), 403
        return f(current_user, *args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@user_management.route('/', methods=['GET'])
@token_required
def user_management_page(current_user):
    if not current_user.is_admin():
        return jsonify({'error': 'Admin privileges required'}), 403
    return render_template('user_management.html')

@user_management.route('/users', methods=['GET'], endpoint='list_users')
@token_required
def get_users(current_user):
    if not current_user.is_admin():
        return jsonify({'error': 'Admin privileges required'}), 403
        
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

@user_management.route('/user/<int:user_id>/role', methods=['PUT'], endpoint='update_role')
@admin_required
def update_user_role(current_user, user_id):
    print(f"PUT /user/{user_id}/role endpoint called")
    print(f"Current user: {current_user}")
    
    data = request.get_json()
    if not data or 'role' not in data:
        return jsonify({'error': 'Role must be specified'}), 400
        
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
            
        role = Role.query.filter_by(name=data['role']).first()
        if not role:
            return jsonify({'error': 'Invalid role'}), 400
            
        user.role = role
        db.session.commit()
        return jsonify({'message': 'User role updated successfully'})
    except Exception as e:
        print(f"Error in update_user_role: {str(e)}")
        return jsonify({'error': str(e)}), 500

@user_management.route('/user/<int:user_id>/status', methods=['PUT'], endpoint='update_status')
@admin_required
def update_user_status(current_user, user_id):
    print(f"PUT /user/{user_id}/status endpoint called")
    print(f"Current user: {current_user}")
    
    data = request.get_json()
    if not data or 'is_active' not in data:
        return jsonify({'error': 'Active status must be specified'}), 400
        
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
            
        user.is_active = data['is_active']
        db.session.commit()
        return jsonify({'message': 'User status updated successfully'})
    except Exception as e:
        print(f"Error in update_user_status: {str(e)}")
        return jsonify({'error': str(e)}), 500

@user_management.route('/roles', methods=['GET'], endpoint='list_roles')
@admin_required
def get_roles(current_user):
    print("GET /roles endpoint called")
    print(f"Current user: {current_user}")
    print(f"Is authenticated: {current_user.is_authenticated}")
    
    try:
        roles = Role.query.all()
        print(f"Found {len(roles)} roles")
        role_list = [{
            'name': role.name,
            'description': role.description,
            'permissions': role.permissions,
            'display_name': ROLES[role.name]['display_name'] if role.name in ROLES else role.name.title()
        } for role in roles]
        print(f"Returning role list: {role_list}")
        return jsonify(role_list)
    except Exception as e:
        print(f"Error in get_roles: {str(e)}")
        return jsonify({'error': str(e)}), 500

@user_management.route('/user/<int:user_id>', methods=['DELETE'], endpoint='delete_user')
@admin_required
def delete_user(current_user, user_id):
    print(f"DELETE /user/{user_id} endpoint called")
    print(f"Current user: {current_user}")
    
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
            
        # Prevent admin from deleting themselves
        if user.id == current_user.id:
            return jsonify({'error': 'Cannot delete your own account'}), 400
            
        db.session.delete(user)
        db.session.commit()
        return jsonify({'message': 'User deleted successfully'})
    except Exception as e:
        print(f"Error in delete_user: {str(e)}")
        return jsonify({'error': str(e)}), 500 