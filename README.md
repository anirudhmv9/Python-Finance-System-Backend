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

Finance_System/
├── app/
│   ├── routers/            # API Route Controllers (End points)
│   │   ├── auth.py         # Login and JWT issuance
│   │   ├── transactions.py # Income/Expense CRUD logic
│   │   ├── summaries.py    # Analytics and totals endpoints
│   │   └── users.py        # Admin user management
│   ├── services/           # Core Business Logic (Processing Layer)
│   │   ├── summary_service.py     # Analytics and balance calculations
│   │   ├── transaction_service.py # Filtering and record management
│   │   └── user_service.py        # User creation and role logic
│   ├── models.py           # SQLAlchemy Database models
│   ├── schemas.py          # Pydantic models (Data validation & Serialization)
│   ├── dependencies.py     # Role-Based Access Control (RBAC) & Auth injectors
│   ├── security.py         # JWT, Bcrypt hashing, and password logic
│   ├── database.py         # SQLite connection and session management
│   ├── config.py           # Environment variable and settings loader
│   └── main.py             # FastAPI entry point & app initialization
├── tests/                  # Unit and integration test suite
├── seed_db.py              # Database initialization and mock data script
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables (DB URL, Secret Key)
├── .env.example            # Template for environment variables
└── README.md               # Project documentation



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
