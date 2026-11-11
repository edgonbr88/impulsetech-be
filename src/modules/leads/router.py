import uuid
from typing import Sequence
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.database import get_db
from src.core.dependencies import get_current_user, require_admin
from src.modules.users.models import Usuario
from src.modules.leads.schemas import (
    LeadCreate,
    LeadUpdate,
    LeadStageUpdate,
    LeadResponse,
)
from src.modules.leads import service

router = APIRouter(prefix="/leads", tags=["Leads"])


@router.get("", response_model=Sequence[LeadResponse])
async def list_leads(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    embudo: str | None = Query(None, description="Filtro por embudo: LEGAL_SAREN, IA_AUTOMATIZACION, SOFTWARE_MEDIDA"),
    etapa: str | None = Query(None, description="Filtro por etapa: NUEVO, DIAGNOSTICO, PROPUESTA, NEGOCIACION, GANADO, PERDIDO"),
    ejecutivo_id: uuid.UUID | None = Query(None, description="Filtro por ejecutivo asignado"),
    solo_mi_cartera: bool = Query(False, description="Filtrar solo leads asignados al usuario actual"),
    search: str | None = Query(None, description="Búsqueda por contacto, empresa, email o teléfono"),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    target_ejecutivo_id = current_user.id if solo_mi_cartera else ejecutivo_id
    return await service.get_leads(
        db,
        skip=skip,
        limit=limit,
        embudo=embudo,
        etapa=etapa,
        ejecutivo_id=target_ejecutivo_id,
        search=search,
    )


@router.get("/{lead_id}", response_model=LeadResponse)
async def get_lead(
    lead_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return await service.get_lead_by_id(db, lead_id)


@router.post("", response_model=LeadResponse, status_code=status.HTTP_201_CREATED)
async def create_lead(
    lead_in: LeadCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return await service.create_lead(db, lead_in)


@router.put("/{lead_id}", response_model=LeadResponse)
async def update_lead(
    lead_id: uuid.UUID,
    lead_in: LeadUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return await service.update_lead(db, lead_id, lead_in)


@router.patch("/{lead_id}/stage", response_model=LeadResponse)
async def update_lead_stage(
    lead_id: uuid.UUID,
    stage_in: LeadStageUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return await service.update_lead_stage(db, lead_id, stage_in)


@router.delete("/{lead_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lead(
    lead_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_admin),
):
    await service.delete_lead(db, lead_id)
