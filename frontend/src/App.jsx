import React, { useEffect, useState } from "react";
import {
  changeTaskStatus,
  createTask,
  deleteTask,
  getTasksByUser,
  getUsers,
  listTasks,
  registerUser,
  loginUser,
} from "./api";

const EMPTY_FORM = {
  title: "",
  description: "",
};

const EMPTY_REGISTER_FORM = {
  username: "",
  password: "",
};

export default function App() {
  const [tasks, setTasks] = useState([]);
  const [users, setUsers] = useState([]);
  const [selectedUser, setSelectedUser] = useState("");
  const [taskForm, setTaskForm] = useState(EMPTY_FORM);
  const [registerForm, setRegisterForm] = useState(EMPTY_REGISTER_FORM);
  const [isLoginMode, setIsLoginMode] = useState(false);
  const [username, setUsername] = useState(() => localStorage.getItem("tf_username") || "");
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [message, setMessage] = useState("");
  const [messageType, setMessageType] = useState("");

  useEffect(() => {
    loadAllTasks();
    loadUsers();
  }, []);

  function showMessage(type, text) {
    setMessage(text);
    setMessageType(type);
  }

  async function loadUsers() {
    try {
      const data = await getUsers();
      setUsers(data);
    } catch (error) {
      showMessage("error", error.message);
    }
  }

  async function loadAllTasks() {
    try {
      setIsLoading(true);
      const data = await listTasks();
      setTasks(data);
      setSelectedUser("");
      setMessage("");
      setMessageType("");
    } catch (error) {
      showMessage("error", error.message);
    } finally {
      setIsLoading(false);
    }
  }

  async function loadTasksForUser(targetUser, source = "admin") {
    if (!targetUser) {
      return;
    }

    try {
      setIsLoading(true);
      const data = await getTasksByUser(targetUser);
      setTasks(data);
      setSelectedUser(targetUser);
      showMessage(
        "info",
        source === "self" ? `Mostrando tareas de ${targetUser}.` : `Vista admin: tareas de ${targetUser}.`
      );
    } catch (error) {
      showMessage("error", error.message);
    } finally {
      setIsLoading(false);
    }
  }

  async function loadMyTasks() {
    if (!username) {
      showMessage("error", "Registrate o inicia sesion para ver tus tareas.");
      return;
    }

    await loadTasksForUser(username, "self");
  }

  function handleTaskFormChange(event) {
    const { name, value } = event.target;
    setTaskForm((current) => ({ ...current, [name]: value }));
  }

  function handleRegisterFormChange(event) {
    const { name, value } = event.target;
    setRegisterForm((current) => ({ ...current, [name]: value }));
  }

  async function handleLogin(event) {
    event.preventDefault();

    const nextUsername = registerForm.username.trim();
    const nextPassword = registerForm.password.trim();
    if (!nextUsername || !nextPassword) {
      showMessage("error", "Usuario y contrasena son obligatorios.");
      return;
    }

    try {
      const data = await loginUser({
        username: nextUsername,
        password: nextPassword,
      });

      localStorage.setItem("tf_username", data.username);
      setUsername(data.username);
      setRegisterForm(EMPTY_REGISTER_FORM);
      showMessage("success", `Sesion iniciada como ${data.username}.`);
      await loadUsers();
    } catch (error) {
      showMessage("error", error.message);
    }
  }

  async function handleRegister(event) {
    event.preventDefault();

    const nextUsername = registerForm.username.trim();
    const nextPassword = registerForm.password.trim();
    if (!nextUsername || !nextPassword) {
      showMessage("error", "Usuario y contrasena son obligatorios.");
      return;
    }

    try {
      const data = await registerUser({
        username: nextUsername,
        password: nextPassword,
      });

      localStorage.setItem("tf_username", data.username);
      setUsername(data.username);
      setRegisterForm(EMPTY_REGISTER_FORM);
      showMessage("success", `Sesion iniciada como ${data.username}.`);
      await loadUsers();
    } catch (error) {
      showMessage("error", error.message);
    }
  }

  function handleLogout() {
    localStorage.removeItem("tf_username");
    setUsername("");
    showMessage("info", "Sesion cerrada.");
  }

  async function handleSubmit(event) {
    event.preventDefault();

    const title = taskForm.title.trim();
    if (!title) {
      showMessage("error", "El titulo es obligatorio.");
      return;
    }

    try {
      setIsSaving(true);
      await createTask({
        title,
        description: taskForm.description.trim(),
        owner: username || null,
      });
      setTaskForm(EMPTY_FORM);
      showMessage("success", "Tarea creada.");
      await loadAllTasks();
    } catch (error) {
      showMessage("error", error.message);
    } finally {
      setIsSaving(false);
    }
  }

  async function handleToggleStatus(task) {
    const nextStatus = task.status === "todo" ? "done" : "todo";

    try {
      await changeTaskStatus(task.id, nextStatus);
      showMessage("success", `Estado actualizado a ${nextStatus}.`);
      if (selectedUser) {
        await loadTasksForUser(selectedUser);
      } else {
        await loadAllTasks();
      }
    } catch (error) {
      showMessage("error", error.message);
    }
  }

  async function handleDelete(taskId) {
    try {
      await deleteTask(taskId);
      showMessage("success", "Tarea eliminada.");
      if (selectedUser) {
        await loadTasksForUser(selectedUser);
      } else {
        await loadAllTasks();
      }
    } catch (error) {
      showMessage("error", error.message);
    }
  }

  return (
    <main className="page">
      <section className="panel">
        <div className="hero">
          <p className="eyebrow">Taskflow</p>
          <h1>Gestion minima de tareas con vista admin</h1>
          <p className="subtitle">
            Crea tareas, cambia su estado y usa el panel admin para ver usuarios y abrir
            sus tareas con un click.
          </p>
        </div>

        <section className="dashboard-grid">
          <section className="auth-card">
            <div className="section-heading">
              <h2>Sesion</h2>
            </div>

            {username ? (
              <div className="session-row">
                <p className="message">
                  Conectado como <strong>{username}</strong>
                </p>
                <button type="button" className="secondary" onClick={handleLogout}>
                  Cerrar sesion
                </button>
              </div>
            ) : (
              <form className="inline-form" onSubmit={isLoginMode ? handleLogin : handleRegister}>
                <input
                  name="username"
                  value={registerForm.username}
                  onChange={handleRegisterFormChange}
                  placeholder="Usuario"
                />
                <input
                  name="password"
                  type="password"
                  value={registerForm.password}
                  onChange={handleRegisterFormChange}
                  placeholder="Contrasena"
                />
                <button type="submit">{isLoginMode ? "Iniciar sesion" : "Registrarse"}</button>
                <button
                  type="button"
                  className="link-button"
                  onClick={() => setIsLoginMode(!isLoginMode)}
                >
                  {isLoginMode ? "Crear cuenta" : "Ya tengo cuenta"}
                </button>
              </form>
            )}
          </section>

          <section className="auth-card admin-card">
            <div className="section-heading">
              <h2>Admin</h2>
              <span className="badge">{users.length}</span>
            </div>
            <p className="message">Haz click en un usuario para ver sus tareas.</p>
            {users.length === 0 ? (
              <p className="message">Todavia no hay usuarios registrados.</p>
            ) : (
              <ul className="user-list">
                {users.map((user) => (
                  <li key={user.id}>
                    <button
                      type="button"
                      className={`user-chip ${selectedUser === user.username ? "active" : ""}`}
                      onClick={() => loadTasksForUser(user.username)}
                    >
                      {user.username}
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </section>
        </section>

        <form className="task-form" onSubmit={handleSubmit}>
          <label className="field">
            <span>Titulo</span>
            <input
              name="title"
              value={taskForm.title}
              onChange={handleTaskFormChange}
              placeholder="Ej. Preparar demo"
              maxLength={120}
            />
          </label>

          <label className="field">
            <span>Descripcion</span>
            <textarea
              name="description"
              value={taskForm.description}
              onChange={handleTaskFormChange}
              placeholder="Contexto breve de la tarea"
              rows="4"
            />
          </label>

          <div className="actions">
            <button type="submit" disabled={isSaving}>
              {isSaving ? "Guardando..." : "Crear tarea"}
            </button>
            <div className="action-group">
              <button type="button" className="secondary" onClick={loadMyTasks} disabled={isLoading}>
                Ver mis tareas
              </button>
              <button type="button" className="secondary" onClick={loadAllTasks} disabled={isLoading}>
                Ver todas
              </button>
              <button type="button" className="secondary" onClick={loadUsers}>
                Recargar usuarios
              </button>
            </div>
          </div>
        </form>

        {message ? <p className={`message ${messageType}`}>{message}</p> : null}

        <section className="task-list">
          <div className="section-heading">
            <h2>{selectedUser ? `Tareas de ${selectedUser}` : "Tareas registradas"}</h2>
            <span className="badge">{tasks.length}</span>
          </div>

          {isLoading ? <p className="message">Cargando tareas...</p> : null}

          {!isLoading && tasks.length === 0 ? (
            <p className="message">Todavia no hay tareas para mostrar.</p>
          ) : null}

          {!isLoading && tasks.length > 0 ? (
            <ul className="tasks">
              {tasks.map((task) => (
                <li key={task.id} className="task-card">
                  <div className="task-card-header">
                    <div>
                      <strong>{task.title}</strong>
                      <p className="task-meta">
                        {task.owner ? `Propietario: ${task.owner}` : "Sin propietario"}
                      </p>
                    </div>
                    <span className={`status ${task.status === "done" ? "done" : ""}`}>
                      {task.status}
                    </span>
                  </div>
                  <p>{task.description || "Sin descripcion."}</p>
                  <div className="task-actions">
                    <button type="button" className="secondary" onClick={() => handleToggleStatus(task)}>
                      {task.status === "todo" ? "Marcar hecha" : "Marcar pendiente"}
                    </button>
                    <button type="button" className="danger" onClick={() => handleDelete(task.id)}>
                      Eliminar
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          ) : null}
        </section>
      </section>
    </main>
  );
}
