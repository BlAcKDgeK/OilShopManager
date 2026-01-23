class Product:
    def __init__(self, id, name, description, price, image_path=None, category="Масло"):
        self.id = id
        self.name = name
        self.description = description
        self.price = price
        self.image_path = image_path
        self.category = category


class User:
    def __init__(self, id, name, email, address):
        self.id = id
        self.name = name
        self.email = email
        self.address = address


class Order:
    def __init__(self, id, user_id, product_id, quantity, order_date, status="Обработан"):
        self.id = id
        self.user_id = user_id
        self.product_id = product_id
        self.quantity = quantity
        self.order_date = order_date
        self.status = status


class CartItem:
    def __init__(self, product_id, name, quantity, price, image_path=None):
        self.product_id = product_id
        self.name = name
        self.quantity = quantity
        self.price = price
        self.image_path = image_path


class Review:
    def __init__(self, id, product_id, user_name, rating, comment, date):
        self.id = id
        self.product_id = product_id
        self.user_name = user_name
        self.rating = rating
        self.comment = comment
        self.date = date
