import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict, model_validator

from src.modules.payments.models import MonedaPago, MedioPago, ConceptoPago, EstadoPago


class PagoBase(BaseModel):
    cliente_id: uuid.UUID
    servicio_id: Optional[uuid.UUID] = None
    monto: Decimal = Field(..., gt=0, max_digits=12, decimal_places=2)
    moneda: MonedaPago
    tasa_cambio_bcv: Optional[Decimal] = Field(None, max_digits=12, decimal_places=4)
    medio_pago: MedioPago
    referencia_bancaria: Optional[str] = Field(None, max_length=100)
    concepto: ConceptoPago = ConceptoPago.ANTICIPO_50
    fecha_pago: date = Field(default_factory=date.today)
    comprobante_url: Optional[str] = Field(None, max_length=500)
    notas: Optional[str] = None

    @model_validator(mode="after")
    def validate_ves_requires_tasa_bcv(self):
        if self.moneda == MonedaPago.VES:
            if self.tasa_cambio_bcv is None or self.tasa_cambio_bcv <= 0:
                raise ValueError("Para pagos en moneda VES es obligatoria la tasa_cambio_bcv mayor a 0")
        return self


class PagoCreate(PagoBase):
    pass


class PagoStatusUpdate(BaseModel):
    estado_pago: EstadoPago
    notas: Optional[str] = None


class PagoResponse(PagoBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    estado_pago: EstadoPago
    created_at: datetime
    updated_at: datetime
    cliente_nombre: Optional[str] = None
    servicio_nombre: Optional[str] = None
    monto_equivalente_usd: Decimal = Field(..., description="Monto normalizado a USD calculado")


class PagoSummary(BaseModel):
    total_verificado_usd: Decimal
    total_pendiente_usd: Decimal
    total_rechazado_usd: Decimal
    conteo_verificados: int
    conteo_pendientes: int
    conteo_rechazados: int
    desglose_por_moneda: dict
