# SpendSense Web UI

This directory contains the web-based user interface for SpendSense.

## Structure

```
web/
└── static/
    ├── index.html          # User-facing dashboard
    ├── operator.html       # Operator dashboard
    ├── style.css           # Shared styles
    ├── operator.css        # Operator-specific styles
    ├── app.js              # User dashboard JavaScript
    └── operator.js         # Operator dashboard JavaScript
```

## Access

Once the API server is running, access the dashboards at:

- **User Dashboard:** http://localhost:8000/
- **Operator Dashboard:** http://localhost:8000/operator-dashboard
- **API Documentation:** http://localhost:8000/docs

## Features

### User Dashboard
- Personalized financial insights
- Behavioral signal visualization
- Education recommendations
- Partner offers
- Feedback submission
- Consent management

### Operator Dashboard
- System analytics
- Approval queue management
- User review and search
- Feedback review
- System health monitoring

## Technology

- **HTML5** - Semantic markup
- **CSS3** - Modern styling with gradients and responsive design
- **Vanilla JavaScript** - No framework dependencies
- **FastAPI Static Files** - Served via FastAPI's StaticFiles mount

## Browser Compatibility

Works in all modern browsers:
- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)

## Development

The web UI is automatically served when you start the API server:

```bash
python run.py --start
```

Static files are mounted at `/static/` and the root route serves the user dashboard.

## API Integration

The frontend makes requests to the REST API endpoints:
- `/users/*` - User management
- `/data/*` - Data and recommendations
- `/operator/*` - Operator functions
- `/eval/*` - Evaluation metrics

All API calls use the same origin (auto-detected from `window.location.origin`), so CORS is handled automatically.

