import enum
import uuid
from datetime import date, datetime
from typing import Optional
from sqlalchemy import (
    Column,
    String,
    Text,
    Numeric,
    Date,
    DateTime,
    ForeignKey,
    Enum as SQLEnum,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.core.database import Base


class MonedaPago(str, enum.Enum):
    USD = "USD"
    VES = "VES"
    USDT = "USDT"


class MedioPago(str, enum.Enum):
    ZELLE = "ZELLE"
    PAGO_MOVIL = "PAGO_MOVIL"
    USDT_BINANCE = "USDT_BINANCE"
    EFECTIVO_USD = "EFECTIVO_USD"
    TRANSFERENCIA_VES = "TRANSFERENCIA_VES"


class ConceptoPago(str, enum.Enum):
    ANTICIPO_50 = "ANTICIPO_50"
    FINIQUITO = "FINIQUITO"
    CUOTA_RETAINER = "CUOTA_RETAINER"
    OTRO = "OTRO"


class EstadoPago(str, enum.Enum):
    PENDIENTE = "PENDIENTE"
    VERIFICADO = "VERIFICADO"
    RECHAZADO = "RECHAZADO"


class Pago(Base):
    __tablename__ = "pagos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cliente_id = Column(UUID(as_uuid=True), ForeignKey("clientes.id", ondelete="RESTRICT"), nullable=False, index=True)
    servicio_id = Column(UUID(as_uuid=True), ForeignKey("servicios.id", ondelete="SET NULL"), nullable=True, index=True)
    monto = Column(Numeric(12, 2), nullable=False)
    moneda = Column(
        SQLEnum(MonedaPago, name="moneda_pago_enum", create_type=False),
        nullable=False,
        index=True
    )
    tasa_cambio_bcv = Column(Numeric(12, 4), nullable=True)
    medio_pago = Column(
        SQLEnum(MedioPago, name="medio_pago_enum", create_type=False),
        nullable=False
    )
    referencia_bancaria = Column(String(100), nullable=True)
    concepto = Column(
        SQLEnum(ConceptoPago, name="concepto_pago_enum", create_type=False),
        nullable=False,
        default=ConceptoPago.ANTICIPO_50
    )
    estado_pago = Column(
        SQLEnum(EstadoPago, name="estado_pago_enum", create_type=False),
        nullable=False,
        default=EstadoPago.PENDIENTE,
        index=True
    )
    fecha_pago = Column(Date, nullable=False, default=date.today, index=True)
    comprobante_url = Column(String(500), nullable=True)
    notas = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    cliente = relationship("Cliente", backref="pagos", lazy="joined")
    servicio = relationship("Servicio", backref="pagos", lazy="joined")
