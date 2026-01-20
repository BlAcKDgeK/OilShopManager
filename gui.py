from PyQt5.QtWidgets import (QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
                             QTableWidgetItem, QPushButton, QLabel, QLineEdit, QMessageBox, QSplitter, QComboBox,
                             QSpinBox, QProgressBar, QTextEdit, QGroupBox, QFormLayout, QInputDialog, QScrollArea,
                             QDialog, QDialogButtonBox, QListWidget, QListWidgetItem, QFileDialog)
from PyQt5.QtGui import QPixmap, QIcon, QFont
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import os
from functools import partial
import database
from database import *


def get_product_by_id(product_id):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM products WHERE id = ?', (product_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return Product(*row)
    return None

class LoadThread(QThread):
    finished = pyqtSignal(list)
    def __init__(self, func, *args):
        super().__init__()
        self.func = func
        self.args = args
    def run(self):
        result = self.func(*self.args)
        self.finished.emit(result)

class OilShopApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.delete_btn = QPushButton("Удалить выбранный товар")
        self.current_user = None
        self.setWindowTitle("Интернет-магазин растительного масла")
        self.setGeometry(100, 100, 1400, 800)
        self.setWindowIcon(QIcon("images/icon.png"))
        self.apply_styles()
        init_data()

        self.tabs = QTabWidget()
        self.tabs.tabBar().setExpanding(True)
        self.setCentralWidget(self.tabs)

        self.catalog_tab = QWidget()
        self.tabs.addTab(self.catalog_tab, "Каталог")
        self.setup_catalog()

        self.cart_tab = QWidget()
        self.tabs.addTab(self.cart_tab, "Корзина")
        self.setup_cart()

        self.orders_tab = QWidget()
        self.tabs.addTab(self.orders_tab, "Мои заказы")
        self.setup_orders()

        self.admin_tab = QWidget()
        self.tabs.addTab(self.admin_tab, "Админ")
        self.setup_admin()

        self.login_tab = QWidget()
        self.tabs.addTab(self.login_tab, "Вход")
        self.setup_login()

    def apply_styles(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #f0f8e7; }
            QTabWidget::pane { border: 1px solid #c0c0c0; background: #ffffff; }
            QTabBar::tab { background: #e8f5e8; padding: 15px 10px; font: bold 12pt; color: #2e7d32; min-width: 120px; min-height: 35px; }
            QTabBar::tab:selected { background: #c8e6c9; }
            QPushButton { background-color: #4caf50; color: white; border-radius: 5px; padding: 8px; font: 10pt; }
            QPushButton:hover { background-color: #45a049; }
            QPushButton[small] { min-width: 70px; padding: 4px 8px; font: 9pt; }  /* Для маленьких кнопок в карточках */
            QLineEdit, QComboBox, QSpinBox { border: 1px solid #ccc; padding: 5px; border-radius: 3px; }
            QTableWidget { gridline-color: #ddd; background: #fff; }
            QLabel { font: 10pt; }
            QGroupBox { font: bold 11pt; min-width: 600px; }
            .product-card { 
                border: 1px solid #ddd; 
                border-radius: 8px; 
                padding: 10px; 
                margin: 10px; 
                background: #f9f9f9; 
                min-width: 250px; 
            }
            .product-name { font: bold 12pt; color: #2e7d32; }
            .product-price { font: bold 14pt; color: #d32f2f; }
            .product-description { font: 9pt; color: #555; min-height: 40px; }
        """)

    def show_large_image(self, image_path):
        if not image_path or not os.path.exists(f"images/{image_path}"):
            return
        dialog = QDialog(self)
        dialog.setWindowTitle("Увеличенное изображение")
        dialog.setModal(True)
        dialog.resize(500, 500)
        layout = QVBoxLayout(dialog)
        large_label = QLabel()
        pixmap = QPixmap(f"images/{image_path}").scaled(400, 400, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        large_label.setPixmap(pixmap)
        large_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(large_label)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok)
        buttons.accepted.connect(dialog.accept)
        layout.addWidget(buttons)
        dialog.exec_()

    def setup_catalog(self):
        layout = QVBoxLayout()

        # Фильтры и поиск
        filter_widget = QWidget()
        filter_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Поиск...")
        self.category_combo = QComboBox()
        self.category_combo.addItems(["Все", "Оливковое", "Подсолнечное", "Льняное"])
        self.min_price = QSpinBox()
        self.min_price.setRange(0, 10000)
        self.max_price = QSpinBox()
        self.max_price.setRange(0, 10000)
        self.max_price.setValue(10000)
        filter_button = QPushButton("Фильтровать")
        filter_button.clicked.connect(self.filter_products)
        filter_layout.addWidget(QLabel("Поиск:"))
        filter_layout.addWidget(self.search_input)
        filter_layout.addWidget(QLabel("Категория:"))
        filter_layout.addWidget(self.category_combo)
        filter_layout.addWidget(QLabel("Цена от:"))
        filter_layout.addWidget(self.min_price)
        filter_layout.addWidget(QLabel("до:"))
        filter_layout.addWidget(self.max_price)
        filter_layout.addWidget(filter_button)
        filter_widget.setLayout(filter_layout)
        layout.addWidget(filter_widget)

        # ScrollArea для карточек товаров
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self.products_container = QWidget()
        self.products_layout = QVBoxLayout(self.products_container)
        self.products_layout.addStretch()  # Для выравнивания

        self.scroll_area.setWidget(self.products_container)
        layout.addWidget(self.scroll_area)

        self.catalog_tab.setLayout(layout)
        self.load_products()

    def load_products(self, search="", category="", min_p=0, max_p=float('inf')):
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)  # Неопределённый прогресс
        self.catalog_tab.layout().insertWidget(1, self.progress)  # Вставляем после фильтров
        self.progress.show()

        def load():
            products = get_products(search, category if category != "Все" else "", min_p, max_p)
            return products

        self.thread = LoadThread(load)
        self.thread.finished.connect(self.populate_products)
        self.thread.start()

    def populate_products(self, products):
        # Очищаем предыдущие карточки
        while self.products_layout.count() > 1:  # Оставляем stretch
            child = self.products_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        for product in products:
            self.create_product_card(product)

        self.progress.hide()
        self.catalog_tab.layout().removeWidget(self.progress)
        self.progress.deleteLater()

    def create_product_card(self, product):
        card = QWidget()
        card.setObjectName("product-card")  # Для стилей
        card_layout = QVBoxLayout(card)

        # Изображение с кликом для увеличения
        image_label = QLabel()
        image_path = product.image_path
        if image_path and os.path.exists(f"images/{image_path}"):
            pixmap = QPixmap(f"images/{image_path}").scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            image_label.setPixmap(pixmap)
            image_label.setAlignment(Qt.AlignCenter)
            image_label.setCursor(Qt.PointingHandCursor)
            image_label.mousePressEvent = lambda event, path=image_path: self.show_large_image(path)
        else:
            image_label.setText("Нет фото")
            image_label.setAlignment(Qt.AlignCenter)
        image_label.setFixedHeight(100)
        card_layout.addWidget(image_label)

        # Название
        name_label = QLabel(product.name)
        name_label.setObjectName("product-name")
        name_label.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(name_label)

        # Описание
        desc_label = QLabel(product.description)
        desc_label.setObjectName("product-description")
        desc_label.setWordWrap(True)
        desc_label.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(desc_label)

        # Цена
        price_label = QLabel(f"{product.price} руб.")
        price_label.setObjectName("product-price")
        price_label.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(price_label)

        # Кнопки действий (небольшие) - центрируем
        actions_layout = QHBoxLayout()
        add_cart_btn = QPushButton("В корзину")
        add_cart_btn.setObjectName("small")  # Для стиля маленькой кнопки
        add_cart_btn.clicked.connect(lambda checked, pid=product.id: self.add_to_cart(pid))
        view_reviews_btn = QPushButton("Отзывы")
        view_reviews_btn.setObjectName("small")
        view_reviews_btn.clicked.connect(lambda checked, pid=product.id: self.show_reviews(pid))
        actions_layout.addStretch()  # Stretch слева для центрирования
        actions_layout.addWidget(add_cart_btn)
        actions_layout.addWidget(view_reviews_btn)
        actions_layout.addStretch()  # Stretch справа для центрирования
        card_layout.addLayout(actions_layout)

        self.products_layout.insertWidget(0, card)  # Добавляем в начало для правильного порядка

    def filter_products(self):
        search = self.search_input.text()
        category = self.category_combo.currentText()
        min_p = self.min_price.value()
        max_p = self.max_price.value()
        self.load_products(search, category, min_p, max_p)

    # --- Добавление в корзину ---
    def add_to_cart(self, product_id):
        if not self.current_user:
            QMessageBox.warning(self, "Ошибка", "Войдите в аккаунт!")
            return
        result = database.add_to_cart(product_id, self.current_user)
        if result:
            self.update_cart()
            QMessageBox.information(self, "Успех", "Добавлено в корзину!")
        else:
            QMessageBox.warning(self, "Ошибка", "Не удалось добавить в корзину")

    def show_reviews(self, product_id):
        reviews = get_reviews(product_id)
        text = ""
        for r in reviews:
            text += f"{r.user_name} ({r.rating}★): {r.comment} - {r.date}\n"
        if not text:
            text = "Отзывов нет."

        dialog = QDialog(self)
        dialog.setWindowTitle("Отзывы")
        layout = QVBoxLayout(dialog)

        reviews_label = QLabel(text)
        reviews_label.setWordWrap(True)
        layout.addWidget(reviews_label)

        # Добавление нового отзыва
        name_input = QLineEdit()
        name_input.setPlaceholderText("Ваше имя")
        rating_input = QSpinBox()
        rating_input.setRange(1, 5)
        comment_input = QTextEdit()
        comment_input.setPlaceholderText("Комментарий")

        layout.addWidget(QLabel("Добавить отзыв"))
        layout.addWidget(name_input)
        layout.addWidget(QLabel("Оценка (1-5)"))
        layout.addWidget(rating_input)
        layout.addWidget(comment_input)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(
            lambda: self.add_review(product_id, name_input.text(), rating_input.value(), comment_input.toPlainText(),
                                    dialog))
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        dialog.exec_()

    def add_review(self, product_id, user_name, rating, comment, dialog):
        if not user_name or not comment:
            QMessageBox.warning(self, "Ошибка", "Заполните имя и комментарий!")
            return
        add_review(product_id, user_name, rating, comment)  # реализовать в database.py
        QMessageBox.information(self, "Успех", "Отзыв добавлен!")
        dialog.accept()

    def setup_cart(self):
        layout = QVBoxLayout()
        self.empty_label = None

        # ScrollArea для карточек корзины
        self.cart_scroll = QScrollArea()
        self.cart_scroll.setWidgetResizable(True)
        self.cart_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.cart_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self.cart_container = QWidget()
        self.cart_layout = QVBoxLayout(self.cart_container)
        self.cart_layout.addStretch()  # Для выравнивания

        self.cart_scroll.setWidget(self.cart_container)
        layout.addWidget(self.cart_scroll)

        # Итоговая сумма
        self.total_label = QLabel("Итого: 0 руб.")
        self.total_label.setAlignment(Qt.AlignRight)
        self.total_label.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(self.total_label)

        # Кнопки - центрируем
        buttons_layout = QHBoxLayout()
        clear_btn = QPushButton("Очистить")
        clear_btn.clicked.connect(self.clear_cart)
        order_btn = QPushButton("Оформить заказ")
        order_btn.clicked.connect(self.order_cart)
        buttons_layout.addStretch()  # Stretch слева для центрирования
        buttons_layout.addWidget(clear_btn)
        buttons_layout.addWidget(order_btn)
        buttons_layout.addStretch()  # Stretch справа для центрирования
        layout.addLayout(buttons_layout)

        self.cart_tab.setLayout(layout)
        self.update_cart()

    # --- Обновление корзины ---
    def update_cart(self):
        if not self.current_user:
            cart_items = []
        else:
            cart_items = database.get_cart(self.current_user)

        # Очищаем предыдущие карточки и empty_label
        while self.cart_layout.count() > 1:  # оставляем stretch
            child = self.cart_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        total = 0
        if cart_items:
            for item in cart_items:
                product = get_product_by_id(item.product_id)
                if product:
                    card = self.create_cart_card(product, item)
                    self.cart_layout.insertWidget(0, card)
                    total += product.price * item.quantity
        else:
            empty_label = QLabel("Корзина пуста")
            empty_label.setAlignment(Qt.AlignCenter)
            empty_label.setStyleSheet("font: italic 12pt; color: #666; padding: 20px;")
            self.cart_layout.insertWidget(0, empty_label)

        self.total_label.setText(f"Итого: {total} руб.")

    def create_cart_card(self, product, cart_item):
        card = QWidget()
        card.setObjectName("product-card")
        card_layout = QVBoxLayout(card)

        # Изображение с кликом для увеличения
        image_label = QLabel()
        image_path = product.image_path
        if image_path and os.path.exists(f"images/{image_path}"):
            pixmap = QPixmap(f"images/{image_path}").scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            image_label.setPixmap(pixmap)
            image_label.setAlignment(Qt.AlignCenter)
            image_label.setCursor(Qt.PointingHandCursor)
            image_label.mousePressEvent = lambda event, path=image_path: self.show_large_image(path)
        else:
            image_label.setText("Нет фото")
            image_label.setAlignment(Qt.AlignCenter)
        image_label.setFixedHeight(100)
        card_layout.addWidget(image_label)

        # Название
        name_label = QLabel(product.name)
        name_label.setObjectName("product-name")
        name_label.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(name_label)

        # Описание
        desc_label = QLabel(product.description)
        desc_label.setObjectName("product-description")
        desc_label.setWordWrap(True)
        desc_label.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(desc_label)

        # Цена по центру (отдельная строка)
        price_layout = QHBoxLayout()
        price_layout.addStretch()
        price_label = QLabel(f"{product.price} руб. / шт.")
        price_label.setObjectName("product-price")
        price_label.setAlignment(Qt.AlignCenter)
        price_layout.addWidget(price_label)
        price_layout.addStretch()
        card_layout.addLayout(price_layout)

        # Информация: количество и итого (центрируем всю строку)
        info_layout = QHBoxLayout()
        info_layout.addStretch()  # Stretch слева для центрирования
        quantity_label = QLabel("Количество:")
        info_layout.addWidget(quantity_label)

        quantity_spin = QSpinBox()
        quantity_spin.setMinimum(1)
        quantity_spin.setValue(cart_item.quantity)
        quantity_spin.valueChanged.connect(partial(self.update_quantity, product.id))
        info_layout.addWidget(quantity_spin)

        total_item_label = QLabel(f"{product.price * cart_item.quantity} руб.")
        total_item_label.setObjectName("product-price")
        total_item_label.setAlignment(Qt.AlignRight)
        info_layout.addWidget(total_item_label)
        info_layout.addStretch()  # Stretch справа для центрирования
        card_layout.addLayout(info_layout)

        # Кнопка удаления (маленькая, строго по центру)
        actions_layout = QHBoxLayout()
        remove_btn = QPushButton("Удалить")
        remove_btn.setObjectName("small")
        remove_btn.clicked.connect(lambda: self.remove_from_cart(product.id))
        actions_layout.addStretch()
        actions_layout.addWidget(remove_btn)
        actions_layout.addStretch()
        card_layout.addLayout(actions_layout)

        return card

    def update_quantity(self, product_id, quantity):
        update_cart_quantity(product_id, self.current_user, quantity)
        self.update_cart()

    def remove_from_cart(self, product_id):
        remove_from_cart(product_id, self.current_user)
        self.update_cart()

    def clear_cart(self):
        clear_cart(self.current_user)
        self.update_cart()
        QMessageBox.information(self, "Успех", "Корзина очищена!")

    # --- Оформление заказа ---
    def order_cart(self):
        if not self.current_user:
            QMessageBox.warning(self, "Ошибка", "Войдите в аккаунт!")
            return
        cart_items = database.get_cart(self.current_user)
        if not cart_items:
            QMessageBox.warning(self, "Ошибка", "Корзина пуста!")
            return
        try:
            database.create_order(self.current_user, cart_items)
            QMessageBox.information(self, "Успех", "Заказ оформлен!")
            self.update_cart()
            self.update_orders()
        except ValueError as e:
            QMessageBox.warning(self, "Ошибка", str(e))

    def setup_orders(self):
        layout = QVBoxLayout()
        self.orders_table = QTableWidget()
        self.orders_table.setColumnCount(5)
        self.orders_table.setHorizontalHeaderLabels(["ID заказа", "Товар", "Количество", "Дата", "Статус"])
        layout.addWidget(self.orders_table)
        self.orders_tab.setLayout(layout)
        self.update_orders()

    def update_orders(self):
        if not self.current_user:
            self.orders_table.setRowCount(0)
            return
        orders = get_orders(self.current_user)
        self.orders_table.setRowCount(len(orders))
        for row, order in enumerate(orders):
            self.orders_table.setItem(row, 0, QTableWidgetItem(str(order[0])))
            self.orders_table.setItem(row, 1, QTableWidgetItem(order[1]))
            self.orders_table.setItem(row, 2, QTableWidgetItem(str(order[2])))
            self.orders_table.setItem(row, 3, QTableWidgetItem(order[3]))
            self.orders_table.setItem(row, 4, QTableWidgetItem(order[4]))

    def setup_admin(self):
        layout = QVBoxLayout()

        # -------------------------------
        # Таблица товаров
        self.admin_products_table = QTableWidget()
        self.admin_products_table.setColumnCount(5)
        self.admin_products_table.setHorizontalHeaderLabels(
            ["ID", "Название", "Категория", "Цена", "Описание"]
        )
        self.admin_products_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.admin_products_table.setSelectionMode(QTableWidget.SingleSelection)
        layout.addWidget(QLabel("Список товаров:"))
        layout.addWidget(self.admin_products_table)

        # Кнопка удаления выбранного товара
        delete_btn = QPushButton("Удалить выбранный товар")
        delete_btn.setObjectName("small")
        delete_btn.clicked.connect(self.delete_selected_product)
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(delete_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # -------------------------------
        # Добавление товара
        add_group = QGroupBox("Добавить товар")
        add_layout = QFormLayout()
        self.add_name = QLineEdit()
        self.add_desc = QTextEdit()
        self.add_price = QLineEdit()
        self.add_image = QLineEdit()
        self.add_category = QComboBox()
        self.add_category.addItems(["Оливковое", "Подсолнечное", "Льняное"])

        add_btn = QPushButton("Добавить")
        add_btn.setObjectName("small")
        add_btn.clicked.connect(self.add_product_admin)

        # Центрируем кнопку
        add_btn_layout = QHBoxLayout()
        add_btn_layout.addStretch()
        add_btn_layout.addWidget(add_btn)
        add_btn_layout.addStretch()
        add_layout.addRow(add_btn_layout)

        add_layout.addRow("Название:", self.add_name)
        add_layout.addRow("Описание:", self.add_desc)
        add_layout.addRow("Цена:", self.add_price)
        add_layout.addRow("Изображение:", self.add_image)
        add_layout.addRow("Категория:", self.add_category)
        add_group.setLayout(add_layout)
        layout.addWidget(add_group)

        # -------------------------------
        # Управление заказами
        orders_group = QGroupBox("Заказы")
        orders_layout = QVBoxLayout()
        self.admin_orders_table = QTableWidget()
        self.admin_orders_table.setColumnCount(6)
        self.admin_orders_table.setHorizontalHeaderLabels(
            ["ID", "Пользователь", "Товар", "Кол-во", "Дата", "Статус"]
        )
        orders_layout.addWidget(self.admin_orders_table)

        update_status_btn = QPushButton("Обновить статус")
        update_status_btn.setObjectName("small")
        update_status_btn.clicked.connect(self.update_order_status)

        # Центрируем кнопку
        status_btn_layout = QHBoxLayout()
        status_btn_layout.addStretch()
        status_btn_layout.addWidget(update_status_btn)
        status_btn_layout.addStretch()
        orders_layout.addLayout(status_btn_layout)

        orders_group.setLayout(orders_layout)
        layout.addWidget(orders_group)

        self.admin_tab.setLayout(layout)

        # Загружаем данные
        self.update_admin_products()
        self.update_admin_orders()

    def update_admin_products(self):
        products = get_products() or []

        table = self.admin_products_table
        table.blockSignals(True)

        table.clear()

        self.delete_btn.clicked.connect(self.delete_selected_product)

        table.setRowCount(len(products))
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(
            ["ID", "Название", "Категория", "Цена", "Описание"]
        )

        for row, p in enumerate(products):
            table.setItem(row, 0, QTableWidgetItem(str(p.id)))
            table.setItem(row, 1, QTableWidgetItem(p.name))
            table.setItem(row, 2, QTableWidgetItem(p.category))
            table.setItem(row, 3, QTableWidgetItem(str(p.price)))
            table.setItem(row, 4, QTableWidgetItem(p.description))

        table.blockSignals(False)

    def delete_selected_product(self):
        table = self.admin_products_table
        row = table.currentRow()

        if row < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите товар")
            return

        product_id = int(table.item(row, 0).text())

        reply = QMessageBox.question(
            self,
            "Удалить",
            "Удалить выбранный товар?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        if not delete_product(product_id):
            QMessageBox.critical(self, "Ошибка", "Не удалось удалить товар")
            return

        QMessageBox.information(self, "Готово", "Товар удалён")
        self.update_admin_products()
        self.load_products()
    def add_product_admin(self):
        name = self.add_name.text()
        desc = self.add_desc.toPlainText()
        price = self.add_price.text()
        image = self.add_image.text()
        category = self.add_category.currentText()
        result = add_product(name, desc, price, image, category)
        if result is True:
            QMessageBox.information(self, "Успех", "Товар добавлен!")
            self.update_admin_products()  # <-- обновляем таблицу
            self.load_products()  # <-- обновляем каталог
        else:
            QMessageBox.warning(self, "Ошибка", result)

    def update_admin_orders(self):
        orders = get_orders()
        self.admin_orders_table.setRowCount(len(orders))
        for row, order in enumerate(orders):
            self.admin_orders_table.setItem(row, 0, QTableWidgetItem(str(order[0])))
            self.admin_orders_table.setItem(row, 1, QTableWidgetItem(order[1]))
            self.admin_orders_table.setItem(row, 2, QTableWidgetItem(order[2]))
            self.admin_orders_table.setItem(row, 3, QTableWidgetItem(str(order[3])))
            self.admin_orders_table.setItem(row, 4, QTableWidgetItem(order[4]))
            self.admin_orders_table.setItem(row, 5, QTableWidgetItem(order[5]))

    def update_order_status(self):
        selected = self.admin_orders_table.currentRow()
        if selected == -1:
            QMessageBox.warning(self, "Ошибка", "Выберите заказ!")
            return
        order_id = int(self.admin_orders_table.item(selected, 0).text())
        status, ok = QInputDialog.getText(self, "Статус", "Новый статус:")
        if ok:
            conn = connect_db()
            cursor = conn.cursor()
            cursor.execute('UPDATE orders SET status = ? WHERE id = ?', (status, order_id))
            conn.commit()
            conn.close()
            self.update_admin_orders()


    def setup_login(self):
        layout = QVBoxLayout()
        form_layout = QFormLayout()
        self.login_email = QLineEdit()
        self.login_email.setPlaceholderText("email@example.com")
        self.login_name = QLineEdit()
        self.login_name.setPlaceholderText("Имя")
        self.login_address = QLineEdit()
        self.login_address.setPlaceholderText("Адрес")

        login_btn = QPushButton("Войти/Регистрация")
        login_btn.setObjectName("small")
        login_btn.clicked.connect(self.login_user)

        logout_btn = QPushButton("Выйти")
        logout_btn.setObjectName("small")
        logout_btn.clicked.connect(self.logout_user)

        # Центрируем кнопки через HBoxLayout
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        buttons_layout.addWidget(login_btn)
        buttons_layout.addWidget(logout_btn)
        buttons_layout.addStretch()

        form_layout.addRow("Email:", self.login_email)
        form_layout.addRow("Имя:", self.login_name)
        form_layout.addRow("Адрес:", self.login_address)
        form_layout.addRow(buttons_layout)

        layout.addLayout(form_layout)
        self.login_tab.setLayout(layout)

    # --- Вход пользователя ---
    def login_user(self):
        email = self.login_email.text().strip()
        name = self.login_name.text().strip()
        address = self.login_address.text().strip()
        if not email or not name:
            QMessageBox.warning(self, "Ошибка", "Заполните email и имя!")
            return
        # Добавляем пользователя в БД, если не существует
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM users WHERE email = ?', (email,))
        if not cursor.fetchone():
            cursor.execute('INSERT INTO users (name, email, address) VALUES (?, ?, ?)', (name, email, address))
            conn.commit()
        conn.close()
        self.current_user = email  # <-- теперь self.current_user всегда email
        QMessageBox.information(self, "Успех", f"Вы вошли как {name}")
        self.update_cart()
        self.update_orders()

    def logout_user(self):
        self.current_user = None
        QMessageBox.information(self, "Выход", "Вы вышли из аккаунта")
        self.update_cart()
        self.update_orders()

if __name__ == "__main__":
    app = QApplication([])
    window = OilShopApp()
    window.show()
    app.exec_()