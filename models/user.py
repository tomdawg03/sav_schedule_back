from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from . import db
import uuid

class Invitation(db.Model):
    __tablename__ = 'invitations'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(36), unique=True, nullable=False)
    email = db.Column(db.String(120), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False)
    used_at = db.Column(db.DateTime)
    
    # Relationship with Role
    role = db.relationship('Role', backref=db.backref('invitations', lazy=True))
    
    def __init__(self, email, role, expires_in_days=7):
        self.code = str(uuid.uuid4())
        self.email = email
        self.role = role
        self.expires_at = db.func.current_timestamp() + db.func.interval(expires_in_days, 'day')
    
    def is_valid(self):
        return not self.used and self.expires_at > db.func.current_timestamp()

class Role(db.Model):
    __tablename__ = 'roles'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.String(200))
    permissions = db.Column(db.Integer)  # Store permissions as a bitmask
    users = db.relationship('User', back_populates='role')
    
    def __repr__(self):
        return f'<Role {self.name}>'

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationship with Role
    role = db.relationship('Role', back_populates='users')

    def __init__(self, username, email, role=None):
        self.username = username
        self.email = email
        if role:
            self.role = role
        else:
            # Default to viewer role if none specified
            self.role = Role.query.filter_by(name='viewer').first()

    def set_password(self, password):
        print(f"Setting password for user: {self.username}")
        self.password_hash = generate_password_hash(password)
        print(f"Password hash generated: {self.password_hash[:20]}...")

    def check_password(self, password):
        print(f"Checking password for user: {self.username}")
        print(f"Stored hash: {self.password_hash[:20]}...")
        result = check_password_hash(self.password_hash, password)
        print(f"Password check result: {result}")
        return result

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
        'permissions': sum(PERMISSIONS.values()),
        'display_name': 'Admin'
    },
    'project_manager': {
        'name': 'project_manager',
        'description': 'Can create and manage projects',
        'permissions': PERMISSIONS['VIEW_CALENDAR'] | 
                     PERMISSIONS['CREATE_PROJECT'] | 
                     PERMISSIONS['EDIT_PROJECT'] | 
                     PERMISSIONS['DELETE_PROJECT'],
        'display_name': 'Project Manager'
    },
    'viewer': {
        'name': 'viewer',
        'description': 'Can only view the calendar',
        'permissions': PERMISSIONS['VIEW_CALENDAR'],
        'display_name': 'Viewer'
    }
}
