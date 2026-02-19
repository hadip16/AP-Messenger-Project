"""
+-----------------------------------+
|             Messenger             |
+-----------------------------------+
| - server: MessengerServer         |
| - clients: dict                   |
+-----------------------------------+
| + start_server()                  |
| + handle_client()                 |
+-----------------------------------+

+-----------------------------------+
|              Client GUI            |
+-----------------------------------+
| - stacked_widget: QStackedWidget  |
| - current_user: User              |
+-----------------------------------+
| + initUI()                        |
| + login()                         |
| + signup()                        |
| + update_profile()                |
| + load_contacts()                 |
+-----------------------------------+

+-----------------------------------+
|             Database              |
+-----------------------------------+
| - engine: SQLAlchemy Engine       |
| - Session: sessionmaker           |
+-----------------------------------+
| + create_tables()                 |
| + get_session()                   |
+-----------------------------------+

+-----------------------------------+
|               User                |
+-----------------------------------+
| - id: int                         |
| - username: str                   |
| - phone: str                      |
| - password: str                   |
| - profile_pic: str                |
+-----------------------------------+

+-----------------------------------+
|             Message               |
+-----------------------------------+
| - id: int                         |
| - sender_id: int                  |
| - receiver_id: int                |
| - content: str                    |
| - file_data: bytes                |
| - file_type: str                  |
+-----------------------------------+
"""



import socket
import threading
import sys
import os
import sqlalchemy
import shutil
import time
from sqlalchemy import create_engine, Column, String, Integer, LargeBinary
from sqlalchemy.orm import declarative_base, sessionmaker
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QListWidget, QTextEdit, QStackedWidget,
    QFileDialog, QMessageBox, QDialog, QFormLayout, QListWidgetItem
)
from PyQt6.QtCore import Qt, QSize, QThread, pyqtSignal
from PyQt6.QtGui import QPixmap, QImage, QIcon, QFont

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    phone = Column(String, unique=True)
    password = Column(String)
    profile_pic = Column(String)


class Contact(Base):
    __tablename__ = 'contacts'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    contact_id = Column(Integer)


class Message(Base):
    __tablename__ = 'messages'
    id = Column(Integer, primary_key=True)
    sender_id = Column(Integer)
    receiver_id = Column(Integer)
    content = Column(String)
    file_data = Column(LargeBinary)
    file_type = Column(String)


engine = create_engine('sqlite:///messenger.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

HOST = '127.0.0.1'
PORT = 65432


# ====================== SOCKET SERVER ======================
class MessengerServer:
    def __init__(self):
        self.clients = {}
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((HOST, PORT))
        self.server_socket.listen()
        print(f"Server listening on {HOST}:{PORT}")

    def handle_client(self, client_socket, address):
        user_id = None
        while True:
            try:
                data = client_socket.recv(1024)
                if not data:
                    break

                parts = data.decode().split(':', 3)
                if len(parts) < 4:
                    continue

                sender_id, receiver_id, msg_type, content = parts
                sender_id = int(sender_id)
                receiver_id = int(receiver_id)

                session = Session()
                new_message = Message(
                    sender_id=sender_id,
                    receiver_id=receiver_id,
                    content=content,
                    file_type=msg_type if msg_type != 'text' else None
                )
                session.add(new_message)
                session.commit()

                if receiver_id in self.clients:
                    self.clients[receiver_id].sendall(data)

            except Exception as e:
                print(f"Error: {e}")
                break

        if user_id in self.clients:
            del self.clients[user_id]
        client_socket.close()

    def start(self):
        while True:
            client_socket, address = self.server_socket.accept()
            user_id = int(client_socket.recv(1024).decode())
            self.clients[user_id] = client_socket
            thread = threading.Thread(
                target=self.handle_client,
                args=(client_socket, address)
            )
            thread.start()

            # ====================== CLIENT GUI ======================


class LoginWindow(QWidget):
    def __init__(self, stacked_widget):
        super().__init__()
        self.stacked_widget = stacked_widget
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        self.logo = QLabel()
        self.logo.setPixmap(QPixmap("logo.png").scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio))
        self.logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.logo)

        self.title = QLabel("Messenger")
        self.title.setFont(QFont("Arial", 20))
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.title)

        form_layout = QFormLayout()

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        form_layout.addRow("Username:", self.username_input)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        form_layout.addRow("Password:", self.password_input)

        layout.addLayout(form_layout)

        self.login_btn = QPushButton("Sign In")
        self.login_btn.clicked.connect(self.login)
        layout.addWidget(self.login_btn)

        self.signup_btn = QPushButton("Create Account")
        self.signup_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(1))
        layout.addWidget(self.signup_btn)

        self.setLayout(layout)

    def login(self):
        username = self.username_input.text()
        password = self.password_input.text()

        if not username or not password:
            QMessageBox.warning(self, "Error", "Please fill all fields")
            return

        session = Session()
        user = session.query(User).filter_by(username=username, password=password).first()

        if user:
            self.stacked_widget.main_window.current_user = user
            self.stacked_widget.setCurrentIndex(2)
        else:
            QMessageBox.warning(self, "Error", "Invalid credentials")


class SignupWindow(QWidget):
    def __init__(self, stacked_widget):
        super().__init__()
        self.stacked_widget = stacked_widget
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        self.title = QLabel("Create Account")
        self.title.setFont(QFont("Arial", 20))
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.title)

        form_layout = QFormLayout()

        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("Phone Number")
        form_layout.addRow("Phone:", self.phone_input)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        form_layout.addRow("Username:", self.username_input)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        form_layout.addRow("Password:", self.password_input)

        self.confirm_input = QLineEdit()
        self.confirm_input.setPlaceholderText("Confirm Password")
        self.confirm_input.setEchoMode(QLineEdit.EchoMode.Password)
        form_layout.addRow("Confirm:", self.confirm_input)

        layout.addLayout(form_layout)

        self.signup_btn = QPushButton("Sign Up")
        self.signup_btn.clicked.connect(self.signup)
        layout.addWidget(self.signup_btn)

        self.back_btn = QPushButton("Back to Login")
        self.back_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        layout.addWidget(self.back_btn)

        self.setLayout(layout)

    def signup(self):
        phone = self.phone_input.text()
        username = self.username_input.text()
        password = self.password_input.text()
        confirm = self.confirm_input.text()

        if not all([phone, username, password, confirm]):
            QMessageBox.warning(self, "Error", "Please fill all fields")
            return

        if password != confirm:
            QMessageBox.warning(self, "Error", "Passwords don't match")
            return

        session = Session()
        if session.query(User).filter_by(username=username).first():
            QMessageBox.warning(self, "Error", "Username already exists")
            return

        if session.query(User).filter_by(phone=phone).first():
            QMessageBox.warning(self, "Error", "Phone number already registered")
            return

        new_user = User(phone=phone, username=username, password=password)
        session.add(new_user)
        session.commit()
        QMessageBox.information(self, "Success", "Account created!")
        self.stacked_widget.setCurrentIndex(0)


class MainWindow(QMainWindow):
    def __init__(self, stacked_widget):
        super().__init__()
        self.stacked_widget = stacked_widget
        self.current_user = None
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Messenger")
        self.setGeometry(100, 100, 800, 600)

        main_widget = QWidget()
        main_layout = QHBoxLayout()

        sidebar = QWidget()
        sidebar.setFixedWidth(250)
        sidebar_layout = QVBoxLayout()

        self.profile_header = QHBoxLayout()
        self.profile_pic = QLabel()
        self.profile_pic.setFixedSize(50, 50)
        self.profile_pic.setStyleSheet("border-radius: 25px; border: 1px solid gray")
        self.profile_header.addWidget(self.profile_pic)

        self.username_label = QLabel()
        self.username_label.setFont(QFont("Arial", 12))
        self.profile_header.addWidget(self.username_label)

        self.settings_btn = QPushButton("⚙️")
        self.settings_btn.setFixedSize(30, 30)
        self.settings_btn.clicked.connect(self.open_settings)
        self.profile_header.addWidget(self.settings_btn)

        self.add_contact_btn = QPushButton("+")
        self.add_contact_btn.setFixedSize(30, 30)
        self.add_contact_btn.clicked.connect(self.open_add_contact)
        self.profile_header.addWidget(self.add_contact_btn)

        sidebar_layout.addLayout(self.profile_header)

        self.contacts_list = QListWidget()
        self.contacts_list.itemClicked.connect(self.open_chat)
        sidebar_layout.addWidget(self.contacts_list)

        sidebar.setLayout(sidebar_layout)
        main_layout.addWidget(sidebar)

        self.stacked_content = QStackedWidget()

        home_screen = QLabel("Select a contact to start chatting")
        home_screen.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.stacked_content.addWidget(home_screen)

        main_layout.addWidget(self.stacked_content)
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

    def update_profile(self):
        if self.current_user:
            self.username_label.setText(self.current_user.username)
            if self.current_user.profile_pic:
                pixmap = QPixmap(self.current_user.profile_pic)
                self.profile_pic.setPixmap(pixmap.scaled(50, 50, Qt.AspectRatioMode.KeepAspectRatio,
                                                         Qt.TransformationMode.SmoothTransformation))

    def load_contacts(self):
        self.contacts_list.clear()
        session = Session()
        contacts = session.query(Contact).filter_by(user_id=self.current_user.id).all()
        for contact in contacts:
            user = session.query(User).get(contact.contact_id)
            item = QListWidgetItem(user.username)
            item.setData(Qt.ItemDataRole.UserRole, user.id)
            self.contacts_list.addItem(item)

    def open_settings(self):
        settings_dialog = SettingsDialog(self.current_user, self)
        settings_dialog.exec()
        self.update_profile()

    def open_add_contact(self):
        add_dialog = AddContactDialog(self.current_user, self)
        add_dialog.exec()
        self.load_contacts()

    def open_chat(self, item):
        contact_id = item.data(Qt.ItemDataRole.UserRole)
        session = Session()
        contact = session.query(User).get(contact_id)

        for i in range(1, self.stacked_content.count()):
            if self.stacked_content.widget(i).contact_id == contact_id:
                self.stacked_content.setCurrentIndex(i)
                return

        chat_window = ChatWindow(self.current_user, contact)
        self.stacked_content.addWidget(chat_window)
        self.stacked_content.setCurrentIndex(self.stacked_content.count() - 1)


class SettingsDialog(QDialog):
    def __init__(self, user, parent=None):
        super().__init__(parent)
        self.user = user
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Settings")
        layout = QVBoxLayout()

        form = QFormLayout()

        self.username_input = QLineEdit(self.user.username)
        form.addRow("Username:", self.username_input)

        self.phone_input = QLineEdit(self.user.phone)
        form.addRow("Phone:", self.phone_input)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("New password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("New Password:", self.password_input)

        self.confirm_input = QLineEdit()
        self.confirm_input.setPlaceholderText("Confirm password")
        self.confirm_input.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("Confirm:", self.confirm_input)

        layout.addLayout(form)

        self.profile_pic = QLabel()
        self.profile_pic.setFixedSize(100, 100)
        self.profile_pic.setStyleSheet("border-radius: 50px; border: 1px solid gray")
        if self.user.profile_pic:
            pixmap = QPixmap(self.user.profile_pic)
            self.profile_pic.setPixmap(pixmap.scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio))
        layout.addWidget(self.profile_pic, alignment=Qt.AlignmentFlag.AlignCenter)

        self.change_pic_btn = QPushButton("Change Profile Picture")
        self.change_pic_btn.clicked.connect(self.change_profile_picture)
        layout.addWidget(self.change_pic_btn)

        self.save_btn = QPushButton("Save Changes")
        self.save_btn.clicked.connect(self.save_changes)
        layout.addWidget(self.save_btn)

        self.setLayout(layout)

    def change_profile_picture(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Profile Picture",
            "",
            "Image Files (*.png *.jpg *.jpeg)"
        )
        if file_path:
            dest = os.path.join(os.getcwd(), "profile_pics", f"{self.user.id}.jpg")
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            try:
                shutil.copyfile(file_path, dest)
                self.user.profile_pic = dest
                pixmap = QPixmap(dest)
                self.profile_pic.setPixmap(pixmap.scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio))
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not update picture:\n{str(e)}")

    def save_changes(self):
        new_username = self.username_input.text()
        new_phone = self.phone_input.text()
        new_password = self.password_input.text()
        confirm_password = self.confirm_input.text()

        if not new_username:
            QMessageBox.warning(self, "Error", "Username cannot be empty")
            return

        session = Session()

        if new_username != self.user.username:
            if session.query(User).filter_by(username=new_username).first():
                QMessageBox.warning(self, "Error", "Username already exists")
                return

        if new_phone != self.user.phone:
            if session.query(User).filter_by(phone=new_phone).first():
                QMessageBox.warning(self, "Error", "Phone number already exists")
                return

        if new_password and new_password != confirm_password:
            QMessageBox.warning(self, "Error", "Passwords don't match")
            return

        self.user.username = new_username
        self.user.phone = new_phone
        if new_password:
            self.user.password = new_password

        session.commit()
        QMessageBox.information(self, "Success", "Profile updated!")
        self.accept()


class AddContactDialog(QDialog):
    def __init__(self, user, parent=None):
        super().__init__(parent)
        self.user = user
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Add Contact")
        layout = QVBoxLayout()

        form = QFormLayout()

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        form.addRow("Username:", self.username_input)

        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("Phone Number")
        form.addRow("Phone:", self.phone_input)

        layout.addLayout(form)

        self.add_btn = QPushButton("Add Contact")
        self.add_btn.clicked.connect(self.add_contact)
        layout.addWidget(self.add_btn)

        self.setLayout(layout)

    def add_contact(self):
        username = self.username_input.text()
        phone = self.phone_input.text()

        if not username and not phone:
            QMessageBox.warning(self, "Error", "Enter username or phone")
            return

        session = Session()
        contact = None

        if username:
            contact = session.query(User).filter_by(username=username).first()
        elif phone:
            contact = session.query(User).filter_by(phone=phone).first()

        if not contact:
            QMessageBox.warning(self, "Error", "User not found")
            return

        if contact.id == self.user.id:
            QMessageBox.warning(self, "Error", "You can't add yourself")
            return

        existing = session.query(Contact).filter_by(
            user_id=self.user.id,
            contact_id=contact.id
        ).first()

        if existing:
            QMessageBox.warning(self, "Error", "Contact already added")
            return

        new_contact = Contact(user_id=self.user.id, contact_id=contact.id)
        session.add(new_contact)
        session.commit()
        QMessageBox.information(self, "Success", "Contact added!")
        self.accept()

class ChatWindow(QWidget):
    def __init__(self, user, contact, parent=None):
        super().__init__(parent)
        self.user = user
        self.contact = contact
        self.contact_id = contact.id
        self.initUI()
        self.load_messages()

    def initUI(self):
        layout = QVBoxLayout()

        header = QHBoxLayout()
        self.contact_name = QLabel(self.contact.username)
        self.contact_name.setFont(QFont("Arial", 14))
        header.addWidget(self.contact_name)
        layout.addLayout(header)

        self.message_display = QTextEdit()
        self.message_display.setReadOnly(True)
        layout.addWidget(self.message_display)

        input_layout = QHBoxLayout()

        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Type a message...")
        input_layout.addWidget(self.message_input)

        self.send_btn = QPushButton("Send")
        self.send_btn.clicked.connect(self.send_text_message)
        input_layout.addWidget(self.send_btn)

        # Attachment buttons
        self.attach_btn = QPushButton("📎")
        self.attach_btn.clicked.connect(self.attach_file)
        input_layout.addWidget(self.attach_btn)

        self.sticker_btn = QPushButton("😊")
        self.sticker_btn.clicked.connect(self.send_sticker)
        input_layout.addWidget(self.sticker_btn)

        self.voice_btn = QPushButton("🎤")
        self.voice_btn.clicked.connect(self.record_voice)
        input_layout.addWidget(self.voice_btn)

        layout.addLayout(input_layout)
        self.setLayout(layout)

    def load_messages(self):
        session = Session()
        messages = session.query(Message).filter(
            ((Message.sender_id == self.user.id) & (Message.receiver_id == self.contact.id)) |
            ((Message.sender_id == self.contact.id) & (Message.receiver_id == self.user.id))
        ).order_by(Message.id).all()

        for msg in messages:
            self.display_message(msg)

    def display_message(self, message):
        sender = "You" if message.sender_id == self.user.id else self.contact.username
        content = message.content

        if message.file_type == 'sticker':
            content = f"<img src='{content}' width='100' />"
        elif message.file_type == 'voice':
            content = "🔊 Voice message"
        elif message.file_type == 'file':
            content = f"📄 File: {content}"

        self.message_display.append(f"<b>{sender}:</b> {content}")

    def send_text_message(self):
        text = self.message_input.text().strip()
        if not text:
            return

        session = Session()
        new_message = Message(
            sender_id=self.user.id,
            receiver_id=self.contact.id,
            content=text,
            file_type='text'
        )
        session.add(new_message)
        session.commit()

        self.message_display.append(f"<b>You:</b> {text}")
        self.message_input.clear()

    def attach_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select File",
            "",
            "All Files (*);;PDF (*.pdf);;Images (*.png *.jpg *.jpeg)"
        )
        if file_path:
            file_name = os.path.basename(file_path)

            session = Session()
            new_message = Message(
                sender_id=self.user.id,
                receiver_id=self.contact.id,
                content=file_name,
                file_type='file'
            )
            session.add(new_message)
            session.commit()

            self.message_display.append(f"<b>You:</b> 📄 File: {file_name}")

    def send_sticker(self):
        sticker_dialog = StickerDialog(self)
        if sticker_dialog.exec():
            sticker_path = sticker_dialog.selected_sticker

            session = Session()
            new_message = Message(
                sender_id=self.user.id,
                receiver_id=self.contact.id,
                content=sticker_path,
                file_type='sticker'
            )
            session.add(new_message)
            session.commit()

            self.message_display.append(f"<b>You:</b> <img src='{sticker_path}' width='100' />")

    def record_voice(self):

        QMessageBox.information(self, "Voice Message", "Voice recording started...")
        time.sleep(2)  # Simulate recording

        session = Session()
        new_message = Message(
            sender_id=self.user.id,
            receiver_id=self.contact.id,
            content="voice_note.wav",
            file_type='voice'
        )
        session.add(new_message)
        session.commit()

        self.message_display.append(f"<b>You:</b> 🔊 Voice message")


class StickerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_sticker = None
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Select Sticker")
        layout = QVBoxLayout()

        sticker_layout = QHBoxLayout()

        stickers = ["sticker1.png", "sticker2.png", "sticker3.png"]
        for sticker in stickers:
            btn = QPushButton()
            btn.setIcon(QIcon(sticker))
            btn.setIconSize(QSize(100, 100))
            btn.clicked.connect(lambda _, s=sticker: self.select_sticker(s))
            sticker_layout.addWidget(btn)

        layout.addLayout(sticker_layout)
        self.setLayout(layout)

    def select_sticker(self, sticker_path):
        self.selected_sticker = sticker_path
        self.accept()


# ====================== MAIN APPLICATION ======================
class MessengerApp(QApplication):
    def __init__(self, argv):
        super().__init__(argv)
        self.stacked_widget = QStackedWidget()

        self.login_window = LoginWindow(self.stacked_widget)
        self.signup_window = SignupWindow(self.stacked_widget)
        self.main_window = MainWindow(self.stacked_widget)

        self.stacked_widget.addWidget(self.login_window)
        self.stacked_widget.addWidget(self.signup_window)
        self.stacked_widget.addWidget(self.main_window)

        self.login_window.stacked_widget = self.stacked_widget
        self.signup_window.stacked_widget = self.stacked_widget
        self.stacked_widget.main_window = self.main_window

        self.stacked_widget.show()


# ====================== RUN APPLICATION ======================
if __name__ == "__main__":
    server_thread = threading.Thread(target=MessengerServer().start, daemon=True)
    server_thread.start()

    app = MessengerApp(sys.argv)
    sys.exit(app.exec())
