import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Text, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.core.database import Base


class Cliente(Base):
    __tablename__ = "clientes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    razon_social: Mapped[str] = mapped_column(String(255), nullable=False)
    rif_identificacion: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    contacto_principal: Mapped[str] = mapped_column(String(150), nullable=False)
    telefono_whatsapp: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    direccion_ciudad: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ejecutivo_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    estado: Mapped[str] = mapped_column(
        SQLEnum("ACTIVO", "INACTIVO", "MOROSO", name="estado_cliente_enum", create_type=False),
        default="ACTIVO",
        nullable=False,
        index=True
    )
    notas: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    ejecutivo = relationship("Usuario", lazy="joined")
