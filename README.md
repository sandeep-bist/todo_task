# To-Do List Application

REST API + Web UI using Django (no ORM, raw SQL)

## Setup

1. Clone repo
2. `python -m venv venv && source venv/bin/activate`
3. `pip install -r requirements.txt`
4. `python manage.py migrate`  (even though no models — creates django sessions etc.)
5. `python manage.py runserver`

## API Endpoints

- GET /api/tasks/ → List tasks
- POST /api/tasks/ → Create task  
  ```json
  {"title": "Buy milk", "description": "...", "due_date": "2026-03-10", "status": "pending"}