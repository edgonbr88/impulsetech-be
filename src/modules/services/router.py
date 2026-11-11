import uuid
from typing import Sequence
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.database import get_db
from src.core.dependencies import get_current_user, require_admin
from src.modules.users.models import Usuario
from src.modules.services.schemas import (
    ServicioCreate,
    ServicioUpdate,
    ServicioStatusUpdate,
    ServicioResponse,
)
from src.modules.services import service

router = APIRouter(prefix="/services", tags=["Servicios Operativos"])


@router.get("", response_model=Sequence[ServicioResponse])
async def list_servicios(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    cliente_id: uuid.UUID | None = Query(None, description="Filtro por cliente"),
    tipo: str | None = Query(None, description="Filtro por tipo: LEGAL_SAREN, IA_AUTOMATIZACION, SOFTWARE_MEDIDA, RETAINER_MENSUAL"),
    modalidad: str | None = Query(None, description="Filtro por modalidad: PROYECTO_UNICO, RECURRENTE_MENSUAL"),
    estado_operativo: str | None = Query(None, description="Filtro por estado operativo"),
    search: str | None = Query(None, description="Búsqueda por nombre de servicio o especialista"),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return await service.get_servicios(
        db,
        skip=skip,
        limit=limit,
        cliente_id=cliente_id,
        tipo=tipo,
        modalidad=modalidad,
        estado_operativo=estado_operativo,
        search=search,
    )


@router.get("/{servicio_id}", response_model=ServicioResponse)
async def get_servicio(
    servicio_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return await service.get_servicio_by_id(db, servicio_id)


@router.post("", response_model=ServicioResponse, status_code=status.HTTP_201_CREATED)
async def create_servicio(
    servicio_in: ServicioCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return await service.create_servicio(db, servicio_in)


@router.put("/{servicio_id}", response_model=ServicioResponse)
async def update_servicio(
    servicio_id: uuid.UUID,
    servicio_in: ServicioUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return await service.update_servicio(db, servicio_id, servicio_in)


@router.patch("/{servicio_id}/status", response_model=ServicioResponse)
async def update_servicio_status(
    servicio_id: uuid.UUID,
    status_in: ServicioStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return await service.update_servicio_status(db, servicio_id, status_in)


@router.delete("/{servicio_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_servicio(
    servicio_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_admin),
):
    await service.delete_servicio(db, servicio_id)
