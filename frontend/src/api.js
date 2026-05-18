const API_URL = import.meta.env.VITE_API_URL || "";

let accessToken = localStorage.getItem('tf_access_token') || "";
let refreshToken = localStorage.getItem('tf_refresh_token') || "";

function setTokens(access, refresh) {
  accessToken = access;
  refreshToken = refresh;
  localStorage.setItem('tf_access_token', access);
  localStorage.setItem('tf_refresh_token', refresh);
}

function clearTokens() {
  accessToken = "";
  refreshToken = "";
  localStorage.removeItem('tf_access_token');
  localStorage.removeItem('tf_refresh_token');
}

async function refreshAccessToken() {
  if (!refreshToken) throw new Error("No refresh token");
  
  const response = await fetch(`${API_URL}/refresh`, {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${refreshToken}`,
      "Content-Type": "application/json"
    }
  });
  
  if (!response.ok) {
    clearTokens();
    throw new Error("Session expired");
  }
  
  const data = await response.json();
  setTokens(data.access_token, data.refresh_token);
  return data.access_token;
}

async function request(path, options = {}, retry = true) {
  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
  };
  
  if (accessToken) {
    headers["Authorization"] = `Bearer ${accessToken}`;
  }
  
  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers,
  });
  
  if (response.status === 401 && retry && refreshToken) {
    try {
      accessToken = await refreshAccessToken();
      return request(path, options, false);
    } catch (e) {
      clearTokens();
      throw e;
    }
  }
  
  if (!response.ok) {
    let message = `Request failed with status ${response.status}`;
    try {
      const errorPayload = await response.json();
      message = errorPayload.detail || message;
    } catch {}
    throw new Error(message);
  }
  
  if (response.status === 204) return null;
  return response.json();
}

export function login(username, password) {
  const formData = new URLSearchParams();
  formData.append("username", username);
  formData.append("password", password);
  
  return fetch(`${API_URL}/login`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: formData,
  }).then(async res => {
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Login failed");
    
    if (data.access_token) {
      setTokens(data.access_token, data.refresh_token);
    }
    return data;
  });
}

export function login2FA(username, code) {
  return request("/login/2fa", {
    method: "POST",
    body: JSON.stringify({ username, code }),
  }, false).then(data => {
    if (data.access_token) {
      setTokens(data.access_token, data.refresh_token);
    }
    return data;
  });
}

export function logout() {
  return request("/logout", { method: "POST" }).finally(clearTokens);
}

export function register(payload) {
  return request("/register", {
    method: "POST",
    body: JSON.stringify(payload),
  }, false).then(data => {
    if (data.access_token) {
      setTokens(data.access_token, data.refresh_token);
    }
    return data;
  });
}

export const registerUser = register;

export const loginUser = login;

export function getMe() {
  return request("/me");
}

export function setup2FA() {
  return request("/2fa/setup", { method: "POST" });
}

export function enable2FA(code) {
  return request("/2fa/enable", {
    method: "POST",
    body: JSON.stringify({ username: "", code }),
  });
}

export function disable2FA(code) {
  return request("/2fa/disable", {
    method: "POST",
    body: JSON.stringify({ username: "", code }),
  });
}

export function listTasks() {
  return request("/tasks");
}

export function getTasksByUser(username) {
  return request(`/tasks/by_user/${encodeURIComponent(username)}`);
}

export function getUsers() {
  return request("/users");
}

export function createTask(payload) {
  return request("/tasks", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateTask(id, payload) {
  return request(`/tasks/${id}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export function changeTaskStatus(id, status) {
  return request(`/tasks/${id}/status?status=${encodeURIComponent(status)}`, {
    method: "PATCH",
  });
}

export function uploadTaskImage(taskId, file) {
  const formData = new FormData();
  formData.append("file", file);
  
  const headers = {};
  if (accessToken) headers["Authorization"] = `Bearer ${accessToken}`;

  return fetch(`${API_URL}/tasks/${taskId}/image`, {
    method: "POST",
    headers,
    body: formData,
  }).then(async res => {
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      throw new Error(data.detail || "Upload failed");
    }
    return res.json();
  });
}

export function getTaskImage(taskId) {
  const headers = {};
  if (accessToken) headers["Authorization"] = `Bearer ${accessToken}`;

  return fetch(`${API_URL}/tasks/${taskId}/image`, {
    headers,
  }).then(res => {
    if (!res.ok) return null;
    return res.blob();
  }).then(blob => {
    if (!blob) return null;
    return URL.createObjectURL(blob);
  });
}

export function deleteTask(id) {
  return request(`/tasks/${id}`, {
    method: "DELETE",
  });
}

export function promoteUser(username) {
  return request(`/admin/promote/${username}`, { method: "POST" });
}

export function demoteUser(username) {
  return request(`/admin/demote/${username}`, { method: "POST" });
}

export function deleteUser(id) {
  return request(`/users/${id}`, { method: "DELETE" });
}
