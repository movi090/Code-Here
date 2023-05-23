from flask import Flask, render_template, request, redirect, url_for, jsonify
from PIL import Image
from pyzbar import pyzbar
import random
import string
import sqlite3
import flask

app = Flask(__name__)
DATABASE = 'instance/products.db'

# Создание таблицы categories
def create_categories_table():
    with sqlite3.connect(DATABASE) as db:
        cursor = db.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL
        )''')
        db.commit()

# Создание таблицы types
def create_types_table():
    with sqlite3.connect(DATABASE) as db:
        cursor = db.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS types (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL
        )''')
        db.commit()

# Создание таблицы products
def create_products_table():
    with sqlite3.connect(DATABASE) as db:
        cursor = db.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER NOT NULL,
            type_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            perishable INTEGER DEFAULT 0,
            FOREIGN KEY (category_id) REFERENCES categories (id),
            FOREIGN KEY (type_id) REFERENCES types (id)
        )''')
        db.commit()

# Создание всех таблиц
def create_tables():
    create_categories_table()
    create_types_table()
    create_products_table()

def get_db():
    db = getattr(flask.g, '_database', None)
    if db is None:
        db = flask.g._database = sqlite3.connect(DATABASE)
        db.execute('PRAGMA foreign_keys = ON')
        db.commit()
    return db

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

    with sqlite3.connect(DATABASE) as db:
        db.execute('PRAGMA foreign_keys = ON')
        db.commit()
        cursor = db.cursor()

        # Используйте конкретные запросы для работы с базой данных SQLite
        cursor.execute('SELECT * FROM products WHERE type_id = ?', (type_id,))
        product = cursor.fetchone()

        if product:
            type_name = product[3]
            perishable = bool(product[4])
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
    with Image.open(barcode) as img:
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

        with sqlite3.connect(DATABASE) as db:
            db.execute('PRAGMA foreign_keys = ON')
            db.commit()
            cursor = db.cursor()

            # Вставляем данные в таблицу "products"
            cursor.execute('INSERT INTO products (category_id, type_id, name, perishable) VALUES (?, ?, ?, ?)',
                           (category_id, type_id, name, perishable))
            db.commit()

        return redirect(url_for('index'))

    with sqlite3.connect(DATABASE) as db:
        db.execute('PRAGMA foreign_keys = ON')
        db.commit()
        cursor = db.cursor()

        # Получаем список категорий и типов из базы данных
        cursor.execute('SELECT id, name FROM categories')
        categories = cursor.fetchall()

        cursor.execute('SELECT id, name FROM types')
        types = cursor.fetchall()

    return render_template('add_product.html', categories=categories, types=types)

@app.route('/add_category', methods=['POST'])
def add_category():
    name = request.form.get('name')

    if not name:
        return jsonify({'success': False, 'error': 'Name is required'})

    with sqlite3.connect(DATABASE) as db:
        db.execute('PRAGMA foreign_keys = ON')
        db.commit()
        cursor = db.cursor()

        # Вставляем данные в таблицу "categories"
        db.execute('INSERT INTO categories (name) VALUES (?)', (name,))
        db.commit()

        category_id = cursor.lastrowid

    return jsonify({'success': True, 'category': {'id': category_id, 'name': name}})

@app.route('/add_type', methods=['POST'])
def add_type():
    name = request.form.get('name')

    with sqlite3.connect(DATABASE) as db:
        db.execute('PRAGMA foreign_keys = ON')
        db.commit()
        cursor = db.cursor()

        # Вставляем данные в таблицу "types"
        cursor.execute('INSERT INTO types (name) VALUES (?)', (name,))
        db.commit()

        type_id = cursor.lastrowid

    return jsonify({'success': True, 'type': {'id': type_id, 'name': name}})

if __name__ == '__main__':
    create_tables()
    app.run(debug=True)
