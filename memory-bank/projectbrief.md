# SpendSense Project Brief

## Project Overview
SpendSense is an intelligent behavioral spending trainer that transforms Plaid-style banking transaction data into explainable, consent-aware behavioral insights and personalized financial education. The system detects patterns, assigns personas, and delivers recommendations with clear rationales.

## Core Purpose
Transform raw banking transaction data into actionable, personalized financial insights that help users understand their spending behaviors and make informed decisions.

## Key Goals
1. **Explainable behavioral signal detection** - Every insight must be explainable with plain-language rationales
2. **Persona assignment** - Assign users to one of 5 priority-based personas based on their financial behavior
3. **Personalized financial education** - Deliver 3-5 educational content items tailored to each persona
4. **Dynamic partner offers** - Generate 1-3 eligible partner offers with clear eligibility criteria
5. **Comprehensive guardrails** - Consent, eligibility, and tone validation at every step
6. **Operator oversight** - Web-based dashboard for human review and approval
7. **User-facing dashboard** - Clean web interface for users to view insights and provide feedback
8. **AI-powered personalization** - Optional LLM-generated personalized financial plans and recommendations (user opt-in)

## Project Scope
- **Deployment:** Local-only (no cloud dependencies)
- **Data:** Synthetic dataset with 100 users (default, configurable)
- **Approach:** Modular, rules-based baseline with optional LLM enhancements (OpenAI GPT integration implemented)
- **Interfaces:** REST API + web-based operator dashboard + user web dashboard
- **AI Integration:** OpenAI GPT-4o-mini (recommended) for personalized financial plans (user opt-in only)

## Target Users
- **End Users:** Individuals with banking accounts seeking financial insights
- **Operators:** Financial advisors or platform operators reviewing and approving recommendations

## Success Criteria
- **Coverage:** 100% of users with assigned persona + ≥3 detected behaviors
- **Explainability:** 100% of recommendations with plain-language rationales
- **Latency:** <5 seconds per user recommendation generation
- **Auditability:** 100% of recommendations with decision traces
- **User Satisfaction:** >70% helpfulness score from feedback
- **Fairness:** No systematic bias across income levels (behavior-based only)

## Key Constraints
- No real Plaid integration (synthetic data only)
- Local deployment only (not production-ready)
- Educational content only (not regulated financial advice)
- Rules-based baseline (ML optional, not required)

## Timeline
Project is organized into 10 phases:
1. ✅ Data Foundation (COMPLETED)
2. ✅ Feature Engineering (COMPLETED)
3. ✅ Persona System (COMPLETED)
4. ✅ Recommendation Engine (COMPLETED)
5. ✅ Guardrails & User UX (COMPLETED - Full)
6. ✅ Operator Dashboard (COMPLETED - Full)
7. ✅ Evaluation & Metrics (COMPLETED)
8. ✅ API & Deployment (COMPLETED)
9. ✅ Testing & Documentation (COMPLETED)
10. ⏳ A/B Testing (Optional Enhancement - Not Started)

**Current Status:** Phases 1-9 Complete (90% of core project) ✅
- System is production-ready and fully operational
- REST API operational (18+ endpoints)
- Web UI dashboards fully implemented (user + operator)
- LLM-powered personalized financial plans (OpenAI GPT integration) ✅
- 30+ tests implemented
- Comprehensive documentation complete
- 100 users, 263 accounts, 31,846 transactions
- Latest evaluation: November 3, 2025

