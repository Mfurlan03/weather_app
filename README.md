# Weather App – Tech Assessment 1 & 2
**Author:** Michael Furlano  
**AI/ML/GenAI Engineer Intern Technical Assessment**

---

## Overview

This project includes both parts of the PM Accelerator Weather App assessments.

- **Tech Assessment 1:** focuses on user input, live API integration, and real-time weather display.  
- **Tech Assessment 2:** extends the app with full CRUD functionality, database persistence, validation, and export options.

Together, these apps demonstrate my ability to combine backend logic, API data handling, validation, and a simple user-friendly interface to create a functional, data-driven web application.

---

## How to Run

### 1. Pick an assessment folder
```bash
cd weather_app_q1   # Tech Assessment 1 (live weather)
# or
cd weather_app_q2   # Tech Assessment 2 (CRUD, persistence, export)
```

### 2. (Optional) Create a virtual environment
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the app
```bash
# Windows PowerShell
$Env:FLASK_APP="app.py"
$Env:FLASK_ENV="development"
flask run
```
Then open **http://127.0.0.1:5000** in your browser.

---

## Tech Assessment 1 – Core Weather App

This version lets users:
- Enter a **city, landmark, postal code, or coordinates** to get live weather data.  
- View **current conditions** and a **5-day forecast**.  
- Use the browser’s **current location** to automatically detect weather.

I used the **Open-Meteo API** for weather data and geocoding, so no API keys are needed.  
This first version focuses on simplicity, clear input validation, and an accessible interface.

---

## Tech Assessment 2 – Advanced Version

For the advanced portion, I added:
- **CRUD features** with an SQLite database (via SQLAlchemy).  
- **Saved locations** that users can rename, view, or delete.  
- **Historical weather requests** with start/end dates, validated and stored for later reference.  
- **Data export** in multiple formats (JSON, CSV, Markdown).  
- **Map and YouTube integration** for extra context on each location.  
- **Input validation** using Pydantic to ensure coordinates, date ranges, and names are valid.

This version highlights my ability to implement persistence, structured validation, API design, and user interaction while maintaining a clean and readable codebase.

---

## Why I Built It This Way

I designed both parts to demonstrate:
- **Practical API integration** with real, external data.  
- **Robust validation** and user-friendly error handling.  
- **Clean structure** using Flask blueprints, modular files, and readable code.  
- **Simple, functional UI** that clearly communicates results and actions.
