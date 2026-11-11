import uuid
from datetime import datetime, date
from decimal import Decimal
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


TipoServicioType = Literal["LEGAL_SAREN", "IA_AUTOMATIZACION", "SOFTWARE_MEDIDA", "RETAINER_MENSUAL"]
ModalidadServicioType = Literal["PROYECTO_UNICO", "RECURRENTE_MENSUAL"]
EstadoOperativoServicioType = Literal["EN_ESPERA", "EN_DESARROLLO", "EN_REVISION", "ACTIVO_PRODUCCION", "FINALIZADO", "PAUSADO"]


class ClienteServicioSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    razon_social: str
    rif_identificacion: str


class ServicioBase(BaseModel):
    cliente_id: uuid.UUID
    tipo: TipoServicioType
    nombre_servicio: str
    modalidad: ModalidadServicioType = "PROYECTO_UNICO"
    estado_operativo: EstadoOperativoServicioType = "EN_ESPERA"
    especialista_responsable: str
    monto_pactado_usd: Decimal = Decimal("0.00")
    fecha_inicio: date
    fecha_entrega_estimada: date | None = None
    dia_corte_mensual: int | None = Field(default=None, ge=1, le=31)
    notas: str | None = None


class ServicioCreate(ServicioBase):
    pass


class ServicioUpdate(BaseModel):
    cliente_id: uuid.UUID | None = None
    tipo: TipoServicioType | None = None
    nombre_servicio: str | None = None
    modalidad: ModalidadServicioType | None = None
    estado_operativo: EstadoOperativoServicioType | None = None
    especialista_responsable: str | None = None
    monto_pactado_usd: Decimal | None = None
    fecha_inicio: date | None = None
    fecha_entrega_estimada: date | None = None
    dia_corte_mensual: int | None = Field(default=None, ge=1, le=31)
    notas: str | None = None


class ServicioStatusUpdate(BaseModel):
    estado_operativo: EstadoOperativoServicioType
    notas_actualizacion: str | None = None


class ServicioResponse(ServicioBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    cliente: ClienteServicioSummary | None = None
