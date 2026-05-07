import React from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import App from "./App";
import * as api from "./api";

vi.mock("./api", () => ({
  listTasks: vi.fn(),
  getTasksByUser: vi.fn(),
  getUsers: vi.fn(),
  createTask: vi.fn(),
  changeTaskStatus: vi.fn(),
  deleteTask: vi.fn(),
  registerUser: vi.fn(),
}));

describe("App", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
    api.listTasks.mockResolvedValue([]);
    api.getTasksByUser.mockResolvedValue([]);
    api.getUsers.mockResolvedValue([
      { id: 1, username: "ana" },
      { id: 2, username: "luis" },
    ]);
    api.createTask.mockResolvedValue({
      id: 10,
      title: "Nueva tarea",
      description: "Descripcion",
      status: "todo",
      owner: "ana",
    });
    api.changeTaskStatus.mockResolvedValue({});
    api.deleteTask.mockResolvedValue({ ok: true });
    api.registerUser.mockResolvedValue({ id: 1, username: "ana" });
  });

  afterEach(() => {
    cleanup();
  });

  it("carga tareas y usuarios al iniciar", async () => {
    api.listTasks.mockResolvedValueOnce([
      { id: 1, title: "Primera", description: "Demo", status: "todo", owner: null },
    ]);

    render(<App />);

    expect(await screen.findByText("Primera")).toBeInTheDocument();
    expect(await screen.findByRole("button", { name: "ana" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "luis" })).toBeInTheDocument();
  });

  it("registra un usuario y guarda la sesion local", async () => {
    const user = userEvent.setup();
    render(<App />);

    await user.type(screen.getByPlaceholderText("Usuario"), "ana");
    await user.type(screen.getByPlaceholderText("Contrasena"), "secreta");
    await user.click(screen.getByRole("button", { name: "Registrarse" }));

    await screen.findByText("Sesion iniciada como ana.");
    expect(localStorage.getItem("tf_username")).toBe("ana");
    expect(api.registerUser).toHaveBeenCalledWith({ username: "ana", password: "secreta" });
  });

  it("crea una tarea asociada al usuario actual", async () => {
    localStorage.setItem("tf_username", "ana");
    const user = userEvent.setup();
    render(<App />);

    await screen.findByText(/Conectado como/i);
    await user.type(screen.getByPlaceholderText("Ej. Preparar demo"), "Nueva tarea");
    await user.type(screen.getByPlaceholderText("Contexto breve de la tarea"), "Descripcion");
    await user.click(screen.getByRole("button", { name: "Crear tarea" }));

    await waitFor(() => {
      expect(api.createTask).toHaveBeenCalledWith({
        title: "Nueva tarea",
        description: "Descripcion",
        owner: "ana",
      });
    });
  });

  it("filtra tareas por el usuario actual", async () => {
    localStorage.setItem("tf_username", "ana");
    api.getTasksByUser.mockResolvedValueOnce([
      { id: 2, title: "Solo mia", description: "", status: "todo", owner: "ana" },
    ]);
    const user = userEvent.setup();
    render(<App />);

    await user.click(await screen.findByRole("button", { name: "Ver mis tareas" }));

    expect(await screen.findByText("Solo mia")).toBeInTheDocument();
    expect(api.getTasksByUser).toHaveBeenCalledWith("ana");
  });

  it("permite ver tareas de un usuario desde la vista admin", async () => {
    api.getTasksByUser.mockResolvedValueOnce([
      { id: 5, title: "Tarea de Luis", description: "", status: "todo", owner: "luis" },
    ]);
    const user = userEvent.setup();
    render(<App />);

    await user.click(await screen.findByRole("button", { name: "luis" }));

    expect(await screen.findByText("Tarea de Luis")).toBeInTheDocument();
    expect(api.getTasksByUser).toHaveBeenCalledWith("luis");
    expect(screen.getByRole("heading", { name: "Tareas de luis" })).toBeInTheDocument();
  });

  it("cambia el estado y elimina una tarea", async () => {
    api.listTasks.mockResolvedValue([
      { id: 3, title: "Revisar", description: "", status: "todo", owner: null },
    ]);
    const user = userEvent.setup();
    render(<App />);

    await screen.findByText("Revisar");
    await user.click(screen.getByRole("button", { name: "Marcar hecha" }));
    await waitFor(() => {
      expect(api.changeTaskStatus).toHaveBeenCalledWith(3, "done");
    });

    await user.click(screen.getByRole("button", { name: "Eliminar" }));
    await waitFor(() => {
      expect(api.deleteTask).toHaveBeenCalledWith(3);
    });
  });
});
