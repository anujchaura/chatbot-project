# Softwallet Chatbot System

A full-stack AI chatbot system with lead capture, scraping, and admin analytics dashboard, developed for Softwallet Innovative Technologies.

---

## Features

* Interactive chatbot interface
* Lead capture system (Name, Email, Phone)
* Admin dashboard for leads and analytics
* Web scraping functionality
* Responsive UI with dark/light mode

---

## Project Structure

```id="k9x2zm"
project/
│
├── Backend/
│   ├── main.py
│   ├── chatbot.db
│   ├── leads.txt
│   ├── requirements.txt
│   └── chromedriver.exe
│
├── Frontend/
│   ├── index.html
│   └── admin.html
│
├── .gitignore
└── README.md
```

---

## Tech Stack

* Frontend: HTML, CSS, JavaScript
* Backend: FastAPI (Python)
* Database: SQLite
* Scraping: Selenium

---

## How to Run Locally

### 1. Clone the repository

```id="j4w8pt"
git clone https://github.com/your-username/your-repo.git
cd your-repo
```

### 2. Setup backend

```id="v2m7qd"
cd Backend
pip install -r requirements.txt
python main.py
```

### 3. Run frontend

* Open `Frontend/index.html` in browser
* Admin panel: `Frontend/admin.html`

---

## Notes

* Do not push `.db`, `.venv`, or `chromedriver.exe`
* SQLite is not recommended for production

---

## Future Improvements

* Use PostgreSQL (Supabase)
* Enhance chatbot AI capabilities
* Add authentication to admin panel

---

## Author

Developed by Anuj
Softwallet Innovative Technologies
