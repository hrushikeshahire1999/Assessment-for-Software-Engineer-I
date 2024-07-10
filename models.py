from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(255), nullable=False)
    input_image_urls = db.Column(db.Text, nullable=False)
    output_image_urls = db.Column(db.Text)

class ProcessingStatus(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(50), nullable=False)