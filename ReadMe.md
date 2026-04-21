# AgriSmart - Smart Crop Management System

A Smart Crop Management System built using Python (Flask), SQLite, and vanilla HTML/CSS/JS.

## Prerequisites

- Python 3.8+

## Setup Instructions

1. Create a virtual environment (optional but recommended):
   ```bash
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On macOS/Linux
   source venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Seed the database:
   ```bash
   python seed.py
   ```

4. Run the application:
   ```bash
   python app.py
   ```

5. Open your browser and navigate to `http://127.0.0.1:5000`.

## Features
- User registration and login flow.
- Add new crops and track their growth progress.
- Log activities like fertilizing, watering, and harvesting.
- Financial reporting and dashboard metrics.
