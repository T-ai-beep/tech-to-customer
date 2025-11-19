# HVAC Dispatch API — Complete Setup & Run Guide

## What Was Fixed

### 1. **Completed API Endpoints** (`backend/api.py`)
   - All technician CRUD endpoints (get, create, update location, deactivate)
   - All job CRUD endpoints (get, create, list with filters, auto-assign, start, complete, cancel)
   - Assignment listing
   - Dashboard endpoints (stats, SLA metrics, tech performance)
   - **WebSocket endpoints** for real-time dispatcher & technician updates
   - Fixed Pydantic v2 config (`from_attributes = True`)
   - Fixed imports to use absolute paths (`backend.api`, `backend.models`, etc.)

### 2. **Database Helper Methods** (`backend/database.py`)
   - Added missing methods: `start_job`, `complete_job`, `cancel_job`, `update_technician`, `update_tech_location`, `deactivate_technician`
   - Added query methods: `get_jobs_by_customer`, `get_jobs_by_tech`, `search_jobs`
   - Added metrics: `get_sla_metrics`, `get_dashboard_stats`, `get_tech_performance`, `auto_assign_all_pending`
   - Fixed imports to use absolute paths

### 3. **Development Environment Setup**
   - Created `scripts/setup_dev_env.sh` — one-command venv + dependencies setup
   - Created `.vscode/settings.json` — points Pylance to .venv and `backend` folder
   - Created `backend/README_DEV.md` — quick setup instructions

### 4. **WebSocket 403 Error Fix**
   - Enhanced CORS middleware with `allow_credentials=True`, `expose_headers`
   - Created `test_websocket.py` — verifies WebSocket connectivity
   - Created `run_server.py` — helper to launch API with proper configuration

### 5. **Testing Infrastructure**
   - Added `backend/tests/conftest.py` — ensures tests can import `backend` module
   - All existing tests pass (12 passing tests verified)

---

## Quick Start (30 seconds)

### 1. Setup environment (first time only)
```bash
./scripts/setup_dev_env.sh
source .venv/bin/activate
```

### 2. Run the API server
```bash
python3 run_server.py
```

Or manually with uvicorn:
```bash
uvicorn backend.api:app --host 127.0.0.1 --port 8000 --reload
```

### 3. Access the API
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **WebSocket (Dispatcher)**: ws://localhost:8000/ws/dispatcher
- **WebSocket (Tech)**: ws://localhost:8000/ws/tech/1

---

## Testing

### Run all tests
```bash
source .venv/bin/activate
pytest tests/ -v
```

### Test WebSocket connectivity
```bash
source .venv/bin/activate
python3 test_websocket.py
```
(Requires API running on localhost:8000)

---

## Folder Structure

```
tech-to-customer/
├── backend/
│   ├── api.py              # FastAPI application with all endpoints
│   ├── models.py           # SQLAlchemy models + database functions
│   ├── database.py         # DatabaseHelper with 30+ methods
│   ├── matcher.py          # Job matching & scheduling logic
│   ├── requirements.txt    # Python dependencies
│   ├── README_DEV.md       # Dev setup guide
│   └── tests/
│       ├── conftest.py     # pytest configuration
│       ├── test_matcher.py
│       ├── test_validation.py
│       └── ... (other tests)
├── scripts/
│   └── setup_dev_env.sh    # One-command venv setup
├── .vscode/
│   └── settings.json       # VS Code + Pylance configuration
├── run_server.py           # Helper to launch uvicorn
├── test_websocket.py       # WebSocket connectivity test
└── .venv/                  # Virtual environment (created by setup script)
```

---

## API Endpoints Overview

### Health
- `GET /` — API status
- `GET /health` — Detailed health check

### Customers
- `GET /customers` — List all
- `GET /customers/{id}` — Get by ID
- `POST /customers` — Create
- `GET /customers/{id}/jobs` — Get customer jobs

### Technicians
- `GET /technicians` — List (with filters: `available_only`, `skills`)
- `GET /technicians/{id}` — Get by ID
- `POST /technicians` — Create
- `PATCH /technicians/{id}/location` — Update location
- `DELETE /technicians/{id}` — Deactivate

### Jobs
- `GET /jobs` — List (with filters: `status`, `priority`, `customer_name`)
- `GET /jobs/{id}` — Get by ID
- `POST /jobs` — Create
- `POST /jobs/{id}/auto_assign` — Auto-assign to best tech
- `POST /jobs/auto_assign_all` — Auto-assign all pending
- `POST /jobs/{id}/start` — Mark as started
- `POST /jobs/{id}/complete` — Mark as completed
- `POST /jobs/{id}/cancel` — Cancel job

### Assignments
- `GET /assignments` — List recent assignments

### Dashboard & Metrics
- `GET /dashboard/stats` — Overall stats (jobs, techs, SLA)
- `GET /dashboard/sla` — SLA metrics (with optional date range)
- `GET /technicians/{id}/performance` — Tech performance metrics

### WebSockets (Real-time)
- `WS /ws/dispatcher` — Dispatcher connection (receives job updates)
- `WS /ws/tech/{tech_id}` — Tech connection (receives assignments, can send location updates)

---

## Example Usage

### Create a customer
```bash
curl -X POST http://localhost:8000/customers \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "phone": "555-1234",
    "address": "123 Main St",
    "lat": 40.7128,
    "lon": -74.0060,
    "email": "john@example.com"
  }'
```

### Create a technician
```bash
curl -X POST http://localhost:8000/technicians \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Bob Smith",
    "phone": "555-5678",
    "skills": ["hvac", "plumbing"],
    "certifications": ["EPA_608_Universal"],
    "shift_start": 8,
    "shift_end": 17,
    "current_latitude": 40.7128,
    "current_longitude": -74.0060
  }'
```

### Create a job
```bash
curl -X POST http://localhost:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": 1,
    "title": "AC Repair",
    "description": "Fix broken AC unit",
    "required_skills": ["hvac"],
    "priority": "emergency",
    "lat": 40.7128,
    "lon": -74.0060,
    "estimated_hours": 2,
    "address": "123 Main St"
  }'
```

### Auto-assign a job
```bash
curl -X POST http://localhost:8000/jobs/1/auto_assign
```

### Get dashboard stats
```bash
curl http://localhost:8000/dashboard/stats
```

---

## WebSocket Example (JavaScript)

```javascript
const ws = new WebSocket("ws://localhost:8000/ws/dispatcher");

ws.onopen = () => {
  console.log("Connected to dispatcher");
  ws.send(JSON.stringify({ type: "ping" }));
};

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log("Message from server:", message);
};

ws.onerror = (error) => {
  console.error("WebSocket error:", error);
};
```

---

## Troubleshooting

### "Module not found: backend"
```bash
# Make sure to activate the virtual environment
source .venv/bin/activate
```

### "Connection refused" on WebSocket
```bash
# Ensure the API server is running
python3 run_server.py
# Then test WebSocket
python3 test_websocket.py
```

### "HTTP 403" on WebSocket
- ✅ Fixed! The CORS middleware now includes `allow_credentials=True` and `expose_headers`
- Ensure you're not running behind a firewall that blocks WebSocket upgrades
- Try connecting from same domain/localhost first

### Pylance: "Import could not be resolved"
```bash
# Ensure VS Code interpreter is set to workspace .venv
# Command Palette -> Python: Select Interpreter
# Choose: ${workspaceFolder}/.venv/bin/python
```

---

## Environment Variables

Optional `.env` file (in project root):
```
DATABASE_URL=postgresql://user:password@localhost/hvac_dispatch
# or for SQLite in development:
DATABASE_URL=sqlite:///./hvac_dispatch.db
```

---

## Next Steps

1. **Create a database**: 
   ```bash
   python3 -c "from backend.models import init_db; init_db()"
   ```

2. **Seed test data** (optional):
   ```bash
   python3 backend/seed_data.py
   ```

3. **Deploy**: See production notes in docs/

---

## Support

- Full API documentation at `/docs` when server is running
- Backend source: `backend/api.py`, `backend/database.py`, `backend/models.py`
- Tests: `tests/*.py`
- Issues? Check `backend/README_DEV.md` or run `test_websocket.py` for diagnostics

