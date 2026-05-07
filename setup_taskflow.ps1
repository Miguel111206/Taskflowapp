$root = "C:\Users\User\taskflow_app"
$dirs = @("backend","backend\app","frontend","frontend\src","frontend\src\components")
foreach ($d in $dirs) {
    $path = Join-Path $root $d
    if (-not (Test-Path $path)) { New-Item -ItemType Directory -Path $path | Out-Null }
}

# backend/main.py
$main_py = @'
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from sqlmodel import SQLModel, Field, create_engine, Session, select
import os

DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://user:password@localhost:3306/taskflow_db")
engine = create_engine(DATABASE_URL, echo=False)

class Task(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str
    description: str = ""
    status: str = "todo"

SQLModel.metadata.create_all(engine)

app = FastAPI()

class TaskCreate(BaseModel):
    title: str
    description: str = ""

@app.post("/tasks", response_model=Task)
def create_task(task: TaskCreate):
    with Session(engine) as session:
        t = Task(title=task.title, description=task.description)
        session.add(t)
        session.commit()
        session.refresh(t)
        return t

@app.get("/tasks", response_model=List[Task])
def list_tasks():
    with Session(engine) as session:
        tasks = session.exec(select(Task)).all()
        return tasks

@app.get("/tasks/{task_id}", response_model=Task)
def get_task(task_id: int):
    with Session(engine) as session:
        t = session.get(Task, task_id)
        if not t:
            raise HTTPException(status_code=404, detail="Task not found")
        return t

@app.put("/tasks/{task_id}", response_model=Task)
def update_task(task_id: int, task: TaskCreate):
    with Session(engine) as session:
        t = session.get(Task, task_id)
        if not t:
            raise HTTPException(status_code=404, detail="Task not found")
        t.title = task.title
        t.description = task.description
        session.add(t)
        session.commit()
        session.refresh(t)
        return t

@app.delete("/tasks/{task_id}")
def delete_task(task_id: int):
    with Session(engine) as session:
        t = session.get(Task, task_id)
        if not t:
            raise HTTPException(status_code=404, detail="Task not found")
        session.delete(t)
        session.commit()
        return {"ok": True}
'@
$main_py | Out-File -FilePath (Join-Path $root "backend\main.py") -Encoding utf8

# backend/requirements.txt
$reqs = @'
fastapi
uvicorn[standard]
sqlmodel
pymysql
'@
$reqs | Out-File -FilePath (Join-Path $root "backend\requirements.txt") -Encoding utf8

# backend/.env.example
$env = @'
# Ejemplo de DATABASE_URL para MySQL
# mysql+pymysql://user:password@host:3306/dbname
DATABASE_URL=mysql+pymysql://user:password@localhost:3306/taskflow_db
'@
$env | Out-File -FilePath (Join-Path $root "backend\.env.example") -Encoding utf8

# frontend files
$package = @'
{
  "name": "taskflow-frontend",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0"
  },
  "devDependencies": {
    "vite": "^5.0.0",
    "@vitejs/plugin-react": "^4.0.0"
  }
}
'@
$package | Out-File -FilePath (Join-Path $root "frontend\package.json") -Encoding utf8

$index = @'
<!doctype html>
<html>
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Taskflow</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
'@
$index | Out-File -FilePath (Join-Path $root "frontend\index.html") -Encoding utf8

$mainjsx = @'
import React from "react";
import { createRoot } from "react-dom/client";
import App from "./App";
import "./styles.css";

createRoot(document.getElementById("root")).render(<App />);
'@
$mainjsx | Out-File -FilePath (Join-Path $root "frontend\src\main.jsx") -Encoding utf8

$appjsx = @'
import React, { useEffect, useState } from "react";
import { listTasks, createTask, updateTask, deleteTask } from "./api";

export default function App() {
  const [tasks, setTasks] = useState([]);
  const [title, setTitle] = useState("");

  useEffect(() => { refresh(); }, []);
  async function refresh() {
    setTasks(await listTasks());
  }
  async function onCreate(e) {
    e.preventDefault();
    if (!title) return;
    await createTask({ title, description: "" });
    setTitle("");
    refresh();
  }
  return (
    <div className="container">
      <h1>Taskflow (MVP)</h1>
      <form onSubmit={onCreate}>
        <input value={title} onChange={e=>setTitle(e.target.value)} placeholder="Nueva tarea" />
        <button type="submit">Crear</button>
      </form>
      <ul>
        {tasks.map(t => (
          <li key={t.id}>
            <strong>{t.title}</strong> — {t.status}
          </li>
        ))}
      </ul>
    </div>
  );
}
'@
$appjsx | Out-File -FilePath (Join-Path $root "frontend\src\App.jsx") -Encoding utf8

$api = @'
const API = import.meta.env.VITE_API_URL || "http://localhost:8000";

export async function listTasks() {
  const res = await fetch(`${API}/tasks`);
  return await res.json();
}
export async function createTask(payload) {
  const res = await fetch(`${API}/tasks`, {
    method: "POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify(payload)
  });
  return await res.json();
}
'@
$api | Out-File -FilePath (Join-Path $root "frontend\src\api.js") -Encoding utf8

$styles = @'
body { font-family: Arial, sans-serif; padding: 20px; }
.container { max-width: 800px; margin: 0 auto; }
input { padding: 8px; margin-right: 8px; }
'@
$styles | Out-File -FilePath (Join-Path $root "frontend\src\styles.css") -Encoding utf8

# TASKS.md with assignments
$tasks = @'
# Taskflow - División de trabajo (Asignado antes de iniciar cada parte)

---
Asignado: Copilot
- Backend (FastAPI):
  - Crear API CRUD de tareas (endpoints /tasks)
  - Modelo Task con SQLModel
  - Archivo: backend/main.py
  - requirements: backend/requirements.txt

---
Asignado: Codex
- Frontend (React + Vite):
  - Interfaz mínima para listar y crear tareas
  - Conectar a la API (frontend/src/api.js)
  - Archivos: frontend/* (index.html, src/*)

---
Asignado: Copilot
- Scripts y ejemplos de configuración
  - backend/.env.example
  - setup_taskflow.ps1 (genera estructura y archivos)

---
Notas:
- Ejecutar setup_taskflow.ps1 en la máquina Windows crea la estructura y los archivos.
'@
$tasks | Out-File -FilePath (Join-Path $root "TASKS.md") -Encoding utf8

# README
$readme = @'
# Taskflow (MVP)

Estructura: backend (FastAPI) y frontend (React + Vite).

Instrucciones rápidas:
1. Abrir PowerShell en esta carpeta y ejecutar: .\setup_taskflow.ps1
2. Backend: ir a backend, crear entorno virtual e instalar:
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   uvicorn main:app --reload
3. Frontend: ir a frontend, npm install, npm run dev

API por defecto: http://localhost:8000
Frontend por defecto: http://localhost:5173
'@
$readme | Out-File -FilePath (Join-Path $root "README.md") -Encoding utf8

Write-Output "setup_taskflow.ps1 and helper files created in $root. Run the PS1 script locally to generate project files."
