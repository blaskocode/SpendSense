# SpendSense System Patterns

## Architecture Overview
SpendSense follows a modular, pipeline-based architecture with clear separation of concerns:

```
Data Ingestion → Signal Detection → Persona Assignment → Recommendation Generation → Guardrails → User/Operator Interfaces
```

## Key Design Patterns

### 1. Modular Module Structure
Each major component is in its own module:
- `ingest/` - Data generation and loading
- `features/` - Feature engineering and signal detection
- `personas/` - Persona assignment logic
- `recommend/` - Recommendation engine
- `guardrails/` - Consent, eligibility, tone validation
- `ui/` - User feedback collection
- `operator/` - Operator dashboard backend
- `eval/` - Evaluation and metrics
- `api/` - REST API endpoints (FastAPI)
- `storage/` - Database and Parquet handlers
- `utils/` - Shared utilities
- `tests/` - Test suite (unit, integration, edge cases, performance)

### 2. Data Flow Pattern
1. **Ingestion:** Synthetic data → Validation → SQLite + Parquet
2. **Signal Detection:** Transactions → Window Partitioning → Signal Computation → Caching
3. **Persona Assignment:** Signals → Persona Matching → Prioritization → Selection
4. **Recommendation:** Persona → Education Catalog → Partner Offers → Rationale Generation
5. **Guardrails:** Recommendations → Consent Check → Eligibility Filter → Tone Validator → Output

### 3. Time Window Strategy
- **Rolling Windows:** Not fixed calendar months (fair for mid-month signups)
- **Dual Windows:** 30-day (recent behavior) + 180-day (long-term patterns)
- **Daily Recalculation:** At midnight UTC (not real-time)
- **Lookback Exclusion:** Exclude "today" (today-1 as end date) to avoid pending transactions

### 4. Persona Prioritization Pattern
- **Priority-Based:** 5 levels (1 = most urgent, 5 = growth)
- **Tie-Breaking:** Signal strength (sum of normalized signals) → Defined order
- **Single Assignment:** One primary persona per user
- **Decision Tracing:** Log all matching personas and selection rationale

### 5. Consent Model Pattern
- **All-or-Nothing:** Single boolean flag (simplicity)
- **Explicit Opt-In:** Required before any processing
- **Immediate Revocation:** Recommendations disappear instantly
- **Per-User Tracking:** Stored in database with timestamp

### 6. Guardrail Layering
```
Recommendations → Consent Check → Eligibility Filter → Tone Validator → Disclosure Injector → Output
```
Each guardrail is independent and can block recommendations.

### 7. Caching Strategy
- **Signal Cache:** Per user per window, 24-hour TTL
- **Cache Key Format:** `signals:{user_id}:{window_type}`
- **Invalidation:** New transactions trigger refresh
- **Storage:** SQLite `signals` table for persistence

### 8. Recommendation Structure
Every recommendation includes:
- **Type:** 'education' or 'offer'
- **Title:** Descriptive name
- **Rationale:** Plain-language "because" statement citing specific data
- **Persona:** Which persona this targets
- **Operator Status:** 'pending', 'approved', 'overridden'

### 9. Error Handling Pattern
- **Graceful Degradation:** System works even with limited data
- **Validation First:** Schema validation before database insertion
- **Custom Exceptions:** `SpendSenseError` hierarchy for different error types
- **Logging:** All errors logged with context

### 10. Database Schema Pattern
- **Foreign Keys:** Proper relational integrity
- **Indexes:** On frequently queried columns (user_id, date, account_id)
- **Timestamps:** Created/updated timestamps for auditability
- **JSON Fields:** Decision traces stored as JSON text

## Component Relationships

### Data Generation Flow
```
SyntheticDataGenerator → DataValidator → DataImporter → SQLiteManager → ParquetHandler
```

### Signal Detection Flow
```
Transaction Partitioner → Window Filter → Signal Computations → Signal Aggregator → Cache
```

### Persona Assignment Flow
```
Signals → Persona Criteria Matcher → Prioritization Engine → Tie-Breaker → Assignment Logger
```

### Recommendation Flow
```
Persona → Education Catalog → Partner Offers → Rationale Generator → Guardrails → Output
```

## Key Architectural Decisions

1. **Local-Only Deployment:** SQLite instead of PostgreSQL (simplifies setup)
2. **Synthetic Data:** No real Plaid integration (reproducibility, privacy)
3. **Rules-Based Baseline:** Explainable logic over ML black boxes
4. **Optional LLM:** Enhancement layer with static fallback
5. **Rolling Windows:** Fairness for users joining at different times
6. **Priority-Based Personas:** Safety-first approach (debt > stability > growth)
7. **Behavior-Only Fairness:** No demographic data, income quartiles from payroll
8. **All-or-Nothing Consent:** Simplicity over granularity

## Data Storage Patterns

### SQLite (Relational)
- Primary storage for all transactional data
- Foreign key relationships for integrity
- Indexed for query performance
- Used for: users, accounts, transactions, liabilities, signals, personas, recommendations, feedback

### Parquet (Analytics)
- Secondary storage for analytical workloads
- Columnar format for fast aggregations
- Used for: transactions, accounts, signals (exported from SQLite)

### JSON (Configs/Logs)
- Configuration files
- Decision traces (stored as JSON text in SQLite)
- Log files

## Testing Strategy Pattern
- **Unit Tests:** Individual signal computations, persona criteria, guardrails (15+ tests)
- **Integration Tests:** End-to-end flows, multi-module interactions (4 tests)
- **Edge Case Tests:** New users, zero balances, negative growth (4 tests)
- **Performance Tests:** Latency targets (<5 seconds per user) (2 tests)
- **Total:** 30+ tests covering all major components

## API Pattern
- **FastAPI Framework:** Modern, fast, auto-generated docs
- **RESTful Design:** Standard HTTP methods and status codes
- **Pydantic Models:** Type-safe request/response validation
- **Swagger UI:** Interactive documentation at `/docs`
- **Error Handling:** Global exception handler with JSON responses
- **CORS Enabled:** For local development and future frontend integration

## Code Organization Principles
- **Single Responsibility:** Each module has one clear purpose
- **Dependency Injection:** Database manager, parquet handler passed to components
- **Configuration Externalization:** Environment variables for settings
- **Logging Throughout:** All modules use structured logging
- **Error Handling:** Custom exceptions with meaningful messages

