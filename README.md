# SpendSense
Intelligent Behavioral Spending Trainer for Gauntlet AI.

## Overview
SpendSense transforms Plaid-style banking transaction data into explainable, consent-aware behavioral insights and personalized financial education. The system detects patterns, assigns personas, and delivers recommendations with clear rationales.

## Quick Start

### Prerequisites
- Python 3.9 or higher
- pip (Python package manager)

### Installation

1. **Clone the repository** (if not already done)
   ```bash
   cd SpendSense
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Setup database and generate synthetic data**
   ```bash
   python run.py --setup
   ```

   This will:
   - Create the SQLite database schema
   - Generate synthetic data for 50-100 users (configurable via `NUM_USERS` environment variable)
   - Store data in `data/spendsense.db`
   - Export analytics data to Parquet format in `data/parquet/`

### Configuration

You can configure data generation by setting environment variables:
- `NUM_USERS`: Number of users to generate (default: 75)
- `SEED`: Random seed for reproducibility (default: 42)

Example:
```bash
NUM_USERS=100 SEED=123 python run.py --setup
```

## Project Structure

```
SpendSense/
├── spendsense/              # Main package
│   ├── ingest/              # Data generation and loading
│   ├── storage/             # Database and Parquet handlers
│   ├── utils/               # Configuration and utilities
│   └── ...
├── data/                    # Generated data (SQLite + Parquet)
├── logs/                    # Application logs
├── docs/                    # Documentation
├── tests/                   # Test suite
├── requirements.txt         # Python dependencies
└── run.py                   # Setup and run script
```

## Running the Application

### Setup
```bash
# Install dependencies and setup database
python run.py --setup
```

### Start API Server
```bash
# Start the REST API server
python run.py --start
```

The API will be available at:
- **API Base URL:** http://localhost:8000
- **Interactive API Docs:** http://localhost:8000/docs
- **Alternative Docs:** http://localhost:8000/redoc

## API Documentation

### User Management Endpoints

- `POST /users` - Create a new user
- `POST /users/consent` - Record user consent
- `DELETE /users/consent/{user_id}` - Revoke consent
- `GET /users/consent/{user_id}` - Check consent status

### Data & Analysis Endpoints

- `GET /data/profile/{user_id}` - Get behavioral profile (signals, persona)
- `GET /data/recommendations/{user_id}` - Get recommendations
- `POST /data/feedback` - Submit feedback on recommendations

### Operator Endpoints

- `GET /operator/review` - Get approval queue
- `POST /operator/approve/{recommendation_id}` - Approve recommendation
- `POST /operator/override/{recommendation_id}` - Override recommendation
- `POST /operator/bulk_approve` - Bulk approve recommendations
- `GET /operator/analytics` - Get system analytics
- `GET /operator/feedback` - Get aggregated feedback

### Evaluation Endpoints

- `GET /eval/metrics` - Get evaluation metrics
- `POST /eval/run` - Trigger full evaluation run
- `GET /eval/fairness` - Get fairness analysis report

## Project Status

### ✅ Completed Phases

**Phase 1: Data Foundation**
- Database schema with SQLite and Parquet
- Synthetic data generator (100 users, 31,846 transactions)
- Data validation and ingestion

**Phase 2: Feature Engineering**
- 30-day and 180-day rolling windows
- Behavioral signal detection (subscriptions, savings, credit, income)
- Graceful degradation for new users
- Signal caching

**Phase 3: Persona System**
- 5 personas with prioritization logic
- Decision trace logging
- Signal strength tie-breaking

**Phase 4: Recommendation Engine**
- Education content catalog (5 items per persona)
- Dynamic partner offers with eligibility
- Rationale generation

**Phase 5: Guardrails & User UX**
- Consent management (opt-in/opt-out)
- Eligibility checks
- Tone validation
- Disclosure injection
- Feedback system

**Phase 6: Operator Dashboard**
- User review and search
- Approval queue management
- System analytics
- Feedback review
- Health monitoring

**Phase 7: Evaluation & Metrics**
- Automatic scoring (coverage, explainability, latency, auditability)
- User satisfaction metrics
- Fairness analysis (income quartiles, bias detection)
- Report generation (JSON, CSV, Markdown)

**Phase 8: API & Deployment**
- REST API with FastAPI
- All endpoints implemented (18 endpoints)
- Swagger UI for interactive testing
- Local-only deployment
- One-command setup and start

**Phase 9: Testing & Documentation**
- 30+ comprehensive tests (unit, integration, edge cases, performance)
- Schema documentation
- Evaluation results
- Testing guides
- Project summary

**Web UI (Frontend)**
- User-facing dashboard (HTML/CSS/JavaScript)
- Operator dashboard (HTML/CSS/JavaScript)
- API integration with REST endpoints
- Modern responsive design
- Accessible at http://localhost:8000/

### Testing

Run tests for each phase:
```bash
python3 test_phase2.py  # Feature Engineering
python3 test_phase3.py  # Persona System
python3 test_phase4.py  # Recommendation Engine
python3 test_phase5.py  # Guardrails & User UX
python3 test_phase6.py  # Operator Dashboard
python3 test_phase7.py  # Evaluation & Metrics
python3 test_end_to_end.py  # Full pipeline test
```

Test the API (requires server running):
```bash
python3 test_phase8.py
```

## Documentation

- [Product Requirements Document](SpendSense_PRD.md)
- [Architecture Document](SpendSense_Architecture.md)
- [Decision Log](SpendSense_Decision_Log.md)
- [Task List](SpendSense_Task_List.md)

## License

This project is for demonstration purposes.
