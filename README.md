# AP-Messenger-Project

## 📦 Project Structure

```
messenger_project/
├── client.py            # GUI client app
├── server.py            # Socket server
├── models.py            # SQLAlchemy DB models
├── threads.py           # Client-side listener thread
├── utils.py             # (optional helper utilities)
├── db.sqlite3           # SQLite database file
├── assets/
│   ├── bg_main.jpg      # Main background image (optional)
│   ├── bg_login.jpg     # Login screen background (optional)
│   └── default_profile.jpg  # Default profile picture
└── README.md            # Setup instructions
```

## ⚙️ Requirements

- Python 3.10+
- PyQt6
- SQLAlchemy

Install with:
```bash
pip install PyQt6 SQLAlchemy
```

## 🚀 How to Run

1. Clone or download this project directory.
2. Launch the server:
   ```bash
   python server.py
   ```
3. In a separate terminal (or on another machine), launch the client:
   ```bash
   python client.py
   ```

> ⚠ Make sure `server.py` is running before opening any clients.

## ✅ Features

- User SignUp / Login
- Live messaging (multithreaded)
- File sharing: `.pdf`, `.jpg`, `.mp4`, `.zip`, etc
- Send GIFs, Stickers (images), Voice messages (`.mp3`, `.wav`)
- Profile picture upload
- SQLite-based user/message database

## 🛠 Notes
- Default profile images and backgrounds are optional.
- Supports LAN/WiFi local communication. WAN requires port forwarding.

## 📷 Assets Usage
Put images like `bg_main.jpg` and `default_profile.jpg` in `assets/` folder. These are used in the GUI layout.

## 🔒 Security
This version uses password hashing but does not encrypt network traffic. For production, add SSL and message encryption.

---
Created for university project — Advanced Programming (Python + PyQt6)
