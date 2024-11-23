import sys
import os
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QLineEdit, QLabel, QDialog, QComboBox, QDateEdit, QHBoxLayout, QHeaderView, QMessageBox
from PySide6.QtCore import Qt, QDate
from fpdf import FPDF
from sqlalchemy import create_engine, Column, Integer, String, Float, Date, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics

# Настройка SQLAlchemy
DATABASE_URL = 'postgresql://postgres:1234@localhost:5432/baza1'  # Замените на ваши данные
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()
Base = declarative_base()

# Определение моделей
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    fio = Column(String)
    login = Column(String, unique=True)
    password = Column(String)
    pin_code = Column(String)

class Payment(Base):
    __tablename__ = 'payments'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    paymentdate = Column(Date)  
    category = Column(String)
    paymentname = Column(String)
    quantity = Column(Integer)
    price = Column(Float)
    cost = Column(Float)

# Интерфейс
class PaymentInterface(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Интерфейс платежей")
        self.setGeometry(100, 100, 800, 600)

        # Сначала показываем окно авторизации
        self.login_dialog = LoginDialog(self)
        if self.login_dialog.exec() == QDialog.Accepted:
            self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        # Верхняя панель с кнопками и фильтрами
        top_layout = QHBoxLayout()
        self.add_buttons(top_layout)
        self.add_date_selectors(top_layout)
        self.add_category_selector(top_layout)
        self.add_action_buttons(top_layout)

        layout.addLayout(top_layout)

        # Таблица для отображения платежей
        self.table = QTableWidget()
        self.setup_table()
        layout.addWidget(self.table)

        self.setLayout(layout)

        self.load_payments()  # Загружаем платежи при старте

    def add_buttons(self, layout):
        btn_add = QPushButton("+")
        btn_add.clicked.connect(self.open_add_dialog)
        btn_remove = QPushButton("-")
        btn_remove.clicked.connect(self.open_remove_dialog)
        layout.addWidget(btn_add)
        layout.addWidget(btn_remove)

    def add_date_selectors(self, layout):
        date_label_from = QLabel("С:")
        self.date_picker_from = QDateEdit()
        self.date_picker_from.setDate(QDate(2015, 1, 1))
        self.date_picker_from.setCalendarPopup(True)
        self.date_picker_from.dateChanged.connect(self.filter_by_category)  # Обновление при изменении даты

        date_label_to = QLabel("По:")
        self.date_picker_to = QDateEdit()
        self.date_picker_to.setDate(QDate(2015, 1, 1))
        self.date_picker_to.setCalendarPopup(True)
        self.date_picker_to.dateChanged.connect(self.filter_by_category)  # Обновление при изменении даты

        layout.addWidget(date_label_from)
        layout.addWidget(self.date_picker_from)
        layout.addWidget(date_label_to)
        layout.addWidget(self.date_picker_to)


    def add_category_selector(self, layout):
        category_label = QLabel("Категория:")
        self.category_combo = QComboBox()
        self.category_combo.addItems(["Все", "Коммунальные платежи", "Автомобиль", "Питание и быт", "Медицина", "Разное"])
        self.category_combo.currentIndexChanged.connect(self.filter_by_category)
        layout.addWidget(category_label)
        layout.addWidget(self.category_combo)

    def add_action_buttons(self, layout):
        btn_select = QPushButton("Выбрать")
        btn_select.clicked.connect(self.open_login_dialog)
        btn_clear = QPushButton("Очистить")
        btn_report = QPushButton("Отчет")
        btn_report.clicked.connect(self.generate_report)  # Генерация отчета
        layout.addWidget(btn_select)
        layout.addWidget(btn_clear)
        layout.addWidget(btn_report)

    def setup_table(self):
        self.table.setColumnCount(5)
        self.table.setRowCount(0)
        self.table.setHorizontalHeaderLabels(["Наименование платежа", "Количество", "Цена", "Сумма", "Категория"])

        # Включаем возможность сортировки по каждому столбцу
        self.table.setSortingEnabled(True)  # Включаем сортировку
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)


    def load_payments(self):
        self.table.setRowCount(0)  # Очищаем таблицу

        # Получаем все платежи, отсортированные по дате
        payments = session.query(Payment).order_by(Payment.paymentdate).all()

        for payment in payments:
            row_position = self.table.rowCount()
            self.table.insertRow(row_position)
            self.table.setItem(row_position, 0, QTableWidgetItem(payment.paymentname))
            self.table.setItem(row_position, 1, QTableWidgetItem(str(payment.quantity)))
            self.table.setItem(row_position, 2, QTableWidgetItem(str(payment.price)))
            self.table.setItem(row_position, 3, QTableWidgetItem(str(payment.cost)))
            self.table.setItem(row_position, 4, QTableWidgetItem(payment.category))


    def filter_by_category(self):
        selected_category = self.category_combo.currentText()
        start_date = self.date_picker_from.date().toPython()  # Дата начала
        end_date = self.date_picker_to.date().toPython()  # Дата окончания

        # Получаем все платежи с учетом фильтров по категории и датам
        if selected_category == "Все":
            payments = session.query(Payment).filter(
                Payment.paymentdate.between(start_date, end_date)
            ).order_by(Payment.paymentdate).all()
        else:
            payments = session.query(Payment).filter(
                Payment.category == selected_category,
                Payment.paymentdate.between(start_date, end_date)
            ).order_by(Payment.paymentdate).all()

        self.table.setRowCount(0)  # Очищаем таблицу
        for payment in payments:
            row_position = self.table.rowCount()
            self.table.insertRow(row_position)
            self.table.setItem(row_position, 0, QTableWidgetItem(payment.paymentname))
            self.table.setItem(row_position, 1, QTableWidgetItem(str(payment.quantity)))
            self.table.setItem(row_position, 2, QTableWidgetItem(str(payment.price)))
            self.table.setItem(row_position, 3, QTableWidgetItem(str(payment.cost)))
            self.table.setItem(row_position, 4, QTableWidgetItem(payment.category))


    def open_add_dialog(self):
        dialog = AddPaymentDialog(self)
        dialog.exec()

    def open_remove_dialog(self):
        selected_row = self.table.currentRow()
        if selected_row >= 0:
            payment_name = self.table.item(selected_row, 0).text()
            dialog = RemovePaymentDialog(self, payment_name, selected_row)
            dialog.exec()
        else:
            QMessageBox.warning(self, "Ошибка", "Сначала выберите запись для удаления.")

    def open_login_dialog(self):
        self.login_dialog = LoginDialog(self)
        if self.login_dialog.exec() == QDialog.Accepted:
            self.load_payments()  # Обновляем данные после смены пользователя

    def generate_report(self):
        try:
            # Загружаем данные из базы данных
            category_filter = self.category_combo.currentText()
            start_date = self.date_picker_from.date().toPython()  # Получаем выбранную дату начала
            end_date = self.date_picker_to.date().toPython()  # Получаем выбранную дату окончания

            # Форматируем даты для отображения
            start_date_str = start_date.strftime("%d-%m-%Y")
            end_date_str = end_date.strftime("%d-%m-%Y")

            # Получаем платежи из базы данных, учитывая фильтр по категории и датам
            # Получаем платежи из базы данных, учитывая фильтр по категории и датам
            if category_filter == "Все":
                payments = session.query(Payment).filter(
                    Payment.paymentdate.between(start_date, end_date)
                ).order_by(Payment.paymentdate).all()
            else:
                payments = session.query(Payment).filter(
                    Payment.category == category_filter,
                    Payment.paymentdate.between(start_date, end_date)
                ).order_by(Payment.paymentdate).all()

            # Группировка платежей по категориям
            grouped_payments = {}
            for payment in payments:
                if payment.category not in grouped_payments:
                    grouped_payments[payment.category] = []
                grouped_payments[payment.category].append(payment)

            # Создаем объект PDF
            pdf = FPDF()
            pdf.set_auto_page_break(auto=True, margin=15)  # Автоматический перенос на новую страницу
            pdf.add_page()

            # Проверяем наличие шрифта и добавляем его
            font_path = './DejaVuSans.ttf'  # Путь к шрифту
            if os.path.exists(font_path):
                pdf.add_font('DejaVuSans', '', font_path, uni=True)
                pdf.set_font('DejaVuSans', '', 12)
            else:
                pdf.set_font('Arial', '', 12)

            # Заголовок отчета
            pdf.cell(200, 10, txt="Отчет по платежам", ln=True, align='C')
            pdf.ln(10)  # Переход на новую строку
            pdf.cell(200, 10, txt=f"Период: {start_date_str} - {end_date_str}", ln=True)
            pdf.ln(10)  # Переход на новую строку

            total_cost = 0  # Для вычисления общей стоимости

            # Заполняем таблицу отчетом, группируя по категориям
            for category, payments_in_category in grouped_payments.items():
                pdf.cell(200, 10, txt=f"{category}", ln=True, align='L')
                category_total = 0  # Сумма по категории
                for payment in payments_in_category:
                    payment_cost = payment.quantity * payment.price
                    category_total += payment_cost
                    pdf.cell(0, 10, txt=f"   {payment.paymentname} - {payment_cost:.2f} руб.", ln=True)
                pdf.cell(200, 10, txt=f"  Итого по {category}: {category_total:.2f} руб.", ln=True)
                pdf.ln(5)  # Переход на новую строку после каждой категории

                total_cost += category_total  # Добавляем стоимость категории в общий итог

            # Отображаем итоговую стоимость всех платежей
            pdf.ln(10)  # Переход на новую строку
            pdf.cell(200, 10, txt=f"Итого: {total_cost:.2f} руб.", ln=True, align='R')

            # Сохраняем PDF файл
            pdf.output("report.pdf")
            QMessageBox.information(self, "Отчет готов", "Отчет успешно сгенерирован и сохранен как report.pdf.")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось создать отчет: {e}")


class AddPaymentDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Добавить платеж")
        self.setGeometry(100, 100, 400, 300)
        layout = QVBoxLayout()
        self.setLayout(layout)

# Вы можете добавить другие диалоговые окна и обработчики

# Диалоговое окно для добавления платежа
class AddPaymentDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Добавить платеж")
        self.setGeometry(150, 150, 400, 350)

        layout = QVBoxLayout()

        # Выбор пользователя
        self.user_combo = QComboBox()
        self.load_users()
        layout.addWidget(QLabel("Выберите пользователя:"))
        layout.addWidget(self.user_combo)

        # Выбор категории
        self.category_combo = QComboBox()
        self.category_combo.addItems(["Коммунальные платежи", "Автомобиль", "Питание и быт", "Медицина", "Разное"])
        layout.addWidget(QLabel("Выбор категории:"))
        layout.addWidget(self.category_combo)

        # Название платежа
        self.purpose_input = QLineEdit()
        layout.addWidget(QLabel("Название платежа:"))
        layout.addWidget(self.purpose_input)

        # Количество
        self.quantity_input = QLineEdit()
        layout.addWidget(QLabel("Количество:"))
        layout.addWidget(self.quantity_input)

        # Цена
        self.price_input = QLineEdit()
        layout.addWidget(QLabel("Цена (р):"))
        layout.addWidget(self.price_input)

        # Дата платежа
        self.date_picker = QDateEdit()
        self.date_picker.setDate(QDate.currentDate())
        self.date_picker.setCalendarPopup(True)
        layout.addWidget(QLabel("Дата платежа:"))
        layout.addWidget(self.date_picker)

        # Кнопки
        btn_layout = QHBoxLayout()
        btn_cancel = QPushButton("Отменить")
        btn_add = QPushButton("Добавить")
        btn_cancel.clicked.connect(self.reject)
        btn_add.clicked.connect(self.add_payment)
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_add)

        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def load_users(self):
        # Загрузка всех пользователей
        users = session.query(User).all()
        self.user_combo.addItems([user.fio for user in users])

    def add_payment(self):
        # Получаем выбранного пользователя
        user_name = self.user_combo.currentText()
        user = session.query(User).filter_by(fio=user_name).first()

        # Если пользователь не выбран
        if user is None:
            QMessageBox.warning(self, "Ошибка", "Выберите пользователя.")
            return

        category = self.category_combo.currentText()
        purpose = self.purpose_input.text()
        quantity = self.quantity_input.text()
        price = self.price_input.text()
        payment_date = self.date_picker.date().toPython()

        # Проверка на заполненность полей
        if not purpose or not quantity or not price:
            QMessageBox.warning(self, "Ошибка", "Все поля должны быть заполнены.")
            return

        # Преобразование строк в нужный формат
        try:
            quantity = int(quantity)
            price = float(price)
        except ValueError:
            QMessageBox.warning(self, "Ошибка", "Количество и цена должны быть числами.")
            return

        # Создание и добавление платежа
        payment = Payment(
            user_id=user.id,  # Передаем правильный id пользователя
            payment_name=purpose,
            quantity=quantity,
            price=price,
            cost=quantity * price,  # Стоимость = количество * цена
            category=category,
            payment_date=payment_date
        )

        try:
            session.add(payment)
            session.commit()
            QMessageBox.information(self, "Успех", "Платеж добавлен.")
            self.accept()
        except Exception as e:
            session.rollback()  # Откат транзакции в случае ошибки
            QMessageBox.warning(self, "Ошибка", f"Произошла ошибка при добавлении платежа: {e}")

# Диалоговое окно для удаления платежа
class RemovePaymentDialog(QDialog):
    def __init__(self, parent, payment_name, row_index):
        super().__init__(parent)
        self.setWindowTitle("Удалить платеж")
        self.setGeometry(150, 150, 300, 150)

        layout = QVBoxLayout()
        layout.addWidget(QLabel(f"Удалить запись: {payment_name}"))

        # Кнопки
        btn_layout = QHBoxLayout()
        btn_cancel = QPushButton("Отмена")
        btn_remove = QPushButton("Удалить")
        btn_cancel.clicked.connect(self.reject)
        btn_remove.clicked.connect(lambda: self.remove_payment(row_index))
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_remove)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def remove_payment(self, row_index):
        payment_name = self.parent().table.item(row_index, 0).text()
        payment = session.query(Payment).filter_by(payment_name=payment_name).first()
        if payment:
            session.delete(payment)
            session.commit()  # Сохраняем изменения в базе данных
            self.parent().load_payments()  # Обновляем таблицу
            self.accept()  # Закрыть диалог

# Диалоговое окно для авторизации
class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Login")
        self.setFixedSize(300, 150)

        layout = QVBoxLayout()

        # Выпадающий список логинов
        self.username_combo = QComboBox(self)
        self.load_usernames()
        layout.addWidget(QLabel("Выберите логин"))
        layout.addWidget(self.username_combo)

        self.password_input = QLineEdit(self)
        self.password_input.setPlaceholderText("Введите пароль")
        self.password_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.password_input)

        self.login_button = QPushButton("Войти", self)
        layout.addWidget(self.login_button)

        self.error_label = QLabel("", self)
        self.error_label.setStyleSheet("color: red")
        layout.addWidget(self.error_label)

        self.login_button.clicked.connect(self.authenticate)

        self.setLayout(layout)

    def load_usernames(self):
        users = session.query(User).all()
        self.username_combo.addItems([user.login for user in users])

    def authenticate(self):
        login = self.username_combo.currentText()
        password = self.password_input.text()

        # Проверка данных в базе
        user = session.query(User).filter(User.login == login, User.password == password).first()

        if user:
            self.accept()  # Закрытие окна и подтверждение успешной авторизации
        else:
            self.error_label.setText("Неверный логин или пароль")

if __name__ == '__main__':
    # Создание таблиц в базе данных
    Base.metadata.create_all(engine)

    app = QApplication(sys.argv)
    window = PaymentInterface()
    window.show()
    sys.exit(app.exec())
