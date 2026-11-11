import uuid
from typing import Sequence
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from src.modules.leads.models import Lead
from src.modules.leads.schemas import LeadCreate, LeadUpdate, LeadStageUpdate
from src.modules.users.models import Usuario
from src.modules.clients.models import Cliente


async def get_leads(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    embudo: str | None = None,
    etapa: str | None = None,
    ejecutivo_id: uuid.UUID | None = None,
    search: str | None = None,
) -> Sequence[Lead]:
    query = select(Lead)

    if embudo:
        query = query.filter(Lead.embudo == embudo)

    if etapa:
        query = query.filter(Lead.etapa == etapa)

    if ejecutivo_id:
        query = query.filter(Lead.ejecutivo_asignado_id == ejecutivo_id)

    if search:
        search_filter = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Lead.nombre_contacto.ilike(search_filter),
                Lead.empresa_o_proyecto.ilike(search_filter),
                Lead.email.ilike(search_filter),
                Lead.telefono_whatsapp.ilike(search_filter),
            )
        )

    query = query.order_by(Lead.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


async def get_lead_by_id(db: AsyncSession, lead_id: uuid.UUID) -> Lead:
    query = select(Lead).filter(Lead.id == lead_id)
    result = await db.execute(query)
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead no encontrado",
        )
    return lead


async def create_lead(db: AsyncSession, lead_in: LeadCreate) -> Lead:
    # 1. Validar que el ejecutivo existe
    ejecutivo = await db.execute(
        select(Usuario).filter(Usuario.id == lead_in.ejecutivo_asignado_id)
    )
    if not ejecutivo.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El ejecutivo comercial asignado no existe",
        )

    # 2. Si se asocia a un cliente existente, validar que exista
    if lead_in.cliente_id:
        cliente = await db.execute(
            select(Cliente).filter(Cliente.id == lead_in.cliente_id)
        )
        if not cliente.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El cliente asociado no existe",
            )

    nuevo_lead = Lead(
        nombre_contacto=lead_in.nombre_contacto.strip(),
        empresa_o_proyecto=lead_in.empresa_o_proyecto.strip(),
        telefono_whatsapp=lead_in.telefono_whatsapp.strip(),
        email=lead_in.email.strip().lower(),
        embudo=lead_in.embudo,
        etapa=lead_in.etapa,
        motivo_perdida=lead_in.motivo_perdida.strip() if lead_in.motivo_perdida else None,
        valor_estimado_usd=lead_in.valor_estimado_usd,
        ejecutivo_asignado_id=lead_in.ejecutivo_asignado_id,
        cliente_id=lead_in.cliente_id,
        notas=lead_in.notas.strip() if lead_in.notas else None,
    )
    db.add(nuevo_lead)
    await db.commit()
    await db.refresh(nuevo_lead)
    return await get_lead_by_id(db, nuevo_lead.id)


async def update_lead(db: AsyncSession, lead_id: uuid.UUID, lead_in: LeadUpdate) -> Lead:
    lead = await get_lead_by_id(db, lead_id)

    if lead_in.ejecutivo_asignado_id and lead_in.ejecutivo_asignado_id != lead.ejecutivo_asignado_id:
        ejecutivo = await db.execute(
            select(Usuario).filter(Usuario.id == lead_in.ejecutivo_asignado_id)
        )
        if not ejecutivo.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El nuevo ejecutivo asignado no existe",
            )
        lead.ejecutivo_asignado_id = lead_in.ejecutivo_asignado_id

    if lead_in.cliente_id and lead_in.cliente_id != lead.cliente_id:
        cliente = await db.execute(
            select(Cliente).filter(Cliente.id == lead_in.cliente_id)
        )
        if not cliente.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El cliente asociado no existe",
            )
        lead.cliente_id = lead_in.cliente_id

    if lead_in.nombre_contacto is not None:
        lead.nombre_contacto = lead_in.nombre_contacto.strip()
    if lead_in.empresa_o_proyecto is not None:
        lead.empresa_o_proyecto = lead_in.empresa_o_proyecto.strip()
    if lead_in.telefono_whatsapp is not None:
        lead.telefono_whatsapp = lead_in.telefono_whatsapp.strip()
    if lead_in.email is not None:
        lead.email = lead_in.email.strip().lower()
    if lead_in.embudo is not None:
        lead.embudo = lead_in.embudo
    if lead_in.etapa is not None:
        lead.etapa = lead_in.etapa
    if lead_in.motivo_perdida is not None:
        lead.motivo_perdida = lead_in.motivo_perdida.strip() if lead_in.motivo_perdida else None
    if lead_in.valor_estimado_usd is not None:
        lead.valor_estimado_usd = lead_in.valor_estimado_usd
    if lead_in.notas is not None:
        lead.notas = lead_in.notas.strip() if lead_in.notas else None

    await db.commit()
    await db.refresh(lead)
    return await get_lead_by_id(db, lead.id)


async def update_lead_stage(
    db: AsyncSession, lead_id: uuid.UUID, stage_in: LeadStageUpdate
) -> Lead:
    lead = await get_lead_by_id(db, lead_id)
    lead.etapa = stage_in.etapa
    if stage_in.etapa == "PERDIDO":
        lead.motivo_perdida = stage_in.motivo_perdida.strip() if stage_in.motivo_perdida else "No especificado"
    elif stage_in.etapa != "PERDIDO":
        lead.motivo_perdida = None

    await db.commit()
    await db.refresh(lead)
    return await get_lead_by_id(db, lead.id)


async def delete_lead(db: AsyncSession, lead_id: uuid.UUID) -> None:
    lead = await get_lead_by_id(db, lead_id)
    await db.delete(lead)
    await db.commit()
