import sqlite3

from models import Product, CartItem, Review


def connect_db():
    return sqlite3.connect('oil_shop.db')

def create_tables():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL,
            image_path TEXT,
            category TEXT DEFAULT 'Масло'
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            address TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            product_id INTEGER,
            quantity INTEGER,
            order_date TEXT,
            status TEXT DEFAULT 'Обработан',
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (product_id) REFERENCES products (id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cart (
            id INTEGER PRIMARY KEY,
            product_id INTEGER,
            user_email TEXT,
            quantity INTEGER,
            FOREIGN KEY (product_id) REFERENCES products (id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY,
            product_id INTEGER,
            user_name TEXT,
            rating INTEGER,
            comment TEXT,
            date TEXT,
            FOREIGN KEY (product_id) REFERENCES products (id)
        )
    ''')
    conn.commit()
    conn.close()

# ---------------- Работа с товарами ----------------
def has_products():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM products')
    count = cursor.fetchone()[0]
    conn.close()
    return count > 0

def add_product(name, description, price, image_path=None, category="Масло"):
    try:
        price = float(price)
        if price <= 0:
            raise ValueError("Цена должна быть положительной")
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO products (name, description, price, image_path, category) VALUES (?, ?, ?, ?, ?)',
            (name, description, price, image_path, category)
        )
        conn.commit()
        conn.close()
        return True
    except ValueError as e:
        return str(e)

def get_products(search_query="", category_filter="", min_price=0, max_price=float('inf')):
    conn = connect_db()
    cursor = conn.cursor()
    query = 'SELECT * FROM products WHERE name LIKE ? AND category LIKE ? AND price BETWEEN ? AND ?'
    cursor.execute(query, ('%' + search_query + '%', '%' + category_filter + '%', min_price, max_price))
    rows = cursor.fetchall()
    products = [Product(*row) for row in rows]
    conn.close()
    return products

def get_product_by_id(product_id):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM products WHERE id = ?', (product_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return Product(*row)
    return None

def update_product(product_id, name=None, description=None, price=None, image_path=None, category=None):
    conn = connect_db()
    cursor = conn.cursor()
    # обновляем только переданные поля
    if name is not None:
        cursor.execute('UPDATE products SET name = ? WHERE id = ?', (name, product_id))
    if description is not None:
        cursor.execute('UPDATE products SET description = ? WHERE id = ?', (description, product_id))
    if price is not None:
        cursor.execute('UPDATE products SET price = ? WHERE id = ?', (price, product_id))
    if image_path is not None:
        cursor.execute('UPDATE products SET image_path = ? WHERE id = ?', (image_path, product_id))
    if category is not None:
        cursor.execute('UPDATE products SET category = ? WHERE id = ?', (category, product_id))
    conn.commit()
    conn.close()

def delete_product(product_id):
    try:
        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute('DELETE FROM cart WHERE product_id = ?', (product_id,))
        cursor.execute('DELETE FROM orders WHERE product_id = ?', (product_id,))
        cursor.execute('DELETE FROM products WHERE id = ?', (product_id,))

        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print("Ошибка удаления товара:", e)
        return False

# ---------------------------------------------------

# ---------------- Работа с корзиной ----------------
def add_to_cart(product_id, user_email, quantity=1):
    if not user_email:
        print("Ошибка: пользователь не авторизован")
        return False
    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute('SELECT quantity FROM cart WHERE product_id = ? AND user_email = ?', (product_id, user_email))
        existing = cursor.fetchone()
        if existing:
            new_quantity = existing[0] + quantity
            cursor.execute(
                'UPDATE cart SET quantity = ? WHERE product_id = ? AND user_email = ?',
                (new_quantity, product_id, user_email)
            )
        else:
            cursor.execute(
                'INSERT INTO cart (product_id, quantity, user_email) VALUES (?, ?, ?)',
                (product_id, quantity, user_email)
            )
        conn.commit()
        conn.close()
        print(f"Добавлено в корзину: product_id={product_id}, user={user_email}")
        return True
    except Exception as e:
        print("Ошибка добавления в корзину:", e)
        return False


def get_cart(user_email):
    if not user_email:
        return []
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT c.product_id, p.name, c.quantity, p.price, p.image_path
        FROM cart c 
        JOIN products p ON c.product_id = p.id
        WHERE c.user_email = ?
    ''', (user_email,))
    rows = cursor.fetchall()
    cart_items = [CartItem(*row) for row in rows]
    conn.close()
    return cart_items


def clear_cart(user_email):
    if not user_email:
        return
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM cart WHERE user_email = ?', (user_email,))
    conn.commit()
    conn.close()


# ---------------- Работа с заказами ----------------
def create_order(user_email, cart_items):
    if not user_email or not cart_items:
        print("Ошибка: нет пользователя или корзины")
        return False
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM users WHERE email = ?', (user_email,))
    user = cursor.fetchone()
    if not user:
        raise ValueError("Пользователь не найден")
    user_id = user[0]
    for item in cart_items:
        cursor.execute(
            'INSERT INTO orders (user_id, product_id, quantity, order_date) VALUES (?, ?, ?, datetime("now"))',
            (user_id, item.product_id, item.quantity)
        )
    conn.commit()
    conn.close()
    clear_cart(user_email)  # передаем email
    return True


def get_orders(user_email=None):
    conn = connect_db()
    cursor = conn.cursor()
    if user_email:
        cursor.execute('''
            SELECT o.id, p.name, o.quantity, o.order_date, o.status
            FROM orders o
            JOIN products p ON o.product_id = p.id
            JOIN users u ON o.user_id = u.id
            WHERE u.email = ?
            ORDER BY o.order_date DESC
        ''', (user_email,))
    else:
        cursor.execute('''
            SELECT o.id, u.name, p.name, o.quantity, o.order_date, o.status
            FROM orders o
            JOIN users u ON o.user_id = u.id
            JOIN products p ON o.product_id = p.id
            ORDER BY o.order_date DESC
        ''')
    rows = cursor.fetchall()
    conn.close()
    return rows
# ---------------------------------------------------

# ---------------- Работа с отзывами ----------------
def add_review(product_id, user_name, rating, comment):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO reviews (product_id, user_name, rating, comment, date) VALUES (?, ?, ?, ?, datetime("now"))',
        (product_id, user_name, rating, comment)
    )
    conn.commit()
    conn.close()

def get_reviews(product_id):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM reviews WHERE product_id = ? ORDER BY date DESC', (product_id,))
    rows = cursor.fetchall()
    reviews = [Review(*row) for row in rows]
    conn.close()
    return reviews
# ---------------------------------------------------

def init_data():
    create_tables()
    if not has_products():
        add_product("Оливковое масло, 250 мл", "Экстра вирджин из Греции", 500.0, "Оливковое масло.jpg", "Оливковое")
        add_product("Подсолнечное масло, 500 мл", "Холодный отжим", 300.0, "Подсолнечное масло.jpg", "Подсолнечное")
        add_product("Льняное масло, 250 мл", "Холодный отжим", 600.0, "Льняное масло.jpg", "Льняное")

def update_cart_quantity(product_id, user_email, quantity):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE cart SET quantity = ? WHERE product_id = ? AND user_email = ?",
        (quantity, product_id, user_email)
    )
    conn.commit()
    conn.close()

def remove_from_cart(product_id, user_email):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM cart WHERE product_id = ? AND user_email = ?",
        (product_id, user_email)
    )
    conn.commit()
    conn.close()

