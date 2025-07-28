#Demonstration video link - https://drive.google.com/file/d/1AiDf8UNUZPsZdJp0wFGnEedjbDxmYMi9/view?usp=sharing

# 🚗 Vehicle Parking App - V1

A web-based vehicle parking management system built with **Flask**, **SQLite**, **Bootstrap**, and **Chart.js** that allows users to search, book, and manage parking lots, while giving administrators powerful tools to control availability, pricing, and statistics.

---

## 📌 Features

### 👤 User Side
- 🔍 **Search Parking Lots** by location or area
- 📊 **Filter and Sort** by availability and price
- 🖼️ **View Images** of parking lots
- 📅 **Book a Parking Spot** in real time
- 🧾 **View Booking History**
- 📈 **Dashboard Charts** showing usage stats
- 🔐 Secure **User Registration** and **Login** with bcrypt

### 🛠️ Admin Side
- ➕ **Add New Parking Lots** with:
  - Location
  - Price per hour
  - Number of available spots
  - Parking image (stored in `/static/uploads`)
- 📷 Upload images tagged by lot ID (e.g. `lot_5.png`)
- 📦 **Dashboard with Charts**:
  - Bookings per lot (Bar chart)
  - Duration distribution (Pie chart)
  - Daily spending trends (Line chart with shaded area)
- 📃 **Full control over lot management**

---

## 🗃️ Tech Stack

| Layer       | Tech Stack                 |
|-------------|----------------------------|
| Backend     | Flask (Python)             |
| Frontend    | HTML, Bootstrap 5, JS      |
| Charts      | Chart.js                   |
| Database    | SQLite                     |
| Auth        | Flask `session` + bcrypt   |
| File Upload | Stored in `/static/uploads/` |

---

## 🧱 Project Structure
<pre>
24F2008369/
├── controllers/                # Flask Blueprints / Route Controllers
│   ├── admin_controller.py
│   ├── api_controller.py
│   ├── auth_controller.py
│   └── user_controller.py
│
├── data/                       # Static data (e.g. JSON, mock credentials)
│   └── admin_credentials.json
│
├── models/                     # Database models & SQLite DB files
│   ├── model.py
│   ├── Parking.db
│   └── Sample.db
│
├── static/                     # Static frontend assets
│   ├── css/
│   ├── images/
│   ├── scripts/
│   └── uploads/
│
├── templates/                  # Jinja2 HTML Templates
│   └── HTML files are here
│
├── app.py                      # Main application entry point
├── extensions.py               # Flask extensions like Bcrypt, etc.
├── init.py                     # Script to install requirements
├── requirements.txt            # Python dependencies
├── README.md                   # Project overview
└── example.txt                 # Example data / temp file

