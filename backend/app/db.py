# Asignado: Copilot — estado: done
from sqlmodel import create_engine
import os
from dotenv import load_dotenv

load_dotenv()

# DATABASE_URL puede venir de entorno; por defecto usar la configuración actual
DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://root:123456789@localhost:3306/taskflow")
engine = create_engine(DATABASE_URL, echo=False)
