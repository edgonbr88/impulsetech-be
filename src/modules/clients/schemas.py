import uuid
from datetime import datetime
from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Literal


EstadoClienteType = Literal["ACTIVO", "INACTIVO", "MOROSO"]


class EjecutivoSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    nombre: str
    email: str


class ClienteBase(BaseModel):
    razon_social: str
    rif_identificacion: str
    contacto_principal: str
    telefono_whatsapp: str
    email: EmailStr
    direccion_ciudad: str | None = None
    ejecutivo_id: uuid.UUID
    estado: EstadoClienteType = "ACTIVO"
    notas: str | None = None


class ClienteCreate(ClienteBase):
    pass


class ClienteUpdate(BaseModel):
    razon_social: str | None = None
    rif_identificacion: str | None = None
    contacto_principal: str | None = None
    telefono_whatsapp: str | None = None
    email: EmailStr | None = None
    direccion_ciudad: str | None = None
    ejecutivo_id: uuid.UUID | None = None
    estado: EstadoClienteType | None = None
    notas: str | None = None


class ClienteResponse(ClienteBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    ejecutivo: EjecutivoSummary | None = None
