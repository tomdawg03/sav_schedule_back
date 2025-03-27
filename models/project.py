from . import db
from datetime import datetime

class Project(db.Model):
<<<<<<< HEAD
    __tablename__ = 'project'
    
=======
>>>>>>> 9e888cc9d22dfe916ed96e30e883c8cbf60cef19
    id = db.Column(db.String(36), primary_key=True)
    date = db.Column(db.Date, nullable=False)
    po = db.Column(db.String(100))
    address = db.Column(db.String(200), nullable=False)
    city = db.Column(db.String(100))
    subdivision = db.Column(db.String(100))
    lot_number = db.Column(db.String(50))
    square_footage = db.Column(db.Integer)
    job_cost_type = db.Column(db.String(100))
    work_type = db.Column(db.String(100))
    notes = db.Column(db.Text)
    region = db.Column(db.String(50), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
<<<<<<< HEAD
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now()) 
=======
    created_at = db.Column(db.DateTime, default=datetime.utcnow) 
>>>>>>> 9e888cc9d22dfe916ed96e30e883c8cbf60cef19
