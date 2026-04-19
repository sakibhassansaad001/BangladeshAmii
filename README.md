# 💰 Crowdfunding Platform

A modern web-based crowdfunding platform that enables users to create, manage, and support fundraising campaigns with transparency and real-time interaction.

---

## 🚀 Features

### 🔹 Module 1
- Campaign Creation (with admin approval)
- User Dashboard (campaigns, contributions, wishlist)
- Admin Moderation System
- Wishlist & Dark Mode

### 🔹 Module 2
- Media Gallery (image/video upload)
- Donation System (custom + quick amount + anonymous)
- Real-time Search with suggestions
- Discussion & Comment System (threaded replies, voting)

### 🔹 Module 3
- Progress Tracker (live funding updates)
- Category Filters & Tabs
- Contributor Visibility
- Notification System (donation, comment, approval)

---

## 🧑‍💻 Tech Stack

| Layer | Technology |
|------|----------|
| Backend | Flask (Python) |
| Frontend | HTML, CSS, JavaScript |
| Database | SQLite (SQLAlchemy ORM) |
| Authentication | Flask-Login |

---

## 🏗️ System Architecture

Client (Browser) → Flask Backend → SQLite Database

---

## 🔐 Key Functionalities

- Role-Based Access Control (Admin/User)
- Real-time notifications
- Secure data validation (backend enforced)
- Dark mode UI support

---

## 📂 Project Structure
project/
│── app.py
│── models.py
│── routes/
│── templates/
│── static/
│── database.db


---

## ⚙️ How It Works

1. Users register and log in
2. Create campaigns (pending approval)
3. Admin approves/rejects campaigns
4. Users donate and interact via comments
5. System updates progress and sends notifications

---

## 👥 Team Members

| Name | Role |
|------|------|
| Md. Sakib Hassan Saad | Backend Developer |
| Mehedi Hasan | Frontend Developer |
| Mostakim Al Billah Siam | System Logic & Admin Features |

---

## 📌 Future Enhancements

- Payment gateway integration
- Mobile application support
- AI-based fraud detection
- Advanced analytics dashboard

---

## 📄 License

This project is for academic purposes.

---

## ⭐ Acknowledgement

Developed as part of a Software Engineering / Academic Project.

---

Installation & Setup Guide


Step 1: Clone the Repository
git clone https://github.com/your-username/crowdfunding-platform.git
cd crowdfunding-platform

Step 2: Create Virtual Environment
python -m venv venv
Activate:
Windows
venv\Scripts\activate

Mac/Linux
source venv/bin/activate

Step 3: Install Dependencies
pip install -r requirements.txt

Step 4: Setup Database
python
>>> from app import db
>>> db.create_all()
>>> exit()

Step 5: Create Admin User
Run Python shell:

python

Then execute:

>>> from app import db
>>> from models import User
>>> from werkzeug.security import generate_password_hash

>>> admin = User(
>>> name="Admin",
>>> email="admin@gmail.com",
>>> password=generate_password_hash("admin123"),
>>> role="admin")
>>> 
>>> db.session.add(admin)
>>> db.session.commit()
>>> print("Admin user created successfully!")
>>> exit()

Step 6: Run the Application
python app.py

Step 7: Access the System
Open browser:
http://127.0.0.1:5000/

Admin Login Credentials
• Email: admin@gmail.com
• Password: admin1
