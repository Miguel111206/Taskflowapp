# Instructions for AI Assistant (Copilot/Terminal)

## Project: TaskFlow App

### Stack
- Frontend: React + Vite (port 5173)
- Backend: FastAPI (port 8010)
- Database: MySQL `taskflow`

### Files Structure
```
taskflow_app/
├── backend/
│   ├── main.py          # FastAPI app (ALL endpoints here)
│   ├── app/
│   │   ├── models.py    # User, Task SQLModel classes
│   │   └── db.py       # engine, create_db_tables
│   └── test_main.py    # pytest tests
└── frontend/
    └── src/
        ├── App_auth.jsx # Main UI component
        ├── api.js      # API calls (login, register, tasks)
        ├── main.jsx    # Entry point
        └── styles.css  # CSS styles
```

## Rules

### DO NOT EDIT
- Never edit `frontend/src/App_auth.jsx` - this is custom
- Never edit `frontend/src/styles.css` - this is custom
- Never edit `frontend/src/api.js` - this is custom
- Never edit any test files

### ONLY EDIT IF NEEDED
- `backend/main.py` - for API endpoints
- `backend/app/models.py` - for database models

### BEFORE EDITING
1. Read current file content first
2. Use grep to find patterns
3. Make minimal changes

### TESTING
- Run: `python -m pytest backend/test_main.py -v`
- Coverage target: 85%

### STARTING SERVERS
```powershell
# Backend
cd backend; uvicorn main:app --reload --host 127.0.0.1 --port 8010

# Frontend
cd frontend; npm run dev
```

## Current Issues to Solve
1. CORS blocking requests from localhost:5174
2. User model missing fields (locked_until, login_attempts, etc)

## User Preferences
- Dark theme UI with blue accents
- Interactive animations
- Use images/icons for better UX