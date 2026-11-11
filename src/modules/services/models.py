import uuid
from datetime import datetime, date, timezone
from decimal import Decimal
from sqlalchemy import String, Text, DateTime, Date, SmallInteger, ForeignKey, Numeric, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.core.database import Base


class Servicio(Base):
    __tablename__ = "servicios"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    cliente_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("clientes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tipo: Mapped[str] = mapped_column(
        SQLEnum(
            "LEGAL_SAREN",
            "IA_AUTOMATIZACION",
            "SOFTWARE_MEDIDA",
            "RETAINER_MENSUAL",
            name="tipo_servicio_enum",
            create_type=False,
        ),
        nullable=False,
        index=True,
    )
    nombre_servicio: Mapped[str] = mapped_column(String(200), nullable=False)
    modalidad: Mapped[str] = mapped_column(
        SQLEnum(
            "PROYECTO_UNICO",
            "RECURRENTE_MENSUAL",
            name="modalidad_servicio_enum",
            create_type=False,
        ),
        default="PROYECTO_UNICO",
        nullable=False,
        index=True,
    )
    estado_operativo: Mapped[str] = mapped_column(
        SQLEnum(
            "EN_ESPERA",
            "EN_DESARROLLO",
            "EN_REVISION",
            "ACTIVO_PRODUCCION",
            "FINALIZADO",
            "PAUSADO",
            name="estado_operativo_servicio_enum",
            create_type=False,
        ),
        default="EN_ESPERA",
        nullable=False,
        index=True,
    )
    especialista_responsable: Mapped[str] = mapped_column(String(150), nullable=False)
    monto_pactado_usd: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )
    fecha_inicio: Mapped[date] = mapped_column(
        Date, default=lambda: datetime.now(timezone.utc).date(), nullable=False
    )
    fecha_entrega_estimada: Mapped[date | None] = mapped_column(Date, nullable=True)
    dia_corte_mensual: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    notas: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    cliente = relationship("Cliente", lazy="joined")
