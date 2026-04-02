# 🏦 Python Finance System Backend (FastAPI)
A robust, production-ready Python backend for personal finance tracking. This system allows users to manage financial records, analyze spending habits through automated summaries, and features a multi-tiered Role-Based Access Control (RBAC) system.

## 🚀 Key Features

-   **Financial Records Management:** Full CRUD operations for income and expense entries.
-   **Advanced Analytics:** Automated calculation of total income, expenses, current balance, and category-wise breakdowns.
-   **Granular RBAC (Role-Based Access Control):** -   **Admin:** Full system control (CRUD + User Management).
    -   **Analyst:** Data visualization and detailed insights (Read + Analytics).
    -   **Viewer:** Basic read-only access to records and balances.
-   **Data Validation:** Strict schema enforcement using Pydantic models.
-   **Security:** JWT-based authentication for secure session management.
-   **Auto-Documentation:** Interactive API documentation via Swagger UI.

## 🛠️ Technical Stack

-   **Framework:** [FastAPI](https://fastapi.tiangolo.com/) (High-performance, modern Python 3.10+)
-   **Database:** SQLite (Zero-config, file-based persistence)
-   **ORM:** SQLAlchemy (Object-Relational Mapping)
-   **Authentication:** Python-Jose (JWT Tokens) & Passlib (Bcrypt hashing)
-   **Environment:** Pydantic (Settings and Validation)

## Project Structure:

Root Directory

At the highest level, the project contains essential configuration and setup files:

main.py: Serves as the entry point for the FastAPI application, where the app is initialized and routers are connected.

seed_db.py: A utility script used to initialize the database schema and populate it with mock data and default user roles.

requirements.txt: Lists all external Python dependencies required to run the backend.

.env & .env.example: Manage environment-specific configurations like database URLs and security keys, keeping sensitive data out of the source code.

tests/: A dedicated directory for unit and integration tests to ensure system reliability.

README.md: Provides comprehensive documentation on how to set up, run, and test the project.

The app/ Core

The internal logic of the system is divided into functional layers within the app/ folder:

1. The Interface Layer (routers/)
   
This layer handles the API endpoints and HTTP communication:

auth.py: Manages user login and the issuance of JWT access tokens.

transactions.py: Handles CRUD operations (Create, Read, Update, Delete) for income and expense records.

summaries.py: Provides the endpoints for high-level financial analytics and balance totals.

users.py: Handles administrative tasks related to user account management.

2. The Business Logic Layer (services/)
   
This is the "brain" of the application where complex data processing happens, keeping the routers thin and readable:

summary_service.py: Contains the logic for calculating balances, category breakdowns, and financial insights.

transaction_service.py: Manages the logic for filtering records by date, type, or category.

user_service.py: Handles the underlying logic for creating users and assigning roles.

3. The Data & Security Layer
   
These files define how data is stored, validated, and secured:

models.py: Defines the database schema using SQLAlchemy ORM models.

schemas.py: Defines Pydantic models used for strict data validation and serializing API responses.

database.py: Manages the connection to the SQLite database and the lifecycle of database sessions.

security.py: Implements the cryptographic logic for password hashing (Bcrypt) and JWT handling.

dependencies.py: Contains the logic for Role-Based Access Control (RBAC), injecting user permissions directly into the API routes.

config.py: Loads and validates environment variables to ensure the application starts with the correct settings.


-   🏁 Getting Started
1. Prerequisites
Python 3.10 or higher

pip (Python package manager)

2. Installation
Clone the repository and install the dependencies:

pip install -r requirements.txt

3. Database Initialization (Important)
Run the seed script to create the SQLite database and populate it with mock users and transactions:

python seed_db.py

Note: This will print the default credentials for the Admin, Analyst, and Viewer accounts to your terminal.

4. Running the Server
Launch the FastAPI development server:

uvicorn app.main:app --reload


📖 API Documentation & Testing
Once the server is running, navigate to:

http://127.0.0.1:8000/docs


How to test Roles:
1. Use the POST /api/v1/auth/login endpoint with the seeded credentials.

2. Copy the access_token from the response.

3. Click the Authorize (lock) button at the top of the page.

4. Paste the token and click Authorize.

5. Test different endpoints (e.g., try deleting a record as a Viewer to see the 403 Forbidden response).


The email and password for different roles are as follows:
  viewer :  email - viewer@example.com and  password - ViewerPass123
  
  analyst : email - analyst@example.com and password - AnalystPass123
  
  admin :  email - admin@example.com and password - AdminPass123
