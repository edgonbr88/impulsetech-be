import uuid
from datetime import datetime
from decimal import Decimal
from typing import Literal
from pydantic import BaseModel, EmailStr, ConfigDict


EmbudoLeadType = Literal["LEGAL_SAREN", "IA_AUTOMATIZACION", "SOFTWARE_MEDIDA"]
EtapaLeadType = Literal["NUEVO", "DIAGNOSTICO", "PROPUESTA", "NEGOCIACION", "GANADO", "PERDIDO"]


class EjecutivoLeadSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    nombre: str
    email: str


class ClienteLeadSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    razon_social: str
    rif_identificacion: str


class LeadBase(BaseModel):
    nombre_contacto: str
    empresa_o_proyecto: str
    telefono_whatsapp: str
    email: EmailStr
    embudo: EmbudoLeadType
    etapa: EtapaLeadType = "NUEVO"
    motivo_perdida: str | None = None
    valor_estimado_usd: Decimal = Decimal("0.00")
    ejecutivo_asignado_id: uuid.UUID
    cliente_id: uuid.UUID | None = None
    notas: str | None = None


class LeadCreate(LeadBase):
    pass


class LeadUpdate(BaseModel):
    nombre_contacto: str | None = None
    empresa_o_proyecto: str | None = None
    telefono_whatsapp: str | None = None
    email: EmailStr | None = None
    embudo: EmbudoLeadType | None = None
    etapa: EtapaLeadType | None = None
    motivo_perdida: str | None = None
    valor_estimado_usd: Decimal | None = None
    ejecutivo_asignado_id: uuid.UUID | None = None
    cliente_id: uuid.UUID | None = None
    notas: str | None = None


class LeadStageUpdate(BaseModel):
    etapa: EtapaLeadType
    motivo_perdida: str | None = None


class LeadResponse(LeadBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    ejecutivo_asignado: EjecutivoLeadSummary | None = None
    cliente: ClienteLeadSummary | None = None
