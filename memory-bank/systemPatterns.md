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
ProfileBasedGenerator (default) → DataValidator → DataImporter → SQLiteManager → ParquetHandler
     ↓
PersonaProfiles (templates) → Profile Variations (20 per persona) → Transaction Generation
     ↓
Account-Appropriate Transactions (HSA only healthcare, no duplicate subscriptions)
```

**Alternative Flow (fallback):**
```
CapitalOneDataGenerator → DataValidator → DataImporter → SQLiteManager → ParquetHandler
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
Persona → [AI Consent Check] → [If AI: LLM Generator → Plan Document + Recommendations] 
         → [If No AI or AI Failed: Static Catalog] 
         → Education Catalog → Partner Offers → Rationale Generator → Guardrails → Output
```

## Key Architectural Decisions

1. **Local-Only Deployment:** SQLite instead of PostgreSQL (simplifies setup)
2. **Synthetic Data:** No real Plaid integration (reproducibility, privacy)
3. **Profile-Based Generation:** Persona-driven realistic data (default since November 2025)
   - Ensures account-appropriate transactions
   - Prevents unrealistic patterns (e.g., Netflix from HSA)
   - No duplicate subscriptions in same month
   - Realistic recurring payment dates
4. **Rules-Based Baseline:** Explainable logic over ML black boxes
5. **Optional LLM:** Enhancement layer with static fallback
6. **Rolling Windows:** Fairness for users joining at different times
7. **Priority-Based Personas:** Safety-first approach (debt > stability > growth)
8. **Behavior-Only Fairness:** No demographic data, income quartiles from payroll
9. **All-or-Nothing Consent:** Simplicity over granularity

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
- **CORS Enabled:** For local development and frontend integration ✅
- **Static File Serving:** Serves web UI files from `web/static/` directory
- **Date Filtering:** Transaction endpoints support `start_date` and `end_date` query parameters

## Web UI Pattern
- **Vanilla HTML/CSS/JavaScript:** No framework dependencies, simple and fast
- **API Integration:** All UI interactions use REST API endpoints
- **Auto-Detection:** `API_BASE_URL` uses `window.location.origin` for flexible deployment
- **Client-Side Filtering:** Transaction search filters loaded data client-side for responsiveness
- **Background Loading:** All transactions in date range loaded in background for instant search
- **Date Range Management:** Default to past 6 months, user-adjustable with reset button
- **Deduplication:** Recommendations deduplicated by title before display
- **Pagination:** Transactions displayed in pages (20 per page) with navigation controls
- **Expandable Details:** Transaction rows expand to show full details

## LLM Integration Pattern ✅ FULLY OPERATIONAL
- **Opt-In Only:** AI features require explicit user consent (separate from data consent) ✅
- **Fallback Strategy:** Static catalog used when LLM fails/timeouts (validated in production) ✅
- **Structured Output:** JSON format for LLM responses (plan document + recommendations) ✅
- **Error Handling:** User-visible errors when LLM fails, system continues with fallback ✅
- **Auditability:** Store AI-generated plans in database with full metadata ✅
- **Prompt Engineering:** Persona-specific prompts with rich user data context ✅
- **Token Tracking:** Monitor API usage for cost management ✅
- **Model Selection:** GPT-4o-mini (default, fastest, most cost-effective, proven in production)
- **Temperature:** 0.3 (default) for consistent, factual financial advice
- **Configuration:** Environment variables via .env file (python-dotenv integration)
- **Database Schema:** Complete AI consent tracking in users table + ai_plans table
- **Performance:** <5s generation time, meeting all latency targets
- **Status:** Production-ready and fully tested

## Code Organization Principles
- **Single Responsibility:** Each module has one clear purpose
- **Dependency Injection:** Database manager, parquet handler passed to components
- **Configuration Externalization:** Environment variables for settings
- **Logging Throughout:** All modules use structured logging
- **Error Handling:** Custom exceptions with meaningful messages

## Data Generation Patterns (Updated November 2025)

### Profile-Based Generation Pattern
1. **Profile Templates:** Base profiles defined in `persona_profiles.py`
   - Each persona has 1-2 base templates
   - Templates define: income, accounts, recurring payments, spending patterns
2. **Variation Generation:** Creates 20 variations per persona
   - Income varies within quartile
   - Merchant names vary (e.g., "Electric Company" vs "Power Company")
   - Amounts vary slightly (±5-10%)
   - Dates vary with jitter (subscriptions stay fixed)
3. **Transaction Generation:** From profiles to transactions
   - Payroll deposits based on frequency
   - Recurring payments on fixed days (rent 1st, subscriptions specific days)
   - Variable spending distributed across date range
   - Account-appropriate routing (HSA only healthcare)
4. **Quality Assurance:**
   - No duplicate subscriptions per user per month
   - Account type validation (HSA transactions must be healthcare)
   - Realistic payment dates and amounts

