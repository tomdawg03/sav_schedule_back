from . import db

class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))  # Full name
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    phone = db.Column(db.String(20), nullable=False)  # Keep phone as required for uniqueness
    email = db.Column(db.String(120))
    projects = db.relationship('Project', backref='customer', lazy=True)

    def __repr__(self):
        return f'<Customer {self.name or f"{self.first_name} {self.last_name}"}'