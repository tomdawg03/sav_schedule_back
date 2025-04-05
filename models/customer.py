from . import db

class Customer(db.Model):
    __tablename__ = 'customer'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))  # Full name
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    phone = db.Column(db.String(20), nullable=False)  # Keep phone as required for uniqueness
    email = db.Column(db.String(120))
    # Define one-to-many relationship with Project
    projects = db.relationship('Project', back_populates='customer', lazy=True)

    def __repr__(self):
        return f'<Customer {self.name or f"{self.first_name} {self.last_name}"}'