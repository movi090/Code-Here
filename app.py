from flask import Flask, render_template, request, redirect, url_for, jsonify
from PIL import Image
from pyzbar import pyzbar
from flask_sqlalchemy import SQLAlchemy
import random
import string

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///products.db'
db = SQLAlchemy(app)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    barcode = db.Column(db.String(20), unique=True, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    type_id = db.Column(db.Integer, db.ForeignKey('type.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    perishable = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f"Product(barcode={self.barcode}, name={self.name}, perishable={self.perishable})"

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)

class Type(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        return redirect(url_for('process_barcode'))

    return render_template('index.html')

@app.route('/process_barcode', methods=['POST'])
def process_barcode():
    barcode = request.files['barcode']
    length = float(request.form['length'])
    width = float(request.form['width'])
    height = float(request.form['height'])

    barcode_data = decode_barcode(barcode)

    if barcode_data is None:
        return render_template('result.html', type_name="Штрих-код не распознан", perishable=False, placement="")

    type_id = barcode_data[1]

    product = Product.query.filter_by(type_id=type_id).first()

    if product:
        type_name = product.name
        perishable = product.perishable
    else:
        type_name = "Неопределенный тип"
        perishable = False

    if length <= 50 and width <= 50 and height <= 50:
        placement = "Полка"
    elif length <= 100 and width <= 100 and height <= 100:
        placement = "Палета"
    else:
        placement = "Пол"

    return render_template('result.html', type_name=type_name, perishable=perishable, placement=placement)

def decode_barcode(barcode):
    img = Image.open(barcode)
    decoded_barcodes = pyzbar.decode(img)

    if decoded_barcodes:
        barcode_data = decoded_barcodes[0].data.decode("utf-8")
        return barcode_data

    return None

@app.route('/add_product', methods=['GET', 'POST'])
def add_product():
    if request.method == 'POST':
        category_id = int(request.form['category'])
        type_id = int(request.form['type'])
        name = request.form['name']
        perishable = bool(request.form.get('perishable'))

        product = Product(category_id=category_id, type_id=type_id, name=name, perishable=perishable)
        db.session.add(product)
        db.session.commit()

        return redirect(url_for('index'))

    categories = Category.query.all()
    types = Type.query.all()
    return render_template('add_product.html', categories=categories, types=types)

@app.route('/add_category', methods=['POST'])
def add_category():
    name = request.form.get('name')

    if not name:
        return jsonify({'success': False, 'error': 'Name is required'})

    category = Category(name=name)
    db.session.add(category)
    db.session.commit()

    return jsonify({'success': True, 'category': {'id': category.id, 'name': category.name}})

@app.route('/add_type', methods=['POST'])
def add_type():
    name = request.form.get('name')

    product_type = Type(name=name)
    db.session.add(product_type)
    db.session.commit()

    return jsonify({'success': True, 'type': {'id': product_type.id, 'name': product_type.name}})


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
