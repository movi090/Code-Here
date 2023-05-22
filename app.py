from flask import Flask, render_template, request, redirect, url_for
from PIL import Image
from pyzbar import pyzbar
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///products.db'
db = SQLAlchemy(app)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    barcode = db.Column(db.String(20), unique=True, nullable=False)
    category_code = db.Column(db.String(4), nullable=False)
    type_code = db.Column(db.String(4), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    perishable = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f"Product(barcode={self.barcode}, name={self.name}, perishable={self.perishable})"


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(4), unique=True, nullable=False)
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
    type_code = barcode_data[1]

    product = Product.query.filter_by(type_code=type_code).first()

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

    return "Штрих-код не распознан"


@app.route('/add_product', methods=['GET', 'POST'])
def add_product():
    if request.method == 'POST':
        category_code = request.form['category']
        type_code = request.form['type']
        name = request.form['name']
        perishable = bool(request.form.get('perishable'))

        product = Product(category_code=category_code, type_code=type_code, name=name, perishable=perishable)
        db.session.add(product)
        db.session.commit()

        return redirect(url_for('index'))

    categories = Category.query.all()
    return render_template('add_product.html', categories=categories)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
