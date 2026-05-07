# TaskFlow - Proyecto de Gestión de Tareas con IA

## 📋 Descripción del Proyecto

TaskFlow es una aplicación web de gestión de tareas con un chatbot integrado que permite crear, editar y administrar tareas usando lenguaje natural. El proyecto está diseñado para aprender y exponer tecnologías modernas de desarrollo web.

---

## 🏗️ Arquitectura del Proyecto

```
taskflow_app/
├── backend/                 # Servidor API (FastAPI)
│   ├── main.py            # Endpoints y lógica del chatbot
│   ├── app/
│   │   ├── models.py      # Modelos de base de datos (User, Task)
│   │   └── db.py         # Configuración de base de datos
│   ├── .venv/            # Entorno virtual Python
│   └── requirements.txt   # Dependencias Python
│
└── frontend/              # Interfaz de usuario (React + Vite)
    ├── src/
    │   ├── App.jsx       # Componente principal
    │   ├── api.js        # Conexiones al backend
    │   └── styles.css    # Estilos visuales
    ├── index.html       # Punto de entrada HTML
    └── package.json     # Dependencias Node.js
```

---

## 🛠️ Tecnologías Usadas

### Backend
| Tecnología | Propósito |
|------------|-----------|
| **FastAPI** | Framework web rápido y moderno |
| **SQLModel** | ORM para base de datos |
| **SQLite** | Base de datos ligera (archivo local) |
| **Uvicorn** | Servidor ASGI |
| **PyJWT** | Autenticación con tokens JWT |
| **Passlib** | Hashing de contraseñas |

### Frontend
| Tecnología | Propósito |
|------------|-----------|
| **React** | Biblioteca de interfaz de usuario |
| **Vite** | Herramienta de build y desarrollo |
| **CSS3** | Estilos con Variables CSS |

---

## 🚀 Cómo Ejecutar el Proyecto

### Opción 1: Script Automático
```powershell
.\setup_taskflow.ps1
```

### Opción 2: Manual

**Backend:**
```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

**Frontend:**
```powershell
cd frontend
npm install
npm run dev
```

### Puertos por Defecto
- Backend: `http://127.0.0.1:8000`
- Frontend: `http://localhost:5181`

---

## 📡 Endpoints de la API

### Autenticación
| Método | Endpoint | Descripción |
|-------|----------|------------|
| POST | `/register` | Crear nueva cuenta |
| POST | `/login` | Iniciar sesión |
| POST | `/refresh` | Actualizar token |
| POST | `/logout` | Cerrar sesión |
| GET | `/me` | Obtener usuario actual |

### Tareas (Tasks)
| Método | Endpoint | Descripción |
|-------|----------|------------|
| GET | `/tasks` | Listar todas las tareas |
| POST | `/tasks` | Crear nueva tarea |
| GET | `/tasks/{id}` | Ver tarea específica |
| PUT | `/tasks/{id}` | Editar tarea |
| PATCH | `/tasks/{id}/status` | Cambiar estado |
| DELETE | `/tasks/{id}` | Eliminar tarea |

### Chatbot
| Método | Endpoint | Descripción |
|-------|----------|------------|
| POST | `/chatbot` | Enviar mensaje (v1) |
| POST | `/chatbot/v2` | Enviar mensaje (v2) |

### Administración
| Método | Endpoint | Descripción |
|-------|----------|------------|
| GET | `/users` | Listar usuarios |
| POST | `/admin/promote/{username}` | Hacer admin |
| POST | `/admin/demote/{username}` | Quitar admin |

---

## 🤖 Chatbot - Comandos y Lenguaje Natural

### 📝 Comandos Escritos
```
[CREAR]
- crea [nombre de tarea]
- crear [nombre]
- nueva [nombre]

[VER]
- mis tareas
- pendientes
- completadas
- stats

[EDITAR]
- completa [nombre o #ID]
- elimina [nombre o #ID]
- cambia #ID a [nuevo nombre]

[BUSCAR]
- busca [palabra]
- detalle #ID

[FOTOS]
- foto [nombre]
- subir foto [nombre]

[MANTENIMIENTO]
- limpiar
```

### 💬 Lenguaje Natural (Entiende frases completas)

El chatbot puede entender oraciones completas en español e inglés:

```
SALUDOS Y AYUDA:
- hola, hello, hey, buenas, que tal
- ayuda, que puedes hacer
- ?

CREAR TAREA:
- quiero crear una tarea [nombre]
- necesito hacer [nombre]
- tengo que hacer la tarea de [nombre]
- agrega una nueva tarea
- hazme una tarea llamada [nombre]
- voy a crear [nombre]
- nueva tarea [nombre]

COMPLETAR TAREA:
- ya la hice
- ya termine
- ya completada
- marcar como faite
- listo con la tarea 1
- completa la tarea [nombre]
- done #1

ELIMINAR TAREA:
- borra la tarea [nombre]
- elimina la tarea #1
- quitame la tarea
- borrar tarea

EDITAR/CAMBIAR NOMBRE:
- cambia #1 a [nuevo nombre]
- editar #1 a [nuevo nombre]
- renombra #1 a [nuevo nombre]

VER TAREAS:
- muestrame mis tareas
- dime mis tareas
- ver mis tareas
- cuales tengo pendientes?

INFO Y ESTADISTICAS:
- cuantas tareas tengo
- cuanto tengo hecho
- dime el progreso
- stats

LIMPIAR:
- limpiar las completadas
- borrar las tareas feitas

BUSCAR:
- busca [palabra]
- encuentra [palabra]

FOTOS:
- agregar foto a [nombre]
- subir imagen de [tarea]
```

---

## 🎨 Características Visuales

COMPLETAR TAREA:
- ya la hice
- ya terminè
- marcar como faite

ELIMINAR TAREA:
- borra la tarea [nombre]
- elimina [nombre]

VER TAREAS:
- muèstrame mis tareas
- dime mis tareas
- ver mis tareas

BUSCAR:
- busca [palabra]

LIMPIAR:
- limpiar
- borrar completadas

INFO:
- cuàntas tareas tengo
- cuanto tengo
```

---

## 📊 Modelos de Base de Datos

### User (Usuario)
```python
class User:
    id: int           # ID único
    username: str     # Nombre de usuario (único)
    password_hash: str  # Contraseña hasheada
    is_admin: bool    # Es administrador
    role: str         # Rol (user/admin)
    is_2fa_enabled: bool  # Autenticación 2FA
    totp_secret: str # Secreto TOTP
    login_attempts: int # Intentos de login
    locked_until: str  # Bloqueo hasta
```

### Task (Tarea)
```python
class Task:
    id: int           # ID único
    title: str        # Título de la tarea
    description: str # Descripción
    status: str      # Estado (todo/in_progress/done)
    owner: str       # Propietario (username)
    image: str       # Ruta de imagen (opcional)
```

---

## 🔐 Autenticación

El sistema usa **JWT (JSON Web Tokens)**:
1. El usuario envía username y password al login
2. El servidor verifica y genera un token de acceso
3. El token se envía en cada request HEADER: `Authorization: Bearer [token]`
4. El token expira después de un tiempo

---

## 🎨 Características Visuales

- **Tema Oscuro** con acentos en azul (#6366f1)
- **Diseño responsivo** - funciona en móvil y escritorio
- **Animaciones suaves** en botones y paneles
- **Chatbot flotante** para interactuar

---

## 📝 Cómo Usar la Aplicación

1. **Registrarse:** Escribir usuario y contraseña
2. **Crear tareas:** Usar el formulario o el chatbot
3. **Ver tareas:** Click en "Mis tareas" o escribir en el chat
4. **Completar:** Click en el botón o decir "completa #ID"
5. **Chatbot:** Escribir mensajes en la ventana de chat

---

## 🧪 Testing

Ejecutar pruebas:
```powershell
cd backend
python -m pytest test_main.py -v
```

---

## 📌 Notas para Presentar

1. **FastAPI** es más rápido que Flask/Django
2. **React + Vite** es el estándar actual
3. El chatbot usa **regex** para entender lenguaje natural
4. **SQLModel** unifica SQLAlchemy y Pydantic
5. El chatbot puede mejorarse con **NLP** o **IA**

---

## ✅ Estado del Proyecto

- [x] CRUD de tareas
- [x] Registro/Login de usuarios
- [x] Chatbot con comandos
- [x] Chatbot con lenguaje natural
- [x] Panel de administrador
- [ ] Subir imágenes (endpoint listo)
- [ ] Tests completos

---

## 📞 Recursos

- Documentación FastAPI: https://fastapi.tiangolo.com/
- Documentación React: https://react.dev/
- Vite: https://vitejs.dev/