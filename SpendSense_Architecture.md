# SpendSense Architecture

```mermaid
flowchart TD
    %% User Data Ingestion
    A[User Synthetic Data (50-100 users)] -->|Ingest CSV/JSON| B[Data Ingestion Module]
    B --> C[SQLite / Parquet Storage]

    %% Windowed Feature Extraction
    C --> D[Partition Transactions by Time Window]
    D --> D30[30-Day Window]
    D --> D180[180-Day Window]

    %% Signal Computation
    D30 --> E1[Behavioral Signals: Subscriptions, Savings, Credit, Income Stability]
    D180 --> E2[Behavioral Signals: Subscriptions, Savings, Credit, Income Stability]

    %% Persona Assignment
    E1 --> F[Persona Assignment Module]
    E2 --> F
    F --> G[Primary Persona per User]

    %% Recommendation Generation
    G --> H[Recommendation Engine]
    H --> I[Education Content (Catalog + optional LLM)]
    H --> J[Dynamic Partner Offers]
    I --> K[Recommendations with Rationale]
    J --> K

    %% Guardrails
    L[Consent & Eligibility & Tone Checks] --> K
    M[User Revokes Consent] --> L

    %% Operator Dashboard
    K --> N[Operator Dashboard]
    C --> N
    N -->|Approve/Override| K

    %% Evaluation & Metrics
    K --> O[Evaluation Module]
    O --> P[Metrics JSON/CSV + Charts/Graphs]

    %% REST API
    Q[REST API Endpoints] --> B
    Q --> D
    Q --> F
    Q --> H
    Q --> L
    Q --> N

    %% Notes
    classDef windows fill:#f9f,stroke:#333,stroke-width:1px;
    class D30,D180 windows;
