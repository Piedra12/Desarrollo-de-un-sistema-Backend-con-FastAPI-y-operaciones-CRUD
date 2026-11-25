from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sqlalchemy import event
from sqlmodel import Field as SQLField, Session, SQLModel, create_engine, select

# ==========================================
# BASE DE DATOS Y CLAVES FORÁNEAS EN SQLITE
# ==========================================
sqlite_url = "sqlite:///universidad.db"
engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})


@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
  cursor = dbapi_connection.cursor()
  cursor.execute("PRAGMA foreign_keys=ON")
  cursor.close()


# ==========================================
# MODELOS DE TABLAS (4 TABLAS RELACIONADAS)
# ==========================================
class Carrera(SQLModel, table=True):
  id: int | None = SQLField(default=None, primary_key=True)
  nombre: str = SQLField(min_length=2, max_length=100)
  descripcion: str = SQLField(min_length=3, max_length=255)


class Alumno(SQLModel, table=True):
  id: int | None = SQLField(default=None, primary_key=True)
  nombre: str = SQLField(min_length=2, max_length=120)
  edad: int = SQLField(gt=0, lt=120)
  carrera_id: int = SQLField(foreign_key="carrera.id")


class Materia(SQLModel, table=True):
  id: int | None = SQLField(default=None, primary_key=True)
  nombre: str = SQLField(min_length=2, max_length=120)
  creditos: int = SQLField(gt=0, le=30)


class Inscripcion(SQLModel, table=True):
  id: int | None = SQLField(default=None, primary_key=True)
  alumno_id: int = SQLField(foreign_key="alumno.id")
  materia_id: int = SQLField(foreign_key="materia.id")
  calificacion: float = SQLField(ge=0.0, le=10.0)


# ==========================================
# ESQUEMAS DE ENTRADA (VALIDACIÓN PYDANTIC)
# ==========================================
class CarreraCreate(BaseModel):
  nombre: str = Field(min_length=2, max_length=100)
  descripcion: str = Field(min_length=3, max_length=255)


class AlumnoCreate(BaseModel):
  nombre: str = Field(min_length=2, max_length=120)
  edad: int = Field(gt=0, lt=120)
  carrera_id: int = Field(gt=0)


class MateriaCreate(BaseModel):
  nombre: str = Field(min_length=2, max_length=120)
  creditos: int = Field(gt=0, le=30)


class InscripcionCreate(BaseModel):
  alumno_id: int = Field(gt=0)
  materia_id: int = Field(gt=0)
  calificacion: float = Field(ge=0.0, le=10.0)


# CREAR TABLAS
SQLModel.metadata.create_all(engine)

app = FastAPI(
    title="API Universidad - EduPanel",
    description=(
        "Sistema de gestión escolar con 4 tablas relacionadas y operaciones CRUD"
    ),
    version="1.0.0",
)

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", include_in_schema=False)
def inicio():
  return FileResponse("static/index.html")


def get_session():
  return Session(engine)


# ==========================================
# CRUD CARRERAS
# ==========================================
@app.post("/carreras/", status_code=201)
def crear_carrera(datos: CarreraCreate):
  with get_session() as session:
    carrera = Carrera(**datos.model_dump())
    session.add(carrera)
    session.commit()
    session.refresh(carrera)
    return carrera


@app.get("/carreras/")
def listar_carreras():
  with get_session() as session:
    return session.exec(select(Carrera)).all()


@app.get("/carreras/{id}")
def buscar_carrera(id: int):
  with get_session() as session:
    carrera = session.get(Carrera, id)
    if not carrera:
      raise HTTPException(status_code=404, detail="Carrera no encontrada")
    return carrera


@app.put("/carreras/{id}")
def actualizar_carrera(id: int, datos: CarreraCreate):
  with get_session() as session:
    carrera = session.get(Carrera, id)
    if not carrera:
      raise HTTPException(status_code=404, detail="Carrera no encontrada")
    carrera.nombre = datos.nombre
    carrera.descripcion = datos.descripcion
    session.add(carrera)
    session.commit()
    session.refresh(carrera)
    return carrera


@app.delete("/carreras/{id}")
def eliminar_carrera(id: int):
  with get_session() as session:
    carrera = session.get(Carrera, id)
    if not carrera:
      raise HTTPException(status_code=404, detail="Carrera no encontrada")

    alumno_vinculado = session.exec(
        select(Alumno).where(Alumno.carrera_id == id)
    ).first()
    if alumno_vinculado:
      raise HTTPException(
          status_code=400,
          detail=(
              "No se puede eliminar la carrera porque tiene alumnos inscritos"
          ),
      )

    session.delete(carrera)
    session.commit()
    return {"mensaje": "Carrera eliminada"}


# ==========================================
# CRUD ALUMNOS
# ==========================================
@app.post("/alumnos/", status_code=201)
def crear_alumno(datos: AlumnoCreate):
  with get_session() as session:
    if not session.get(Carrera, datos.carrera_id):
      raise HTTPException(status_code=404, detail="Carrera no encontrada")
    alumno = Alumno(**datos.model_dump())
    session.add(alumno)
    session.commit()
    session.refresh(alumno)
    return alumno


@app.get("/alumnos/")
def listar_alumnos():
  with get_session() as session:
    return session.exec(select(Alumno)).all()


@app.get("/alumnos/{id}")
def buscar_alumno(id: int):
  with get_session() as session:
    alumno = session.get(Alumno, id)
    if not alumno:
      raise HTTPException(status_code=404, detail="Alumno no encontrado")
    return alumno


@app.put("/alumnos/{id}")
def actualizar_alumno(id: int, datos: AlumnoCreate):
  with get_session() as session:
    alumno = session.get(Alumno, id)
    if not alumno:
      raise HTTPException(status_code=404, detail="Alumno no encontrado")
    if not session.get(Carrera, datos.carrera_id):
      raise HTTPException(status_code=404, detail="Carrera no encontrada")
    alumno.nombre = datos.nombre
    alumno.edad = datos.edad
    alumno.carrera_id = datos.carrera_id
    session.add(alumno)
    session.commit()
    session.refresh(alumno)
    return alumno


@app.delete("/alumnos/{id}")
def eliminar_alumno(id: int):
  with get_session() as session:
    alumno = session.get(Alumno, id)
    if not alumno:
      raise HTTPException(status_code=404, detail="Alumno no encontrado")

    inscripcion_vinculada = session.exec(
        select(Inscripcion).where(Inscripcion.alumno_id == id)
    ).first()
    if inscripcion_vinculada:
      raise HTTPException(
          status_code=400,
          detail=(
              "No se puede eliminar el alumno porque tiene inscripciones"
              " activas"
          ),
      )

    session.delete(alumno)
    session.commit()
    return {"mensaje": "Alumno eliminado"}


# ==========================================
# CRUD MATERIAS
# ==========================================
@app.post("/materias/", status_code=201)
def crear_materia(datos: MateriaCreate):
  with get_session() as session:
    materia = Materia(**datos.model_dump())
    session.add(materia)
    session.commit()
    session.refresh(materia)
    return materia


@app.get("/materias/")
def listar_materias():
  with get_session() as session:
    return session.exec(select(Materia)).all()


@app.get("/materias/{id}")
def buscar_materia(id: int):
  with get_session() as session:
    materia = session.get(Materia, id)
    if not materia:
      raise HTTPException(status_code=404, detail="Materia no encontrada")
    return materia


@app.put("/materias/{id}")
def actualizar_materia(id: int, datos: MateriaCreate):
  with get_session() as session:
    materia = session.get(Materia, id)
    if not materia:
      raise HTTPException(status_code=404, detail="Materia no encontrada")
    materia.nombre = datos.nombre
    materia.creditos = datos.creditos
    session.add(materia)
    session.commit()
    session.refresh(materia)
    return materia


@app.delete("/materias/{id}")
def eliminar_materia(id: int):
  with get_session() as session:
    materia = session.get(Materia, id)
    if not materia:
      raise HTTPException(status_code=404, detail="Materia no encontrada")

    inscripcion_vinculada = session.exec(
        select(Inscripcion).where(Inscripcion.materia_id == id)
    ).first()
    if inscripcion_vinculada:
      raise HTTPException(
          status_code=400,
          detail=(
              "No se puede eliminar la materia porque tiene alumnos inscritos"
          ),
      )

    session.delete(materia)
    session.commit()
    return {"mensaje": "Materia eliminada"}


# ==========================================
# CRUD INSCRIPCIONES
# ==========================================
@app.post("/inscripciones/", status_code=201)
def crear_inscripcion(datos: InscripcionCreate):
  with get_session() as session:
    if not session.get(Alumno, datos.alumno_id):
      raise HTTPException(status_code=404, detail="Alumno no encontrado")
    if not session.get(Materia, datos.materia_id):
      raise HTTPException(status_code=404, detail="Materia no encontrada")

    duplicada = session.exec(
        select(Inscripcion).where(
            Inscripcion.alumno_id == datos.alumno_id,
            Inscripcion.materia_id == datos.materia_id,
        )
    ).first()
    if duplicada:
      raise HTTPException(
          status_code=400,
          detail="El alumno ya está inscrito en esta materia",
      )

    inscripcion = Inscripcion(**datos.model_dump())
    session.add(inscripcion)
    session.commit()
    session.refresh(inscripcion)
    return inscripcion


@app.get("/inscripciones/")
def listar_inscripciones():
  with get_session() as session:
    return session.exec(select(Inscripcion)).all()


@app.get("/inscripciones/{id}")
def buscar_inscripcion(id: int):
  with get_session() as session:
    inscripcion = session.get(Inscripcion, id)
    if not inscripcion:
      raise HTTPException(status_code=404, detail="Inscripción no encontrada")
    return inscripcion


@app.put("/inscripciones/{id}")
def actualizar_inscripcion(id: int, datos: InscripcionCreate):
  with get_session() as session:
    inscripcion = session.get(Inscripcion, id)
    if not inscripcion:
      raise HTTPException(status_code=404, detail="Inscripción no encontrada")
    if not session.get(Alumno, datos.alumno_id):
      raise HTTPException(status_code=404, detail="Alumno no encontrado")
    if not session.get(Materia, datos.materia_id):
      raise HTTPException(status_code=404, detail="Materia no encontrada")

    duplicada = session.exec(
        select(Inscripcion).where(
            Inscripcion.alumno_id == datos.alumno_id,
            Inscripcion.materia_id == datos.materia_id,
            Inscripcion.id != id,
        )
    ).first()
    if duplicada:
      raise HTTPException(
          status_code=400,
          detail="El alumno ya está inscrito en esta materia",
      )

    inscripcion.alumno_id = datos.alumno_id
    inscripcion.materia_id = datos.materia_id
    inscripcion.calificacion = datos.calificacion
    session.add(inscripcion)
    session.commit()
    session.refresh(inscripcion)
    return inscripcion


@app.delete("/inscripciones/{id}")
def eliminar_inscripcion(id: int):
  with get_session() as session:
    inscripcion = session.get(Inscripcion, id)
    if not inscripcion:
      raise HTTPException(status_code=404, detail="Inscripción no encontrada")
    session.delete(inscripcion)
    session.commit()
    return {"mensaje": "Inscripción eliminada"}