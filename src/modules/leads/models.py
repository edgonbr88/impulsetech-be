import uuid
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import String, Text, DateTime, ForeignKey, Numeric, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.core.database import Base


class Lead(Base):
    __tablename__ = "leads"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    nombre_contacto: Mapped[str] = mapped_column(String(150), nullable=False)
    empresa_o_proyecto: Mapped[str] = mapped_column(String(200), nullable=False)
    telefono_whatsapp: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    embudo: Mapped[str] = mapped_column(
        SQLEnum(
            "LEGAL_SAREN",
            "IA_AUTOMATIZACION",
            "SOFTWARE_MEDIDA",
            name="embudo_lead_enum",
            create_type=False,
        ),
        nullable=False,
        index=True,
    )
    etapa: Mapped[str] = mapped_column(
        SQLEnum(
            "NUEVO",
            "DIAGNOSTICO",
            "PROPUESTA",
            "NEGOCIACION",
            "GANADO",
            "PERDIDO",
            name="etapa_lead_enum",
            create_type=False,
        ),
        default="NUEVO",
        nullable=False,
        index=True,
    )
    motivo_perdida: Mapped[str | None] = mapped_column(Text, nullable=True)
    valor_estimado_usd: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )
    ejecutivo_asignado_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    cliente_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("clientes.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
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

    ejecutivo_asignado = relationship("Usuario", lazy="joined")
    cliente = relationship("Cliente", lazy="joined")
