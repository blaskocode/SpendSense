# SpendSense Technical Context

## Technology Stack

### Backend
- **Language:** Python 3.9+
- **Framework:** FastAPI (implemented) ✅
- **Database:** SQLite (built-in, no external dependency) ✅
- **Analytics Storage:** Parquet (via PyArrow) ✅
- **Data Processing:** Pandas, NumPy ✅

### Frontend ✅ Implemented
- **Framework:** Vanilla HTML, CSS, and JavaScript (no framework dependencies)
- **Purpose:** User-facing dashboard and operator dashboard
- **Status:** ✅ Fully implemented and operational
- **Files:**
  - `web/static/index.html` - User dashboard
  - `web/static/app.js` - User dashboard logic
  - `web/static/style.css` - User dashboard styles
  - `web/static/operator.html` - Operator dashboard
  - `web/static/operator.js` - Operator dashboard logic
  - `web/static/operator.css` - Operator dashboard styles
- **Features:**
  - Consent management UI
  - Personalized recommendations display
  - Behavioral insights visualization
  - Active subscriptions display with statistics
  - Transaction records with pagination and search
  - Date range filtering (default: past 6 months)
  - Feedback collection
  - Operator dashboard with tabs for analytics, approval queue, etc.
- **Alternative:** Swagger UI also available for testing at `/docs`

### LLM Integration (Planned) 📋
- **Provider:** OpenAI GPT (GPT-4 or GPT-3.5-turbo)
- **Status:** Plan created, ready for implementation
- **Opt-In:** User must explicitly consent to AI features (separate from data consent)
- **Dependency:** `openai>=1.0.0` (to be added to requirements.txt)
- **Configuration:** API key, model selection, timeout, temperature via environment variables
- **Features:**
  - Generate complete personalized financial plan documents
  - Generate personalized recommendations (education + offers)
  - Fallback to static catalog on failure
  - Error messaging with graceful degradation

### Optional Components
- **Local LLM:** Could use local models (Ollama, etc.) as alternative in future

## Development Setup

### Prerequisites
- Python 3.9 or higher
- pip (Python package manager)

### Installation
```bash
pip install -r requirements.txt
```

### Dependencies (requirements.txt)
- `pandas>=2.0.0` - Data processing
- `numpy>=1.24.0` - Numerical operations
- `pyarrow>=12.0.0` - Parquet support
- `fastapi>=0.104.0` - API framework ✅ (implemented)
- `uvicorn>=0.24.0` - ASGI server ✅ (implemented)
- `python-dateutil>=2.8.2` - Date utilities
- `pytest>=7.4.0` - Testing framework
- `pytest-cov>=4.1.0` - Test coverage
- `synthetic-data` - Capital One synthetic data library (for data generation)
- `openai>=1.0.0` - OpenAI API client (planned for LLM integration) 📋

## Project Structure

```
SpendSense/
├── spendsense/              # Main package
│   ├── ingest/              # Data generation and loading
│   │   ├── data_generator.py
│   │   ├── loader.py
│   │   ├── validator.py
│   │   └── importer.py
│   ├── storage/             # Database and Parquet handlers
│   │   ├── sqlite_manager.py
│   │   └── parquet_handler.py
│   ├── features/            # Feature engineering (Phase 2) ✅
│   ├── personas/            # Persona system (Phase 3) ✅
│   ├── recommend/           # Recommendation engine (Phase 4) ✅
│   ├── guardrails/          # Guardrails (Phase 5) ✅
│   ├── ui/                  # User feedback (Phase 5) ✅
│   ├── operator/            # Operator dashboard (Phase 6) ✅
│   ├── eval/                # Evaluation (Phase 7) ✅
│   ├── api/                 # REST API (Phase 8) ✅
│   ├── utils/               # Utilities
│   │   ├── config.py
│   │   ├── logger.py
│   │   └── errors.py
│   └── tests/               # Test suite
│       ├── unit/
│       ├── integration/
│       └── edge_cases/
├── data/                    # Generated data
│   ├── spendsense.db        # SQLite database
│   └── parquet/             # Parquet files
├── logs/                     # Application logs
├── memory-bank/             # Memory bank documentation
├── requirements.txt        # Python dependencies
├── run.py                   # Setup and run script
└── README.md                # Project documentation
```

## Configuration

### Environment Variables
- `NUM_USERS` - Number of synthetic users to generate (default: 75)
- `SEED` - Random seed for reproducibility (default: 42)

### Configuration Files
- `spendsense/utils/config.py` - Centralized configuration
- Database paths, parquet paths, logging setup

## Database Schema

### SQLite Tables
1. **users** - User accounts with consent tracking
2. **accounts** - Banking accounts (checking, savings, credit, etc.)
3. **transactions** - All financial transactions
4. **liabilities** - Credit card liabilities, loans
5. **signals** - Cached behavioral signals
6. **personas** - Persona assignments with decision traces
7. **recommendations** - Generated recommendations
8. **feedback** - User feedback on recommendations

### Indexes
- `transactions(account_id, date)` - Query optimization
- `transactions(date)` - Window queries
- `accounts(user_id)` - User account lookup
- `signals(user_id, window_type)` - Signal retrieval
- `personas(user_id)` - Persona lookup
- `recommendations(user_id)` - User recommendations

## Data Generation

### Synthetic Data Characteristics
- **Users:** 100 (default, configurable via NUM_USERS)
- **Data Library:** Capital One `synthetic-data` library for statistically robust generation
- **Income Distribution:** 4 quartiles (Q1: $20-40k, Q2: $40-65k, Q3: $65-100k, Q4: $100-200k)
- **Account Types:** Checking, Savings, Credit Card, Money Market, HSA
- **Transaction History:** 210 days (180 + 30 day buffer)
- **Realistic Variability:** Subscriptions, seasonality, life events, edge cases
- **Current Data:** 100 users, 263 accounts, 31,846 transactions

### Reproducibility
- Deterministic random seed (default: 42)
- All randomness seeded for consistent results
- Same seed produces identical data
- Capital One library uses NumPy random generator for better statistical distribution

## Development Constraints

### Local-Only Deployment
- No cloud dependencies
- SQLite instead of PostgreSQL/MySQL
- Local file storage instead of S3
- No external authentication (basic operator auth only)

### No Real Integrations
- Synthetic data only (no real Plaid API)
- No real credit checks or income verification
- Educational content only (not financial advice)

## API Design ✅ Implemented

### REST Endpoints Structure (18+ endpoints)
- `/users` - User management (POST, GET)
- `/users/consent` - Consent operations (POST, DELETE, GET)
- `/data/profile/{user_id}` - Behavioral profile (GET)
- `/data/recommendations/{user_id}` - Recommendations (GET)
- `/data/transactions/{user_id}` - Transaction records (GET) with date filtering
- `/data/subscriptions/{user_id}` - Active subscriptions (GET)
- `/data/feedback` - User feedback (POST)
- `/operator/*` - Operator dashboard endpoints (6 endpoints)
- `/eval/*` - Evaluation endpoints (3 endpoints)
- `/` - User dashboard (serves index.html)
- `/operator-dashboard` - Operator dashboard (serves operator.html)

### API Implementation
- ✅ FastAPI framework with automatic OpenAPI docs
- ✅ Swagger UI at `/docs` for interactive testing
- ✅ Pydantic models for type-safe validation
- ✅ RESTful resource-oriented design
- ✅ Stateless (no server-side sessions)
- ✅ JSON request/response format
- ✅ Standard HTTP methods (GET, POST, DELETE)
- ✅ Global error handling
- ✅ CORS enabled for local development
- ✅ Static file serving for web UI
- ✅ Date filtering support for transaction queries
- ✅ Transaction pagination support
- ✅ Subscription aggregation endpoint

## Testing Setup

### Test Framework
- **pytest** - Test runner
- **pytest-cov** - Coverage reporting

### Test Structure
- **Unit Tests:** Individual function/class tests
- **Integration Tests:** Multi-module workflow tests
- **Edge Case Tests:** Boundary conditions
- **Performance Tests:** Latency validation

### Test Coverage ✅
- ✅ 30+ total tests collected
- ✅ 15+ unit tests
- ✅ 4 integration tests
- ✅ 4 edge case tests
- ✅ 2 performance tests
- ✅ Test suite in `spendsense/tests/`

## Logging

### Logging Setup
- File-based logging in `logs/` directory
- Console output for development
- Structured format with timestamps
- Per-module loggers

### Log Levels
- INFO - Normal operations
- WARNING - Non-critical issues
- ERROR - Errors requiring attention
- DEBUG - Detailed debugging (when needed)

## Deployment

### Local Setup
```bash
python run.py --setup  # Initialize database and generate data ✅
python run.py --start  # Start API server ✅
```

### Single-Command Setup ✅
- ✅ Creates database schema
- ✅ Generates synthetic data (100 users, 31,846 transactions)
- ✅ Exports to Parquet
- ✅ Starts REST API server on http://localhost:8000
- ✅ Swagger UI available at http://localhost:8000/docs

## Performance Targets
- **Latency:** <5 seconds per user recommendation generation
- **Database:** Indexed queries for fast lookups
- **Caching:** 24-hour TTL for signal cache
- **Batch Processing:** Daily window recalculation (not real-time)

## Known Limitations
- SQLite not suitable for high concurrency (local-only acceptable)
- No real-time updates (daily recalculation)
- Synthetic data may not cover all real-world edge cases
- Local deployment only (not scalable to production)

