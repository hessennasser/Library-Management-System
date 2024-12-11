# Library Management System

A Flask-based Library Management System with features for both administrators and customers.

## Features

- User Authentication (Login/Register)
- Role-based access control (Admin/Customer)
- Book management
- Author management
- Library card system
- Book checkout and return functionality

## Setup Instructions

1. Create a virtual environment:
```bash
python -m venv venv
```

2. Activate the virtual environment:
```bash
# On Windows
venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the application:
```bash
python app.py
```

5. Access the application at `http://localhost:5000`

## Initial Setup

The first user needs to be manually set as an admin in the database. You can do this by:
1. Register a new user through the web interface
2. Access the SQLite database (library.db) using a SQLite browser
3. Set the `is_admin` field to `True` for the desired user

## Usage

### Admin Features
- Add new books
- Add authors
- Issue library cards to users
- View all users and their status

### Customer Features
- View available books
- Checkout books (requires library card)
- Return books
- View checkout history

## Database Schema

- Users: Stores user information and authentication details
- Books: Stores book information and availability status
- Authors: Stores author information
- Relationships: Books can be checked out by users with valid library cards
