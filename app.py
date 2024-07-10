from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from celery import Celery
from models import db, Product, ProcessingStatus
import pandas as pd
import requests
from io import BytesIO
from PIL import Image
import os
import uuid

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://username:password@localhost/image_processing'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'

db.init_app(app)
celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

# Celery Task
@celery.task(bind=True)
def process_images(self, product_id, input_image_urls):
    try:
        processed_urls = []
        for idx, url in enumerate(input_image_urls.split(',')):
            response = requests.get(url.strip())
            img = Image.open(BytesIO(response.content))
            # Process image (e.g., resize, compress)
            img.save(f'processed_{idx}_{product_id}.jpg', optimize=True, quality=50)
            processed_urls.append(f'http://yourserver/processed_{idx}_{product_id}.jpg')

        product = Product.query.get(product_id)
        product.output_image_urls = ','.join(processed_urls)
        db.session.commit()

        return 'Processed images successfully'
    except Exception as e:
        return f'Error processing images: {str(e)}'

# API endpoints
@app.route('/upload', methods=['POST'])
def upload_csv():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file part in the request'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
        
        if file:
            df = pd.read_csv(file)
            for index, row in df.iterrows():
                product_name = row['Product Name']
                input_image_urls = row['Input Image Urls']
                
                # Save product and initiate image processing task
                product = Product(product_name=product_name, input_image_urls=input_image_urls)
                db.session.add(product)
                db.session.commit()

                # Start image processing task asynchronously
                process_images.apply_async(args=[product.id, input_image_urls])

            return jsonify({'message': 'File uploaded successfully'}), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/status/<request_id>', methods=['GET'])
def check_status(request_id):
    try:
        status = ProcessingStatus.query.filter_by(request_id=request_id).first()
        if not status:
            return jsonify({'message': 'Invalid request ID'}), 404
        
        return jsonify({'status': status.status}), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
