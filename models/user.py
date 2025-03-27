from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from . import db

<<<<<<< HEAD
class Role(db.Model):
    __tablename__ = 'roles'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.String(200))
    permissions = db.Column(db.Integer)  # Store permissions as a bitmask
    
    def __repr__(self):
        return f'<Role {self.name}>'

=======
>>>>>>> 9e888cc9d22dfe916ed96e30e883c8cbf60cef19
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
<<<<<<< HEAD
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationship with Role
    role = db.relationship('Role', backref=db.backref('users', lazy=True))

    def __init__(self, username, email, role=None):
        self.username = username
        self.email = email
        if role:
            self.role = role
        else:
            # Default to viewer role if none specified
            self.role = Role.query.filter_by(name='viewer').first()
=======

    def __init__(self, username, email):
        self.username = username
        self.email = email
>>>>>>> 9e888cc9d22dfe916ed96e30e883c8cbf60cef19

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

<<<<<<< HEAD
    def has_permission(self, permission):
        if not self.role:
            return False
        return bool(self.role.permissions & permission)

    def is_admin(self):
        return self.role and self.role.name == 'admin'

    def __repr__(self):
        return f'<User {self.username}>'

# Permission constants
PERMISSIONS = {
    'VIEW_CALENDAR': 1,
    'CREATE_PROJECT': 2,
    'EDIT_PROJECT': 4,
    'DELETE_PROJECT': 8,
    'MANAGE_USERS': 16
}

# Role definitions
ROLES = {
    'admin': {
        'name': 'admin',
        'description': 'Administrator with all permissions',
        'permissions': sum(PERMISSIONS.values())
    },
    'project_manager': {
        'name': 'project_manager',
        'description': 'Can create and manage projects',
        'permissions': PERMISSIONS['VIEW_CALENDAR'] | 
                     PERMISSIONS['CREATE_PROJECT'] | 
                     PERMISSIONS['EDIT_PROJECT'] | 
                     PERMISSIONS['DELETE_PROJECT']
    },
    'viewer': {
        'name': 'viewer',
        'description': 'Can only view the calendar',
        'permissions': PERMISSIONS['VIEW_CALENDAR']
    }
} 
=======
    def __repr__(self):
        return f'<User {self.username}>' 
>>>>>>> 9e888cc9d22dfe916ed96e30e883c8cbf60cef19
