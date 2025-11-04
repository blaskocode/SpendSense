# Quick Start: Web-Based Testing

Your API server is running! 🎉

## What the Server Output Means

```
✅ Server started successfully
✅ Running on http://127.0.0.1:8000 (localhost:8000)
✅ Swagger UI available at http://localhost:8000/docs
✅ Root endpoint accessed (GET / HTTP/1.1" 200 OK) - Server is responding!
```

## Next Steps

### 1. Open Swagger UI in Your Browser

Open this URL in your browser:
```
http://localhost:8000/docs
```

This gives you a **web-based interface** to test all endpoints!

### 2. Test the Root Endpoint

You already accessed the root endpoint (that's the `GET / HTTP/1.1" 200 OK` in your terminal).

Open in browser:
```
http://localhost:8000/
```

You should see:
```json
{
  "service": "SpendSense API",
  "version": "1.0.0",
  "status": "running",
  "endpoints": {
    "user_management": "/users",
    "data_analysis": "/data",
    "operator": "/operator",
    "evaluation": "/eval"
  }
}
```

### 3. Test User Recommendations

In Swagger UI (`/docs`):
1. Expand **"Data & Analysis"** section
2. Click **"GET /data/recommendations/{user_id}"**
3. Click **"Try it out"**
4. Enter `user_001` in the user_id field
5. Click **"Execute"**
6. See the JSON response with recommendations!

### 4. Test User Profile

1. In Swagger UI, find **"GET /data/profile/{user_id}"**
2. Click "Try it out"
3. Enter `user_001`
4. Click "Execute"
5. See persona, signals, and data availability!

### 5. Submit Feedback

1. Find **"POST /data/feedback"**
2. Click "Try it out"
3. Click "Request body" to see the example
4. Modify the JSON with your values
5. Click "Execute"

## Available Endpoints to Test

### User-Facing (Most relevant for testing)
- `GET /data/profile/{user_id}` - See user's persona and signals
- `GET /data/recommendations/{user_id}` - Get recommendations
- `POST /data/feedback` - Submit feedback
- `POST /users/consent` - Record consent
- `GET /users/consent/{user_id}` - Check consent

### Operator (For system testing)
- `GET /operator/analytics` - System metrics
- `GET /operator/review` - Approval queue
- `GET /operator/feedback` - Aggregated feedback

### System
- `GET /` - Server status
- `GET /health` - Health check
- `GET /eval/metrics` - Evaluation metrics

## Pro Tips

1. **Swagger UI is your friend** - It's a full web interface, not just docs
2. **All endpoints are interactive** - Click "Try it out" on any endpoint
3. **See responses in real-time** - JSON responses appear in the browser
4. **No code needed** - Everything works through the web interface

## Example: Complete User Journey in Browser

1. **Check consent:**
   - `GET /users/consent/user_001`
   - See if user has consent

2. **Record consent (if needed):**
   - `POST /users/consent`
   - Body: `{"user_id": "user_001"}`

3. **Get recommendations:**
   - `GET /data/recommendations/user_001`
   - See all recommendations

4. **Submit feedback:**
   - `POST /data/feedback`
   - Submit thumbs up/down

All done in the browser - no command line needed!

## Server Status

Your server is running and ready. The terminal shows:
- ✅ Server started
- ✅ Listening on port 8000
- ✅ Already responding to requests (you accessed `/`)

Keep the terminal open - that's your server running. To stop it, press `CTRL+C` in the terminal.

---

**You're all set! Open http://localhost:8000/docs and start testing!** 🚀

