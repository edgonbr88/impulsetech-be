import uuid
from typing import Sequence
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from src.modules.clients.models import Cliente
from src.modules.clients.schemas import ClienteCreate, ClienteUpdate
from src.modules.users.models import Usuario


async def get_clientes(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    search: str | None = None,
    estado: str | None = None,
    ejecutivo_id: uuid.UUID | None = None,
) -> Sequence[Cliente]:
    query = select(Cliente)

    if search:
        search_filter = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Cliente.razon_social.ilike(search_filter),
                Cliente.rif_identificacion.ilike(search_filter),
                Cliente.contacto_principal.ilike(search_filter),
                Cliente.email.ilike(search_filter),
            )
        )

    if estado:
        query = query.filter(Cliente.estado == estado)

    if ejecutivo_id:
        query = query.filter(Cliente.ejecutivo_id == ejecutivo_id)

    query = query.order_by(Cliente.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


async def get_cliente_by_id(db: AsyncSession, cliente_id: uuid.UUID) -> Cliente:
    query = select(Cliente).filter(Cliente.id == cliente_id)
    result = await db.execute(query)
    cliente = result.scalar_one_or_none()
    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente no encontrado"
        )
    return cliente


async def create_cliente(db: AsyncSession, cliente_in: ClienteCreate) -> Cliente:
    # 1. Verificar si el RIF ya existe
    existing_rif = await db.execute(
        select(Cliente).filter(Cliente.rif_identificacion == cliente_in.rif_identificacion.strip())
    )
    if existing_rif.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe un cliente registrado con este RIF o identificación"
        )

    # 2. Verificar que el ejecutivo exista
    ejecutivo = await db.execute(
        select(Usuario).filter(Usuario.id == cliente_in.ejecutivo_id)
    )
    if not ejecutivo.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El ejecutivo responsable asignado no existe"
        )

    nuevo_cliente = Cliente(
        razon_social=cliente_in.razon_social.strip(),
        rif_identificacion=cliente_in.rif_identificacion.strip().upper(),
        contacto_principal=cliente_in.contacto_principal.strip(),
        telefono_whatsapp=cliente_in.telefono_whatsapp.strip(),
        email=cliente_in.email.strip().lower(),
        direccion_ciudad=cliente_in.direccion_ciudad.strip() if cliente_in.direccion_ciudad else None,
        ejecutivo_id=cliente_in.ejecutivo_id,
        estado=cliente_in.estado,
        notas=cliente_in.notas.strip() if cliente_in.notas else None,
    )
    db.add(nuevo_cliente)
    await db.commit()
    await db.refresh(nuevo_cliente)
    return await get_cliente_by_id(db, nuevo_cliente.id)


async def update_cliente(
    db: AsyncSession, cliente_id: uuid.UUID, cliente_in: ClienteUpdate
) -> Cliente:
    cliente = await get_cliente_by_id(db, cliente_id)

    # Si se intenta cambiar el RIF, validar unicidad
    if cliente_in.rif_identificacion and cliente_in.rif_identificacion.strip().upper() != cliente.rif_identificacion:
        existing_rif = await db.execute(
            select(Cliente).filter(
                Cliente.rif_identificacion == cliente_in.rif_identificacion.strip().upper(),
                Cliente.id != cliente_id
            )
        )
        if existing_rif.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe otro cliente con este RIF o identificación"
            )
        cliente.rif_identificacion = cliente_in.rif_identificacion.strip().upper()

    # Si se cambia el ejecutivo, validar existencia
    if cliente_in.ejecutivo_id and cliente_in.ejecutivo_id != cliente.ejecutivo_id:
        ejecutivo = await db.execute(
            select(Usuario).filter(Usuario.id == cliente_in.ejecutivo_id)
        )
        if not ejecutivo.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El nuevo ejecutivo asignado no existe"
            )
        cliente.ejecutivo_id = cliente_in.ejecutivo_id

    if cliente_in.razon_social is not None:
        cliente.razon_social = cliente_in.razon_social.strip()
    if cliente_in.contacto_principal is not None:
        cliente.contacto_principal = cliente_in.contacto_principal.strip()
    if cliente_in.telefono_whatsapp is not None:
        cliente.telefono_whatsapp = cliente_in.telefono_whatsapp.strip()
    if cliente_in.email is not None:
        cliente.email = cliente_in.email.strip().lower()
    if cliente_in.direccion_ciudad is not None:
        cliente.direccion_ciudad = cliente_in.direccion_ciudad.strip() if cliente_in.direccion_ciudad else None
    if cliente_in.estado is not None:
        cliente.estado = cliente_in.estado
    if cliente_in.notas is not None:
        cliente.notas = cliente_in.notas.strip() if cliente_in.notas else None

    await db.commit()
    await db.refresh(cliente)
    return await get_cliente_by_id(db, cliente.id)


async def delete_cliente(db: AsyncSession, cliente_id: uuid.UUID) -> None:
    cliente = await get_cliente_by_id(db, cliente_id)
    await db.delete(cliente)
    await db.commit()
