const API = "";
let usuarioActual = "";
let paginaActual = "dashboard";
let registros = [];
let registroEditando = null;
let listasAuxiliares = { carreras: [], alumnos: [], materias: [] };

const configuracion = {
    carreras: {
        titulo: "Carreras",
        descripcion: "Administración de carreras",
        endpoint: "/carreras/",
        campos: [
            { key: "nombre", label: "Nombre", type: "text" },
            { key: "descripcion", label: "Descripción", type: "text" }
        ]
    },
    alumnos: {
        titulo: "Alumnos",
        descripcion: "Administración de alumnos",
        endpoint: "/alumnos/",
        campos: [
            { key: "nombre", label: "Nombre", type: "text" },
            { key: "edad", label: "Edad", type: "number" },
            { key: "carrera_id", label: "Carrera", type: "select-carrera" }
        ]
    },
    materias: {
        titulo: "Materias",
        descripcion: "Administración de materias",
        endpoint: "/materias/",
        campos: [
            { key: "nombre", label: "Nombre", type: "text" },
            { key: "creditos", label: "Créditos", type: "number" }
        ]
    },
    inscripciones: {
        titulo: "Inscripciones",
        descripcion: "Administración de inscripciones",
        endpoint: "/inscripciones/",
        campos: [
            { key: "alumno_id", label: "Alumno", type: "select-alumno" },
            { key: "materia_id", label: "Materia", type: "select-materia" },
            { key: "calificacion", label: "Calificación", type: "number" }
        ]
    }
};

// LOGIN
document.getElementById("loginForm").addEventListener("submit", function (e) {
    e.preventDefault();
    const usuario = document.getElementById("username").value.trim();
    const password = document.getElementById("password").value;
    if (!usuario || !password) return alert("Completa todos los campos");

    usuarioActual = usuario;
    document.getElementById("loginScreen").classList.add("hidden");
    document.getElementById("appScreen").classList.remove("hidden");
    document.getElementById("userDisplay").textContent = usuario;
    document.getElementById("topUser").textContent = usuario;
    mostrarDashboard();
});

// CERRAR SESIÓN
document.getElementById("logoutBtn").addEventListener("click", function () {
    usuarioActual = "";
    document.getElementById("appScreen").classList.add("hidden");
    document.getElementById("loginScreen").classList.remove("hidden");
    document.getElementById("loginForm").reset();
});

// NAVEGACIÓN
document.querySelectorAll(".nav-btn").forEach(btn => {
    btn.addEventListener("click", () => {
        document.querySelectorAll(".nav-btn").forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
        cambiarPagina(btn.dataset.page);
    });
});

function cambiarPagina(pagina) {
    paginaActual = pagina;
    document.getElementById("dashboardPage").classList.add("hidden");
    document.getElementById("dataPage").classList.add("hidden");
    document.getElementById("formArea").classList.add("hidden");
    document.getElementById("message").textContent = "";

    if (pagina === "dashboard") {
        mostrarDashboard();
    } else {
        document.getElementById("dataPage").classList.remove("hidden");
        cargarTabla(pagina);
    }

    document.getElementById("pageTitle").textContent =
        pagina === "dashboard" ? "Inicio" : configuracion[pagina].titulo;
}

// CARGAR DATOS AUXILIARES
async function cargarDatosAuxiliares() {
    try {
        const [resCarreras, resAlumnos, resMaterias] = await Promise.all([
            fetch(API + "/carreras/"),
            fetch(API + "/alumnos/"),
            fetch(API + "/materias/")
        ]);
        listasAuxiliares.carreras = await resCarreras.json();
        listasAuxiliares.alumnos = await resAlumnos.json();
        listasAuxiliares.materias = await resMaterias.json();
    } catch (error) {
        console.error("Error cargando catálogos:", error);
    }
}

// DASHBOARD
async function mostrarDashboard() {
    document.getElementById("dashboardPage").classList.remove("hidden");
    await actualizarEstadisticas();
}

// CONSULTAR REGISTROS
async function cargarTabla(pagina, limpiarMensaje = true) {
    const config = configuracion[pagina];
    document.getElementById("tableTitle").textContent = config.titulo;
    document.getElementById("tableDescription").textContent = config.descripcion;

    await cargarDatosAuxiliares();

    try {
        const response = await fetch(API + config.endpoint);
        if (!response.ok) throw new Error("No se pudieron consultar los datos");
        registros = await response.json();
        dibujarTabla(config, limpiarMensaje);
    } catch (error) {
        mostrarMensaje(error.message, true);
    }
}

// DIBUJAR TABLA
function dibujarTabla(config, limpiarMensaje = true) {
    const head = document.getElementById("tableHead");
    const body = document.getElementById("tableBody");

    head.innerHTML = `
        <tr>
            <th>ID</th>
            ${config.campos.map(c => `<th>${c.label}</th>`).join("")}
            <th>Acciones</th>
        </tr>
    `;

    body.innerHTML = registros.map(registro => `
        <tr>
            <td>${registro.id}</td>
            ${config.campos.map(c => {
                let valor = registro[c.key] ?? "";
                if (c.key === "carrera_id") {
                    const obj = listasAuxiliares.carreras.find(x => x.id === valor);
                    valor = obj ? obj.nombre : valor;
                } else if (c.key === "alumno_id") {
                    const obj = listasAuxiliares.alumnos.find(x => x.id === valor);
                    valor = obj ? obj.nombre : valor;
                } else if (c.key === "materia_id") {
                    const obj = listasAuxiliares.materias.find(x => x.id === valor);
                    valor = obj ? obj.nombre : valor;
                }
                return `<td>${valor}</td>`;
            }).join("")}
            <td>
                <button class="action-btn edit-btn" data-action="edit" data-id="${registro.id}">Editar</button>
                <button class="action-btn delete-btn" data-action="delete" data-id="${registro.id}">Eliminar</button>
            </td>
        </tr>
    `).join("");

    if (limpiarMensaje) {
        document.getElementById("message").textContent = "";
    }
}

// ABRIR FORMULARIO
document.getElementById("addBtn").addEventListener("click", () => abrirFormulario());

async function abrirFormulario(registro = null) {
    registroEditando = registro;
    await cargarDatosAuxiliares();

    const config = configuracion[paginaActual];
    const area = document.getElementById("formArea");
    area.classList.remove("hidden");

    area.innerHTML = `
        <h3>${registro ? "Editar registro" : "Nuevo registro"}</h3>
        <form id="registroForm">
            ${config.campos.map(c => {
                let inputHTML = "";
                const valActual = registro ? registro[c.key] ?? "" : "";

                if (c.type === "select-carrera") {
                    inputHTML = `<select name="${c.key}" required>
                        <option value="">Seleccione una carrera...</option>
                        ${listasAuxiliares.carreras.map(car => `<option value="${car.id}" ${valActual === car.id ? "selected" : ""}>${car.nombre}</option>`).join("")}
                    </select>`;
                } else if (c.type === "select-alumno") {
                    inputHTML = `<select name="${c.key}" required>
                        <option value="">Seleccione un alumno...</option>
                        ${listasAuxiliares.alumnos.map(alu => `<option value="${alu.id}" ${valActual === alu.id ? "selected" : ""}>${alu.nombre}</option>`).join("")}
                    </select>`;
                } else if (c.type === "select-materia") {
                    inputHTML = `<select name="${c.key}" required>
                        <option value="">Seleccione una materia...</option>
                        ${listasAuxiliares.materias.map(mat => `<option value="${mat.id}" ${valActual === mat.id ? "selected" : ""}>${mat.nombre}</option>`).join("")}
                    </select>`;
                } else {
                    inputHTML = `<input name="${c.key}" type="${c.type}" ${c.type === "number" ? 'step="any"' : ""} value="${valActual}" required>`;
                }

                return `<label>${c.label}</label>${inputHTML}`;
            }).join("")}

            <div class="form-actions" style="margin-top: 15px;">
                <button class="primary-btn" type="submit">${registro ? "Guardar cambios" : "Guardar registro"}</button>
                <button class="secondary-btn" type="button" id="cancelBtn">Cancelar</button>
            </div>
        </form>
    `;

    document.getElementById("registroForm").addEventListener("submit", guardarRegistro);
    document.getElementById("cancelBtn").addEventListener("click", () => {
        area.classList.add("hidden");
        registroEditando = null;
    });
}

// GUARDAR / ACTUALIZAR
async function guardarRegistro(e) {
    e.preventDefault();
    const config = configuracion[paginaActual];
    const formData = new FormData(e.target);
    const datos = {};

    config.campos.forEach(c => {
        const valor = formData.get(c.key);
        datos[c.key] = (c.type === "number" || c.type.startsWith("select-")) ? Number(valor) : valor;
    });

    const editando = registroEditando !== null;
    const url = API + config.endpoint + (editando ? registroEditando.id : "");

    try {
        const response = await fetch(url, {
            method: editando ? "PUT" : "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(datos)
        });

        if (!response.ok) {
            const errJson = await response.json();
            const detalle = Array.isArray(errJson.detail)
                ? errJson.detail.map(d => d.msg).join(", ")
                : (errJson.detail || "No se pudo guardar");
            throw new Error(detalle);
        }

        document.getElementById("formArea").classList.add("hidden");
        registroEditando = null;
        await cargarTabla(paginaActual, false);
        await actualizarEstadisticas();
        mostrarMensaje(editando ? "Registro actualizado con éxito" : "Registro creado con éxito");
    } catch (error) {
        mostrarMensaje(error.message, true);
    }
}

// EDITAR / ELIMINAR
document.getElementById("tableBody").addEventListener("click", async e => {
    const boton = e.target.closest("button[data-action]");
    if (!boton) return;

    const id = Number(boton.dataset.id);
    const accion = boton.dataset.action;
    const registro = registros.find(r => r.id === id);

    if (accion === "edit") abrirFormulario(registro);

    if (accion === "delete") {
        if (!confirm("¿Deseas eliminar este registro?")) return;
        const config = configuracion[paginaActual];

        try {
            const response = await fetch(API + config.endpoint + id, { method: "DELETE" });
            if (!response.ok) {
                const errJson = await response.json();
                throw new Error(errJson.detail || "No se pudo eliminar");
            }
            await cargarTabla(paginaActual, false);
            await actualizarEstadisticas();
            mostrarMensaje("Registro eliminado correctamente");
        } catch (error) {
            mostrarMensaje(error.message, true);
        }
    }
});

// ACTUALIZAR ESTADÍSTICAS
async function actualizarEstadisticas() {
    const endpoints = [
        ["alumnos", "/alumnos/"],
        ["carreras", "/carreras/"],
        ["materias", "/materias/"],
        ["inscripciones", "/inscripciones/"]
    ];

    try {
        for (const [nombre, endpoint] of endpoints) {
            const response = await fetch(API + endpoint);
            const datos = await response.json();
            const id = "stat" + nombre.charAt(0).toUpperCase() + nombre.slice(1);
            const el = document.getElementById(id);
            if (el) el.textContent = datos.length;
        }
    } catch (error) {
        console.error(error);
    }
}

function mostrarMensaje(texto, error = false) {
    const mensaje = document.getElementById("message");
    mensaje.textContent = texto;
    mensaje.style.color = error ? "#c44242" : "#27865d";
}