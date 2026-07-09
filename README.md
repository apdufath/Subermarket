# Subermarket

Star Supermarket — Django store management system with inventory, orders, POS, and reporting.

## Setup
 
```bash 
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

## Sample data

```bash
python manage.py seed_sample_data --assign-images
```
