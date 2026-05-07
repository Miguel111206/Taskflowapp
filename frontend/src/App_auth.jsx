import React, { useEffect, useState, useRef } from "react";
import {
  CheckCircle,
  Circle,
  Clock,
  Trash2,
  LogOut,
  Shield,
  ShieldCheck,
  User,
  Users,
  Settings,
  Plus,
  Lock,
  ArrowRight,
  AlertTriangle,
  Check,
  Sparkles,
  Zap,
  Activity,
  KeyRound,
  RotateCcw,
  Image,
  Camera,
  X,
  FileImage,
  Eye,
  MessageSquare,
  Send,
  Bot,
  Loader,
} from "lucide-react";
import {
  changeTaskStatus,
  createTask,
  deleteTask,
  getTasksByUser,
  listTasks,
  registerUser,
  getUsers,
  loginUser,
  login2FA,
  logout,
  getMe,
  setup2FA,
  enable2FA,
  disable2FA,
  promoteUser,
  demoteUser,
  deleteUser,
  uploadTaskImage,
  getTaskImage,
} from "./api";

const EMPTY_FORM = { title: "", description: "" };
const EMPTY_LOGIN = { username: "", password: "" };
const EMPTY_REGISTER = { username: "", password: "" };

export default function App() {
  const [tasks, setTasks] = useState([]);
  const [taskForm, setTaskForm] = useState(EMPTY_FORM);
  const [loginForm, setLoginForm] = useState(EMPTY_LOGIN);
  const [registerForm, setRegisterForm] = useState(EMPTY_REGISTER);
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [message, setMessage] = useState("");
  const [showLogin, setShowLogin] = useState(true);
  const [view, setView] = useState("all");
  const [selectedUser, setSelectedUser] = useState(null);
  const [show2FASetup, setShow2FASetup] = useState(false);
  const [qrCode, setQrCode] = useState(null);
  const [totpCode, setTotpCode] = useState("");
  const [users, setUsers] = useState([]);
  const [loginStep, setLoginStep] = useState("credentials");
  const [showBackgroundParticles, setShowBackgroundParticles] = useState(true);
  const [deletingTask, setDeletingTask] = useState(null);
  const [creatingTask, setCreatingTask] = useState(false);
  const [completedTasks, setCompletedTasks] = useState(new Set());
  const [selectedTask, setSelectedTask] = useState(null);
  const [taskImage, setTaskImage] = useState(null);
  const [uploadingImage, setUploadingImage] = useState(false);
  const [chatbotOpen, setChatbotOpen] = useState(false);
  const [chatbotMessages, setChatbotMessages] = useState([
    { role: "bot", text: "¡Hola! Soy Flowi, tu asistente de TaskFlow. ¿En qué puedo ayudarte hoy?" }
  ]);
  const [chatbotInput, setChatbotInput] = useState("");
  const [chatbotLoading, setChatbotLoading] = useState(false);
  const [pendingChatImage, setPendingChatImage] = useState(null);
  const taskInputRef = useRef(null);
  const startupTimeoutRef = useRef(null);

  useEffect(() => {
    startupTimeoutRef.current = setTimeout(() => setIsLoading(false), 3000);
    checkAuth().finally(() => clearTimeout(startupTimeoutRef.current));
    return () => clearTimeout(startupTimeoutRef.current);
  }, []);

  async function checkAuth() {
    try {
      const token = localStorage.getItem('tf_access_token');
      if (token) {
        const userData = await getMe();
        setUser(userData);
        await loadAllTasks();
      }
    } catch (e) {
      localStorage.removeItem('tf_access_token');
      localStorage.removeItem('tf_refresh_token');
    } finally {
      setIsLoading(false);
    }
  }

  function showMessage(text, type = "info") {
    setMessage({ text, type });
    setTimeout(() => setMessage(""), 5000);
  }

  async function loadAllTasks() {
    try {
      setIsLoading(true);
      const data = await listTasks();
      setTasks(data);
    } catch (e) {
      showMessage('Error: ' + e.message, "error");
    } finally {
      setIsLoading(false);
    }
  }

  function handleTaskFormChange(event) {
    const { name, value } = event.target;
    setTaskForm(current => ({...current, [name]: value}));
  }

  function handleLoginChange(event) {
    const { name, value } = event.target;
    setLoginForm(current => ({...current, [name]: value}));
  }

  function handleRegisterChange(event) {
    const { name, value } = event.target;
    setRegisterForm(current => ({...current, [name]: value}));
  }

  async function handleLogin(event) {
    event.preventDefault();
    try {
      const result = await loginUser(loginForm.username, loginForm.password);
      if (result.access_token) {
        const userData = await getMe();
        setUser(userData);
        setLoginForm(EMPTY_LOGIN);
        await loadAllTasks();
        showMessage(`Bienvenido ${userData.username}!`, "success");
      } else {
        setLoginStep("2fa");
        showMessage("Ingresa el código de 2FA", "info");
      }
    } catch (e) {
      showMessage('Error: ' + e.message, "error");
    }
  }

  async function handle2FALogin(event) {
    event.preventDefault();
    try {
      await login2FA(loginForm.username, totpCode);
      setLoginStep("credentials");
      setTotpCode("");
      const userData = await getMe();
      setUser(userData);
      await loadAllTasks();
      showMessage(`Bienvenido ${userData.username}!`, "success");
    } catch (e) {
      showMessage('Código incorrecto', "error");
    }
  }

  async function handleRegister(event) {
    event.preventDefault();
    try {
      await registerUser({ username: registerForm.username, password: registerForm.password });
      const userData = await getMe();
      setUser(userData);
      setRegisterForm(EMPTY_REGISTER);
      await loadAllTasks();
      showMessage(`Bienvenido ${userData.username}!`, "success");
    } catch (e) {
      showMessage('Error: ' + e.message, "error");
    }
  }

  async function handleLogout() {
    try {
      await logout();
      setUser(null);
      setTasks([]);
      setSelectedUser(null);
      setView("all");
      showMessage('Sesión cerrada.', "info");
    } catch (e) {
      setUser(null);
      setTasks([]);
    }
  }

  async function handleSubmit(event) {
    event.preventDefault();
    const title = taskForm.title.trim();
    if (!title) {
      showMessage('El título es obligatorio.', "error");
      return;
    }
    try {
      setIsSaving(true);
      setCreatingTask(true);
      await createTask({ title, description: taskForm.description.trim() });
      setTaskForm(EMPTY_FORM);
      showMessage('Tarea creada.', "success");
      await loadAllTasks();
      if (taskInputRef.current) taskInputRef.current.focus();
    } catch (e) {
      showMessage('Error: ' + e.message, "error");
    } finally {
      setIsSaving(false);
      setCreatingTask(false);
    }
  }

  async function handleToggleStatus(task, newStatus) {
    try {
      await changeTaskStatus(task.id, newStatus);
      setTasks(prev => prev.map(t => t.id === task.id ? { ...t, status: newStatus } : t));
      if (selectedTask && selectedTask.id === task.id) {
        setSelectedTask(prev => ({ ...prev, status: newStatus }));
      }
      if (newStatus === "done") {
        setCompletedTasks(prev => new Set([...prev, task.id]));
        setTimeout(() => {
          setCompletedTasks(prev => {
            const next = new Set(prev);
            next.delete(task.id);
            return next;
          });
        }, 500);
      }
      showMessage(`Estado actualizado a ${newStatus}.`, "success");
    } catch (e) {
      showMessage('Error: ' + e.message, "error");
      await loadAllTasks();
    }
  }

  async function handleDelete(taskId) {
    setDeletingTask(taskId);
    setTimeout(async () => {
      try {
        await deleteTask(taskId);
        showMessage('Tarea eliminada.', "success");
        await loadAllTasks();
      } catch (e) {
        showMessage('Error: ' + e.message, "error");
      } finally {
        setDeletingTask(null);
      }
    }, 300);
  }

  async function handleImageUpload(taskId, file) {
    try {
      setUploadingImage(true);
      await uploadTaskImage(taskId, file);
      showMessage('Imagen subida.', "success");
      await loadAllTasks();
      if (selectedTask && selectedTask.id === taskId) {
        setSelectedTask({ ...selectedTask, image: await getTaskImage(taskId) });
      }
    } catch (e) {
      showMessage('Error: ' + e.message, "error");
    } finally {
      setUploadingImage(false);
    }
  }

  function handleTaskClick(task) {
    setSelectedTask(task);
  }

  async function handleSetup2FA() {
    try {
      const data = await setup2FA();
      setQrCode(data.qr_code);
      setShow2FASetup(true);
      showMessage('Escanea el código QR con tu app de autenticación', "info");
    } catch (e) {
      showMessage('Error: ' + e.message, "error");
    }
  }

  async function handleEnable2FA() {
    try {
      await enable2FA(totpCode);
      setShow2FASetup(false);
      setQrCode(null);
      setTotpCode("");
      const userData = await getMe();
      setUser(userData);
      showMessage('2FA activado correctamente', "success");
    } catch (e) {
      showMessage('Código inválido', "error");
    }
  }

  async function handleDisable2FA() {
    try {
      await disable2FA(totpCode);
      setTotpCode("");
      const userData = await getMe();
      setUser(userData);
      showMessage('2FA desactivado', "success");
    } catch (e) {
      showMessage('Código inválido', "error");
    }
  }

  async function loadUsers() {
    try {
      const data = await getUsers();
      setUsers(data);
    } catch (e) {
      showMessage('Error: ' + e.message, "error");
    }
  }

  async function handleSelectUser(username) {
    try {
      const data = await getTasksByUser(username);
      setTasks(data);
      setSelectedUser({ username });
      setView("user");
    } catch (e) {
      showMessage('Error: ' + e.message, "error");
    }
  }

  async function handlePromote(username) {
    try {
      await promoteUser(username);
      showMessage(`Usuario ${username} promovido a admin`, "success");
      await loadUsers();
    } catch (e) {
      showMessage('Error: ' + e.message, "error");
    }
  }

  async function handleDemote(username) {
    try {
      await demoteUser(username);
      showMessage(`Usuario ${username} degradado a usuario`, "success");
      await loadUsers();
    } catch (e) {
      showMessage('Error: ' + e.message, "error");
    }
  }

  async function handleDeleteUser(targetUser) {
    if (!window.confirm(`Eliminar usuario ${targetUser.username}? Tambien se eliminaran sus tareas.`)) {
      return;
    }

    try {
      await deleteUser(targetUser.id);
      showMessage(`Usuario ${targetUser.username} eliminado`, "success");
      await loadUsers();
      await loadAllTasks();
    } catch (e) {
      showMessage('Error: ' + e.message, "error");
    }
  }

  async function handleChatbotSubmit(event) {
    event.preventDefault();
    const userMessage = chatbotInput.trim();
    if (!userMessage || chatbotLoading) return;
    
    setChatbotMessages(prev => [...prev, { role: "user", text: userMessage }]);
    setChatbotInput("");
    setChatbotLoading(true);
    
    try {
      const accessToken = localStorage.getItem('tf_access_token');
      const response = await fetch("/chatbot", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${accessToken}`,
        },
        body: JSON.stringify({ message: userMessage }),
      });
      
      const data = await response.json();
      setChatbotMessages(prev => [...prev, {
        role: "bot",
        text: data.response || "Lo siento, no pude procesar tu mensaje.",
        action: data.action,
        taskId: data.task_id,
      }]);
      if (pendingChatImage && data.action === "photo_upload" && data.task_id) {
        await uploadTaskImage(data.task_id, pendingChatImage);
        await loadAllTasks();
        setPendingChatImage(null);
        setChatbotMessages(prev => [...prev, {
          role: "bot",
          text: "Imagen subida correctamente.",
        }]);
      }
    } catch (e) {
      setChatbotMessages(prev => [...prev, { role: "bot", text: "Lo siento, ocurrió un error. Intenta de nuevo." }]);
    } finally {
      setChatbotLoading(false);
    }
  }

  async function handleChatbotImageUpload(taskId, file) {
    if (!file) return;

    try {
      setChatbotLoading(true);
      await uploadTaskImage(taskId, file);
      await loadAllTasks();
      setChatbotMessages(prev => [...prev, {
        role: "bot",
        text: "Imagen subida correctamente.",
      }]);
    } catch (e) {
      setChatbotMessages(prev => [...prev, {
        role: "bot",
        text: "No pude subir la imagen: " + e.message,
      }]);
    } finally {
      setChatbotLoading(false);
    }
  }

  async function handleChatbotPhotoPick(file) {
    if (!file) return;

    setPendingChatImage(file);
    setChatbotMessages(prev => [...prev, {
      role: "user",
      text: `Foto seleccionada: ${file.name}`,
    }]);
    setChatbotLoading(true);

    try {
      const accessToken = localStorage.getItem('tf_access_token');
      const response = await fetch("/chatbot", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${accessToken}`,
        },
        body: JSON.stringify({ message: "Agregale una foto" }),
      });

      const data = await response.json();
      setChatbotMessages(prev => [...prev, {
        role: "bot",
        text: data.response || "¿A cuál tarea quieres agregar esta foto? Dame el nombre o ID.",
        action: data.action,
        taskId: data.task_id,
      }]);
    } catch (e) {
      setPendingChatImage(null);
      setChatbotMessages(prev => [...prev, {
        role: "bot",
        text: "No pude preparar la subida de foto. Intenta de nuevo.",
      }]);
    } finally {
      setChatbotLoading(false);
    }
  }

  if (isLoading) {
    return (
      <div className="page" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '100vh', background: 'linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #0f172a 100%)' }}>
        <div style={{ textAlign: 'center', color: '#e2e8f0' }}>
          <div style={{ width: 60, height: 60, border: '3px solid #334155', borderTopColor: '#6366f1', borderRadius: '50%', animation: 'spin 1s linear infinite', margin: '0 auto 20px' }}></div>
          <p>Cargando TaskFlow...</p>
        </div>
      </div>
    );
  }

  return (
    <main className="page">
      {showBackgroundParticles && <div className="bg-particles">
        {[...Array(20)].map((_, i) => (
          <div key={i} className="particle" style={{
            left: Math.random() * 100 + '%',
            animationDelay: Math.random() * 5 + 's',
            animationDuration: (5 + Math.random() * 5) + 's'
          }}></div>
        ))}
      </div>}
      <section className="panel">
        <div className="hero">
          <div className="hero-icon">
            <div className="hero-icon-inner">
              <Sparkles size={32} />
            </div>
          </div>
          <p className="eyebrow">Gestión de Tareas</p>
          <h1>TaskFlow</h1>
          {user ? (
            <div className="user-welcome">
              <Zap size={16} className="welcome-icon" />
              <span>Hola, <strong>{user.username}</strong></span>
              {user.is_admin && <span className="badge-admin"><ShieldCheck size={12} /> Admin</span>}
              {user.is_2fa_enabled && <span className="badge-2fa"><Lock size={12} /> 2FA</span>}
            </div>
          ) : (
            <p className="hero-subtitle">Gestiona tus tareas de forma segura</p>
          )}
        </div>

        {message && (
          <div className={`message ${message.type}`}>
            {message.type === "error" && <AlertTriangle size={18} />}
            {message.type === "success" && <Check size={18} />}
            <span>{message.text}</span>
          </div>
        )}

        {!user ? (
          <div className="auth-container">
            <div className="auth-tabs">
              <button className={showLogin ? "active" : ""} onClick={() => { setShowLogin(true); setLoginStep("credentials"); }}>
                <LogOut size={16} /> Iniciar Sesión
              </button>
              <button className={!showLogin ? "active" : ""} onClick={() => { setShowLogin(false); setLoginStep("credentials"); }}>
                <User size={16} /> Registrarse
              </button>
            </div>

            {showLogin ? (
              loginStep === "2fa" ? (
                <form onSubmit={handle2FALogin} className="auth-form">
                  <div className="auth-icon">
                    <Shield size={32} />
                  </div>
                  <p>Verificación de dos factores</p>
                  <p className="auth-hint">Ingresa el código de 6 dígitos de tu app</p>
                  <input 
                    type="text" 
                    placeholder="000 000" 
                    value={totpCode} 
                    onChange={(e) => setTotpCode(e.target.value.replace(/\D/g, ''))}
                    maxLength={6}
                    autoFocus
                    required 
                  />
                  <button type="submit" className="btn-primary">
                    <ShieldCheck size={16} /> Verificar
                  </button>
                  <button type="button" className="secondary" onClick={() => { setLoginStep("credentials"); setTotpCode(""); }}>
                    <ArrowRight size={16} className="flip" /> Volver
                  </button>
                </form>
              ) : (
                <form onSubmit={handleLogin} className="auth-form">
                  <div className="auth-icon">
                    <Settings size={32} />
                  </div>
                  <input type="text" name="username" placeholder="Usuario" value={loginForm.username} onChange={handleLoginChange} required />
                  <input type="password" name="password" placeholder="Contraseña" value={loginForm.password} onChange={handleLoginChange} required />
                  <button type="submit" className="btn-primary">
                    <LogOut size={16} /> Entrar
                  </button>
                </form>
              )
            ) : (
              <form onSubmit={handleRegister} className="auth-form">
                <div className="auth-icon">
                  <User size={32} />
                </div>
                <input type="text" name="username" placeholder="Usuario" value={registerForm.username} onChange={handleRegisterChange} required />
                <input type="password" name="password" placeholder="Contraseña" value={registerForm.password} onChange={handleRegisterChange} required />
                <button type="submit" className="btn-primary">
                  <User size={16} /> Crear Cuenta
                </button>
              </form>
            )}
          </div>
        ) : (
          <>
            <div className="toolbar">
              <div className="toolbar-left">
                <span className="user-badge">
                  <User size={18} />
                  <strong>{user.username}</strong>
                </span>
              </div>
              <div className="toolbar-right">
                <button onClick={handleLogout} className="btn-icon" title="Cerrar Sesión">
                  <LogOut size={18} />
                </button>
                {user.is_2fa_enabled ? (
                  <button onClick={() => setShow2FASetup(true)} className="btn-secondary">
                    <ShieldCheck size={16} /> 2FA Activo
                  </button>
                ) : (
                  <button onClick={handleSetup2FA} className="btn-secondary">
                    <Shield size={16} /> Activar 2FA
                  </button>
                )}
                {user.is_admin && (
                  <button onClick={() => { loadUsers(); setView("admin"); setSelectedUser(null); }}>
                    <Users size={16} /> Admin
                  </button>
                )}
              </div>
            </div>

            {show2FASetup && (
              <div className="modal-overlay">
                <div className="modal">
                  <div className="modal-icon">
                    <ShieldCheck size={40} />
                  </div>
                  <h3>{user.is_2fa_enabled ? "Desactivar 2FA" : "Activar 2FA"}</h3>
                  {!user.is_2fa_enabled && qrCode && (
                    <div className="qr-container">
                      <img src={qrCode} alt="QR Code" />
                      <p>Escanea con Google Authenticator o similar</p>
                    </div>
                  )}
                  <input 
                    type="text" 
                    placeholder="Código de 6 dígitos" 
                    value={totpCode} 
                    onChange={(e) => setTotpCode(e.target.value)}
                    maxLength={6}
                  />
                  <div className="modal-buttons">
                    {user.is_2fa_enabled ? (
                      <button onClick={handleDisable2FA} className="btn-danger">
                        <Shield size={16} /> Desactivar
                      </button>
                    ) : (
                      <button onClick={handleEnable2FA} className="btn-primary">
                        <ShieldCheck size={16} /> Activar
                      </button>
                    )}
                    <button className="secondary" onClick={() => { setShow2FASetup(false); setQrCode(null); setTotpCode(""); }}>
                      Cancelar
                    </button>
                  </div>
                </div>
              </div>
            )}

            {view === "admin" && user.is_admin && (
              <div className="admin-panel">
                <div className="panel-header">
                  <Users size={24} />
                  <h2>Panel de Administrador</h2>
                </div>
                <div className="users-list">
                  {users.map(u => (
                    <div key={u.id} className="user-card">
                      <div className="user-info">
                        <div className="user-avatar">
                          <User size={20} />
                        </div>
                        <div>
                          <strong>{u.username}</strong>
                          <span>{u.is_admin ? "Administrador" : "Usuario"}</span>
                        </div>
                      </div>
                      <div className="user-actions">
                        <button onClick={() => handleSelectUser(u.username)} className="btn-icon-sm" title="Ver Tareas">
                          <CheckCircle size={16} />
                        </button>
                        {!u.is_admin ? (
                          <button onClick={() => handlePromote(u.username)} className="btn-secondary-sm">
                            <ArrowRight size={14} /> Promover
                          </button>
                        ) : (
                          <button onClick={() => handleDemote(u.username)} className="btn-secondary-sm">
                            <ArrowRight size={14} className="flip" /> Degradar
                          </button>
                        )}
                        {u.username !== user.username && (
                          <button onClick={() => handleDeleteUser(u)} className="btn-delete" title="Eliminar Usuario">
                            <Trash2 size={16} />
                          </button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
                <button className="secondary" onClick={() => { setView("all"); loadAllTasks(); }}>
                  <ArrowRight size={16} className="flip" /> Volver
                </button>
              </div>
            )}

            {view === "user" && selectedUser && (
              <div className="user-tasks-panel">
                <div className="panel-header">
                  <User size={24} />
                  <h2>Tareas de {selectedUser.username}</h2>
                </div>
                <button className="secondary" onClick={() => { setView("all"); setSelectedUser(null); loadAllTasks(); }}>
                  <ArrowRight size={16} className="flip" /> Volver
                </button>
              </div>
            )}

            {view === "all" || view === "user" ? (
              <>
                <form onSubmit={handleSubmit} className="task-form">
                  <div className="task-form-inner">
                    <input 
                      type="text" 
                      name="title" 
                      placeholder="Nueva tarea..." 
                      value={taskForm.title} 
                      onChange={handleTaskFormChange}
                      ref={taskInputRef}
                    />
                    <input 
                      type="text" 
                      name="description" 
                      placeholder="Descripción (opcional)" 
                      value={taskForm.description} 
                      onChange={handleTaskFormChange}
                    />
                    <button type="submit" disabled={isSaving} className={`btn-add ${creatingTask ? 'creating' : ''}`}>
                      {creatingTask ? <RotateCcw size={18} className="spin" /> : <Plus size={18} />}
                      {isSaving ? "Agregando..." : "Agregar"}
                    </button>
                  </div>
                </form>

                <div className="task-list">
                  {tasks.length === 0 ? (
                    <div className="empty-state">
                      <div className="empty-icon">
                        <Circle size={48} />
                      </div>
                      <p>No hay tareas todavía</p>
                      <p className="empty-hint">Crea tu primera tarea arriba</p>
                    </div>
                  ) : (
                    tasks.map((task, index) => (
                      <div 
                        key={task.id} 
                        className={`task ${task.status} ${deletingTask === task.id ? 'deleting' : ''} ${completedTasks.has(task.id) ? 'completed' : ''}`}
                        style={{ animationDelay: index * 0.05 + 's' }}
                        onClick={() => handleTaskClick(task)}
                      >
                        <div className="task-content">
                          <div className="task-title">
                            {task.status === "done" ? (
                              <CheckCircle size={18} className="done-icon" />
                            ) : task.status === "in_progress" ? (
                              <Activity size={18} className="progress-icon" />
                            ) : (
                              <Circle size={18} />
                            )}
                            <span>{task.title}</span>
                            {task.image && <Image size={14} className="task-has-image" />}
                          </div>
                          {task.description && <p>{task.description}</p>}
                          <small><Clock size={12} /> {task.owner}</small>
                        </div>
                        <div className="task-actions" onClick={e => e.stopPropagation()}>
                          <select 
                            value={task.status} 
                            onChange={(e) => handleToggleStatus(task, e.target.value)}
                            className="status-select"
                          >
                            <option value="todo">Pendiente</option>
                            <option value="in_progress">En Revisión</option>
                            <option value="done">Completado</option>
                          </select>
                          <button 
                            onClick={() => handleDelete(task.id)} 
                            className={`btn-delete ${deletingTask === task.id ? 'deleting' : ''}`}
                            title="Eliminar"
                          >
                            {deletingTask === task.id ? (
                              <RotateCcw size={16} className="spin" />
                            ) : (
                              <Trash2 size={16} />
                            )}
                          </button>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </>
            ) : null}

            {selectedTask && (
              <div className="task-detail-overlay" onClick={() => setSelectedTask(null)}>
                <div className="task-detail-modal" onClick={e => e.stopPropagation()}>
                  <button className="task-detail-close" onClick={() => setSelectedTask(null)}>
                    <X size={24} />
                  </button>
                  
                  <div className="task-detail-header">
                    <div className={`task-detail-status-badge ${selectedTask.status}`}>
                      {selectedTask.status === "done" ? <CheckCircle size={16} /> : 
                       selectedTask.status === "in_progress" ? <Activity size={16} /> :
                       <Circle size={16} />}
                      <span>{selectedTask.status === "todo" ? "Pendiente" : 
                             selectedTask.status === "in_progress" ? "En Revisión" : 
                             "Completado"}</span>
                    </div>
                  </div>
                  
                  <h2>{selectedTask.title}</h2>
                  
                  {selectedTask.description && (
                    <p className="task-detail-description">{selectedTask.description}</p>
                  )}
                  
                  <div className="task-detail-meta">
                    <span><User size={14} /> {selectedTask.owner}</span>
                    <span><Clock size={14} /> ID: {selectedTask.id}</span>
                  </div>
                  
                  <div className="task-detail-image-section">
                    <h3><Image size={16} /> Imagen</h3>
                    {selectedTask.image ? (
                      <div className="task-detail-image-preview">
                        <img src={selectedTask.image} alt="Task" />
                      </div>
                    ) : (
                      <p className="task-detail-no-image">No hay imagen</p>
                    )}
                    
                    <label className="task-detail-upload-btn">
                      {uploadingImage ? <RotateCcw size={16} className="spin" /> : <Camera size={16} />}
                      {uploadingImage ? "Subiendo..." : "Subir imagen"}
                      <input 
                        type="file" 
                        accept="image/*"
                        onChange={(e) => {
                          if (e.target.files[0]) {
                            handleImageUpload(selectedTask.id, e.target.files[0]);
                          }
                        }}
                        style={{ display: 'none' }}
                      />
                    </label>
                  </div>
                  
                  <div className="task-detail-actions">
                    <select 
                      value={selectedTask.status} 
                      onChange={async (e) => {
                        await handleToggleStatus(selectedTask, e.target.value);
                        setSelectedTask({ ...selectedTask, status: e.target.value });
                      }}
                      className="status-select"
                    >
                      <option value="todo">Pendiente</option>
                      <option value="in_progress">En Revisión</option>
                      <option value="done">Completado</option>
                    </select>
                    <button className="btn-danger" onClick={() => {
                      handleDelete(selectedTask.id);
                      setSelectedTask(null);
                    }}>
                      <Trash2 size={16} /> Eliminar
                    </button>
                  </div>
                </div>
              </div>
            )}

            <button className={`chatbot-fab ${chatbotOpen ? 'open' : ''}`} onClick={() => setChatbotOpen(!chatbotOpen)}>
              {chatbotOpen ? <X size={24} /> : <MessageSquare size={24} />}
            </button>

            {chatbotOpen && (
              <div className="chatbot-window">
                <div className="chatbot-header">
                  <div className="chatbot-header-info">
                    <div className="chatbot-avatar">
                      <Bot size={20} />
                    </div>
                    <div>
                      <h3>Flowi</h3>
                      <span>En línea</span>
                    </div>
                  </div>
                  <button className="chatbot-close" onClick={() => setChatbotOpen(false)}>
                    <X size={20} />
                  </button>
                </div>
                
                <div className="chatbot-messages">
                  {chatbotMessages.map((msg, i) => (
                    <div key={i} className={`chatbot-message ${msg.role}`}>
                      <div className="chatbot-bubble">
                        <div>{msg.text}</div>
                        {msg.action === "photo_upload" && msg.taskId && (
                          <label className="chatbot-upload-btn">
                            <Camera size={16} />
                            Subir foto
                            <input
                              type="file"
                              accept="image/*"
                              onChange={(e) => handleChatbotImageUpload(msg.taskId, e.target.files[0])}
                              style={{ display: 'none' }}
                            />
                          </label>
                        )}
                      </div>
                    </div>
                  ))}
                  {chatbotLoading && (
                    <div className="chatbot-message bot">
                      <div className="chatbot-typing">
                        <span></span>
                        <span></span>
                        <span></span>
                      </div>
                    </div>
                  )}
                </div>
                
                <form className="chatbot-input-area" onSubmit={handleChatbotSubmit}>
                  <label className={`chatbot-attach ${pendingChatImage ? 'has-file' : ''}`} title="Enviar foto">
                    <Camera size={18} />
                    <input
                      type="file"
                      accept="image/*"
                      onChange={(e) => {
                        handleChatbotPhotoPick(e.target.files[0]);
                        e.target.value = "";
                      }}
                      style={{ display: 'none' }}
                    />
                  </label>
                  <input 
                    type="text" 
                    className="chatbot-input"
                    placeholder="Escribe tu mensaje..."
                    value={chatbotInput}
                    onChange={(e) => setChatbotInput(e.target.value)}
                    disabled={chatbotLoading}
                  />
                  <button type="submit" className="chatbot-send" disabled={chatbotLoading || !chatbotInput.trim()}>
                    {chatbotLoading ? <Loader size={18} className="spin" /> : <Send size={18} />}
                  </button>
                </form>
              </div>
            )}
          </>
        )}
      </section>
    </main>
  );
}
