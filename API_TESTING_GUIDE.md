# SpendSense API Testing Guide

While command-line tools are available, you can also test SpendSense through the REST API using HTTP requests.

## Current Options

### 1. Command-Line Tools (Current)
- ✅ `user_view.py` - Simulate user dashboard
- ✅ `interactive_test.py` - Menu-driven interface
- ✅ `user_testing_scenarios.py` - Automated scenarios

### 2. REST API (Available)
- ✅ HTTP endpoints accessible via browser, curl, Postman, or frontend apps
- ✅ Interactive API documentation (Swagger UI)
- ⚠️ Web UI dashboards not yet implemented (backend ready)

### 3. Web UI (Not Yet Implemented)
- ⚠️ Frontend dashboards planned but not built
- Backend API is ready to support web UI

## Using the REST API

### Start the API Server

```bash
python run.py --start
```

The API will be available at:
- **Base URL:** http://localhost:8000
- **Interactive Docs:** http://localhost:8000/docs
- **Alternative Docs:** http://localhost:8000/redoc

### Access Interactive API Documentation

Once the server is running, open your browser to:
```
http://localhost:8000/docs
```

This provides a **web-based interface** where you can:
- ✅ See all available endpoints
- ✅ Test endpoints directly in the browser
- ✅ View request/response schemas
- ✅ Submit requests and see responses

### Example API Calls

#### Using curl (Command Line)

```bash
# Get user profile
curl http://localhost:8000/data/profile/user_001

# Get recommendations
curl http://localhost:8000/data/recommendations/user_001

# Submit feedback
curl -X POST http://localhost:8000/data/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "recommendation_id": "rec_123",
    "user_id": "user_001",
    "thumbs_up": true,
    "helped_me": true
  }'
```

#### Using Browser

1. Start API server: `python run.py --start`
2. Open browser to: `http://localhost:8000/docs`
3. Click on any endpoint
4. Click "Try it out"
5. Fill in parameters
6. Click "Execute"
7. See response in browser

#### Using Python requests

```python
import requests

# Get recommendations
response = requests.get('http://localhost:8000/data/recommendations/user_001')
recommendations = response.json()
print(recommendations)

# Submit feedback
response = requests.post('http://localhost:8000/data/feedback', json={
    'recommendation_id': 'rec_123',
    'user_id': 'user_001',
    'thumbs_up': True,
    'helped_me': True
})
print(response.json())
```

## Available User-Facing Endpoints

### Get User Profile
```
GET /data/profile/{user_id}
```
Returns: Persona, signals, data availability

### Get Recommendations
```
GET /data/recommendations/{user_id}
```
Returns: List of recommendations with rationales

### Submit Feedback
```
POST /data/feedback
Body: {
  "recommendation_id": "...",
  "user_id": "...",
  "thumbs_up": true/false,
  "helped_me": true/false,
  "applied_this": true/false,
  "free_text": "..."
}
```

### Consent Management
```
POST /users/consent
Body: {"user_id": "user_001"}

DELETE /users/consent/{user_id}

GET /users/consent/{user_id}
```

## Web UI Status

### What's Implemented
- ✅ REST API backend (all endpoints)
- ✅ Interactive API documentation (Swagger UI)
- ✅ Data models and schemas
- ✅ Backend logic for all features

### What's Not Implemented
- ❌ User-facing web dashboard (HTML/CSS/JS frontend)
- ❌ Operator web dashboard (HTML/CSS/JS frontend)
- ❌ Frontend authentication UI
- ❌ Frontend forms and buttons

### Why No Web UI Yet?

The web dashboards were planned in Phase 5 (User UX) but the backend API was prioritized first (Phase 8). The API is fully functional and ready for a frontend to be built.

## Building a Web UI

The API is ready to support a web frontend. You could build:

1. **Simple HTML/JS Frontend**
   - Use the API endpoints
   - Create forms and buttons
   - Display data from API responses

2. **React/Vue/Angular App**
   - Modern framework
   - Connect to API endpoints
   - Rich user experience

3. **Use Swagger UI**
   - Already available at `/docs`
   - Functional for testing
   - Not as polished as custom UI

## Quick Start: Test via Browser

1. **Start the API server:**
   ```bash
   python run.py --start
   ```

2. **Open browser:**
   ```
   http://localhost:8000/docs
   ```

3. **Test an endpoint:**
   - Find "GET /data/recommendations/{user_id}"
   - Click "Try it out"
   - Enter `user_001` for user_id
   - Click "Execute"
   - See the response!

## Summary

**Current State:**
- ✅ Command-line tools (full testing suite)
- ✅ REST API (HTTP accessible)
- ✅ Interactive web docs (browser-based testing)
- ❌ Custom web UI (not implemented)

**Recommendation:**
- For testing: Use command-line tools or Swagger UI (`/docs`)
- For production: Build a web frontend using the API
- For development: Use the API endpoints directly

The API is production-ready and can be accessed via any HTTP client, including browsers, curl, Postman, or custom frontend applications.

