# 🏠 Rental House System (Data-Driven Web Application)

## Project Overview
This project is a full-stack web application designed to simulate a property rental platform. It was developed to demonstrate proficiency in data administration, advanced Python feature engineering, and full-stack development principles.

**Primary Technologies:** Python, Flask, SQLite, SQL, Jinja Templating, HTML/CSS.

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

## 🚀 How to Run the Project Locally

Follow these steps to set up and run the application on your local machine:

### Prerequisites
* [Python 3.x](https://www.python.org/downloads/)
* [Git](https://git-scm.com/downloads)

### Setup Instructions

1.  **Clone the Repository:**
    ```bash
    git clone [Your Repository URL Here]
    cd rental-house-system
    ```

2.  **Install Dependencies:**
    ```bash
    pip install flask werkzeug
    ```
    *(Note: We only need `flask` and `werkzeug` for security and running the app).*

3.  **Build the Database:**
    This command reads the `schema.sql` file and creates the `rental.db` file with initial users and properties.
    ```bash
    python database.py
    ```

4.  **Start the Server:**
    ```bash
    python app.py
    ```

5.  **Access the Application:**
    Open your browser and navigate to: `http://127.0.0.1:5000/`

### Testing Credentials (from schema.sql)
You can use these default accounts for initial testing:
* **Owner:** email: `eiden@owner.com` / password: `123456`
* **Renter:** email: `renter@test.com` / password: `7891011`

---
