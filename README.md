# 🏠 Rental House System (Data-Driven Web Application)

## Project Overview
This project is a full-stack web application designed to simulate a property rental platform. It was developed to demonstrate proficiency in data administration, advanced Python feature engineering, and full-stack development principles.

**Primary Technologies:** Python, Flask, Flask-SQLAlchemy, SQLite, Jinja Templating, HTML/CSS.

---

## Key Features & Data Administration

This application is fully interactive and manages all data dynamically via an SQLite database.

| Category | Features Implemented | Data Administration Focus |
| :--- | :--- | :--- |
| **Authentication** | Register, Login, Logout, Session management. | Uses **Werkzeug Security** for hashed password storage. |
| **User Roles** | Renter and Owner roles with restricted access. | Owner has **CRUD** access to their listings. |
| **Core Features** | Homepage with dynamic property listings. | SQL queries optimized for search and retrieval. |
| **Feature Engineering**| **Dynamic Search** filtering by city. **Price Calculation** of total booking cost based on dates. | Implemented custom Jinja filters for date and currency formatting. |
| **Admin Reports** | **Owner Dashboard** calculates and displays **Total Revenue** from all listed properties. | SUM() aggregation in SQL for financial reporting. |
| **CRUD** | Owners can **C**reate, **R**ead, **U**pdate, and **D**elete their specific property listings. | Implemented security checks to ensure owners only modify their own data. |

---

## 🗂️ Project Structure

The application is split into focused modules rather than a single monolithic file:

| File | Responsibility |
| :--- | :--- |
| `app.py` | Flask app factory, routes, Jinja filters. |
| `models.py` | SQLAlchemy models (`User`, `Property`, `Booking`). |
| `decorators.py` | Route guards (`login_required`, `owner_required`). |
| `database.py` | Builds `rental.db` from `schema.sql` with seed data. |
| `test_app.py` | Pytest suite covering auth and core routes. |

---

## 🚀 How to Run the Project Locally

Follow these steps to set up and run the application on your local machine:

### Prerequisites
* [Python 3.x](https://www.python.org/downloads/)
* [Git](https://git-scm.com/downloads)

### Setup Instructions

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/EidenWilson/Rental-house-system.git
    cd Rental-house-system
    ```

2.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure Environment Variables (optional but recommended):**
    Create a `.env` file in the project root to set a real secret key:
    ```
    SECRET_KEY=your-own-secret-key
    ```
    If omitted, a development-only fallback key is used.

4.  **Build the Database:**
    This command reads the `schema.sql` file and creates the `rental.db` file with initial users and properties.
    ```bash
    python database.py
    ```

5.  **Start the Server:**
    ```bash
    python app.py
    ```

6.  **Access the Application:**
    Open your browser and navigate to: `http://127.0.0.1:5000/`

### Running Tests

The project includes a Pytest suite covering authentication and core routes:
```bash
pytest
```

### Testing Credentials (from schema.sql)
You can use these default accounts for initial testing:
* **Owner:** email: `eiden@owner.com` / password: `123456`
* **Renter:** email: `renter@test.com` / password: `7891011`

---
