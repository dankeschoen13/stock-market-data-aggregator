# Market Data Aggregator & ETL Pipeline

A robust, headless data engineering pipeline built with Flask and PostgreSQL. This application extracts daily stock market data from the Financial Modeling Prep (FMP) API, transforms it using Pandas, and loads it into a relational database using highly optimized, idempotent SQL operations. 

The architecture is built around the **Thin Controller** and **Service Layer** patterns, completely decoupling the extraction logic, database transactions, and CLI orchestration.

## 🚀 Tech Stack
* **Framework:** Python, Flask
* **Database:** PostgreSQL, SQLAlchemy (ORM & Core), Flask-Migrate
* **Data Transformation:** Pandas, NumPy
* **CLI Orchestration:** Click (Flask CLI)
* **External API:** Financial Modeling Prep (FMP)

## ✨ Key Features
* **Custom CLI Tooling:** Fully integrated terminal commands to manage the pipeline without requiring a web interface.
* **Idempotent Bulk Inserts:** Utilizes PostgreSQL-native `ON CONFLICT DO NOTHING` statements to safely ignore duplicates during batch jobs without poisoning the SQLAlchemy session.
* **Service Layer Architecture:** * `TickerSvc`: Manages the configuration watchlist of active stocks.
  * `MktDataSvc`: Handles complex database Upserts and heavy Pandas transformations.
* **Fail-Fast Loop Handling:** The ETL loop gracefully catches targeted `SQLAlchemyError` and network exceptions, logging localized errors without halting the entire batch process.

## 🛠️ Setup and Installation

### 1. Clone the repository and install dependencies
```bash
git clone [https://github.com/dankeschoen13/stock-market-data-aggregator.git](https://github.com/dankeschoen13/stock-market-data-aggregator.git)
cd stock-market-data-aggregator
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
pip install -r requirements.txt
```

### 2. Environment Variables
Create a `.env` file in the root directory and add your configuration details:
```env
FLASK_APP=run.py
FLASK_ENV=development
DATABASE_URL=postgresql://user:password@localhost:5432/market_data_db
FMP_KEY=your_financial_modeling_prep_api_key
```

### 3. Initialize the Database
Ensure PostgreSQL is running locally, then apply the migrations:
```bash
flask db upgrade
```

## 💻 CLI Commands

The application is controlled via custom Flask CLI commands designed to manage the data warehouse dynamically.

### Seed the Configuration Watchlist
Populates the `TrackedTicker` database with an initial batch of highly liquid S&P 500 stocks. 
```bash
flask seed-tickers
```
*Note: This command is idempotent. Running it multiple times is perfectly safe and will only insert missing tickers.*

### Run the Main ETL Pipeline
Orchestrates the Extract, Transform, and Load process for all currently active tickers in the database.
```bash
flask get-stock-data
```
**Execution Flow:**
1. Dynamically fetches all active tickers from the database.
2. Extracts the latest market data via the FMP API.
3. Transforms the JSON payload into a structured Pandas DataFrame (mapping `symbol` to `ticker` and calculating technicals like `rsi_14`).
4. Loads the clean data into the PostgreSQL `Stock` table.

## 🏗️ Project Structure
```text
├── app/
│   ├── cli/
│   │   ├── __init__.py         
│   │   └── cli.py               # Custom Click commands (ETL orchestration & seed tasks)
│   ├── models/
│   │   ├── __init__.py         
│   │   └── models.py            # SQLAlchemy database models and schema definitions
│   ├── routes/
│   │   ├── __init__.py         
│   │   └── main.py              # Flask API endpoints and web route controllers
│   ├── services/
│   │   ├── __init__.py         
│   │   ├── extract.py           # External HTTP requests (FMP API extraction logic)
│   │   └── service.py           # Business logic, Pandas transformations, and DB transactions
│   ├── __init__.py              # App factory and dynamic route/CLI registration
│   ├── constants.py             # Static variables, configuration lists, and global constants
│   └── extensions.py            # Flask extensions initialization (e.g., db, migrate)
├── migrations/                  # Alembic database revisions
├── wsgi.py                      # Application entry point (Development/Production server)
├── requirements.txt             # Project Python dependencies
└── .env                         # Environment variables and sensitive API keys
```