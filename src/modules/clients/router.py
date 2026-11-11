import uuid
from typing import Sequence
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.database import get_db
from src.core.dependencies import get_current_user, require_admin
from src.modules.users.models import Usuario
from src.modules.clients.schemas import (
    ClienteCreate,
    ClienteUpdate,
    ClienteResponse,
    ClienteReassign,
)
from src.modules.clients import service

router = APIRouter(prefix="/clients", tags=["Clientes"])


@router.get("", response_model=Sequence[ClienteResponse])
async def list_clientes(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    search: str | None = Query(None, description="Búsqueda por Razón Social, RIF, Contacto o Email"),
    estado: str | None = Query(None, description="Filtro por estado: ACTIVO, INACTIVO, MOROSO"),
    ejecutivo_id: uuid.UUID | None = Query(None, description="Filtro por ejecutivo asignado"),
    solo_mi_cartera: bool = Query(False, description="Filtrar solo clientes asignados al usuario logueado"),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    target_ejecutivo_id = current_user.id if solo_mi_cartera else ejecutivo_id
    return await service.get_clientes(
        db, skip=skip, limit=limit, search=search, estado=estado, ejecutivo_id=target_ejecutivo_id
    )


@router.get("/{cliente_id}", response_model=ClienteResponse)
async def get_cliente(
    cliente_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return await service.get_cliente_by_id(db, cliente_id)


@router.post("", response_model=ClienteResponse, status_code=status.HTTP_201_CREATED)
async def create_cliente(
    cliente_in: ClienteCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return await service.create_cliente(db, cliente_in)


@router.put("/{cliente_id}", response_model=ClienteResponse)
async def update_cliente(
    cliente_id: uuid.UUID,
    cliente_in: ClienteUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return await service.update_cliente(db, cliente_id, cliente_in)


@router.patch("/{cliente_id}/reassign", response_model=ClienteResponse)
async def reassign_cliente(
    cliente_id: uuid.UUID,
    reassign_in: ClienteReassign,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return await service.reassign_cliente(db, cliente_id, reassign_in)


@router.delete("/{cliente_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_cliente(
    cliente_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_admin),
):
    await service.delete_cliente(db, cliente_id)
