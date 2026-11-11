import uuid
from typing import Sequence
from datetime import datetime, timezone
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from src.modules.services.models import Servicio
from src.modules.services.schemas import ServicioCreate, ServicioUpdate, ServicioStatusUpdate
from src.modules.clients.models import Cliente


async def get_servicios(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    cliente_id: uuid.UUID | None = None,
    tipo: str | None = None,
    modalidad: str | None = None,
    estado_operativo: str | None = None,
    search: str | None = None,
) -> Sequence[Servicio]:
    query = select(Servicio)

    if cliente_id:
        query = query.filter(Servicio.cliente_id == cliente_id)

    if tipo:
        query = query.filter(Servicio.tipo == tipo)

    if modalidad:
        query = query.filter(Servicio.modalidad == modalidad)

    if estado_operativo:
        query = query.filter(Servicio.estado_operativo == estado_operativo)

    if search:
        search_filter = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Servicio.nombre_servicio.ilike(search_filter),
                Servicio.especialista_responsable.ilike(search_filter),
            )
        )

    query = query.order_by(Servicio.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


async def get_servicio_by_id(db: AsyncSession, servicio_id: uuid.UUID) -> Servicio:
    query = select(Servicio).filter(Servicio.id == servicio_id)
    result = await db.execute(query)
    servicio = result.scalar_one_or_none()
    if not servicio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Servicio no encontrado",
        )
    return servicio


async def create_servicio(db: AsyncSession, servicio_in: ServicioCreate) -> Servicio:
    # 1. Validar que el cliente existe
    cliente = await db.execute(
        select(Cliente).filter(Cliente.id == servicio_in.cliente_id)
    )
    if not cliente.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El cliente especificado no existe",
        )

    # 2. Validar regla de modalidad recurrente
    if servicio_in.modalidad == "RECURRENTE_MENSUAL" and not servicio_in.dia_corte_mensual:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Los servicios de modalidad recurrente deben especificar el día de corte mensual (1-31).",
        )

    nuevo_servicio = Servicio(
        cliente_id=servicio_in.cliente_id,
        tipo=servicio_in.tipo,
        nombre_servicio=servicio_in.nombre_servicio.strip(),
        modalidad=servicio_in.modalidad,
        estado_operativo=servicio_in.estado_operativo,
        especialista_responsable=servicio_in.especialista_responsable.strip(),
        monto_pactado_usd=servicio_in.monto_pactado_usd,
        fecha_inicio=servicio_in.fecha_inicio,
        fecha_entrega_estimada=servicio_in.fecha_entrega_estimada,
        dia_corte_mensual=servicio_in.dia_corte_mensual,
        notas=servicio_in.notas.strip() if servicio_in.notas else None,
    )
    db.add(nuevo_servicio)
    await db.commit()
    await db.refresh(nuevo_servicio)
    return await get_servicio_by_id(db, nuevo_servicio.id)


async def update_servicio(
    db: AsyncSession, servicio_id: uuid.UUID, servicio_in: ServicioUpdate
) -> Servicio:
    servicio = await get_servicio_by_id(db, servicio_id)

    if servicio_in.cliente_id and servicio_in.cliente_id != servicio.cliente_id:
        cliente = await db.execute(
            select(Cliente).filter(Cliente.id == servicio_in.cliente_id)
        )
        if not cliente.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El cliente especificado no existe",
            )
        servicio.cliente_id = servicio_in.cliente_id

    if servicio_in.tipo is not None:
        servicio.tipo = servicio_in.tipo
    if servicio_in.nombre_servicio is not None:
        servicio.nombre_servicio = servicio_in.nombre_servicio.strip()
    if servicio_in.modalidad is not None:
        servicio.modalidad = servicio_in.modalidad
    if servicio_in.estado_operativo is not None:
        servicio.estado_operativo = servicio_in.estado_operativo
    if servicio_in.especialista_responsable is not None:
        servicio.especialista_responsable = servicio_in.especialista_responsable.strip()
    if servicio_in.monto_pactado_usd is not None:
        servicio.monto_pactado_usd = servicio_in.monto_pactado_usd
    if servicio_in.fecha_inicio is not None:
        servicio.fecha_inicio = servicio_in.fecha_inicio
    if servicio_in.fecha_entrega_estimada is not None:
        servicio.fecha_entrega_estimada = servicio_in.fecha_entrega_estimada
    if servicio_in.dia_corte_mensual is not None:
        servicio.dia_corte_mensual = servicio_in.dia_corte_mensual
    if servicio_in.notas is not None:
        servicio.notas = servicio_in.notas.strip() if servicio_in.notas else None

    await db.commit()
    await db.refresh(servicio)
    return await get_servicio_by_id(db, servicio.id)


async def update_servicio_status(
    db: AsyncSession, servicio_id: uuid.UUID, status_in: ServicioStatusUpdate
) -> Servicio:
    servicio = await get_servicio_by_id(db, servicio_id)
    servicio.estado_operativo = status_in.estado_operativo

    if status_in.notas_actualizacion:
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        nota = f"[{ts}] Estado cambiado a {status_in.estado_operativo}: {status_in.notas_actualizacion.strip()}"
        servicio.notas = f"{servicio.notas}\n{nota}" if servicio.notas else nota

    await db.commit()
    await db.refresh(servicio)
    return await get_servicio_by_id(db, servicio.id)


async def delete_servicio(db: AsyncSession, servicio_id: uuid.UUID) -> None:
    servicio = await get_servicio_by_id(db, servicio_id)
    await db.delete(servicio)
    await db.commit()
