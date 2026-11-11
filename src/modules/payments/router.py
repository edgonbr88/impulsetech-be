import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.dependencies import get_current_user
from src.modules.users.models import Usuario
from src.modules.payments.models import MonedaPago, EstadoPago
from src.modules.payments.schemas import PagoCreate, PagoStatusUpdate, PagoResponse, PagoSummary
from src.modules.payments.service import PaymentService

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("", response_model=PagoResponse, status_code=status.HTTP_201_CREATED)
async def create_payment(
    pago_in: PagoCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    try:
        return await PaymentService.create_payment(db, pago_in)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("", response_model=List[PagoResponse])
async def list_payments(
    cliente_id: Optional[uuid.UUID] = Query(None),
    servicio_id: Optional[uuid.UUID] = Query(None),
    moneda: Optional[MonedaPago] = Query(None),
    estado_pago: Optional[EstadoPago] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return await PaymentService.list_payments(
        session=db,
        cliente_id=cliente_id,
        servicio_id=servicio_id,
        moneda=moneda,
        estado_pago=estado_pago,
        limit=limit,
        offset=offset,
    )


@router.get("/summary/balance", response_model=PagoSummary)
async def get_payments_summary(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return await PaymentService.get_summary(db)


@router.get("/{payment_id}", response_model=PagoResponse)
async def get_payment_detail(
    payment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    pago = await PaymentService.get_payment_by_id(db, payment_id)
    if not pago:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pago no encontrado")
    return pago


@router.patch("/{payment_id}/status", response_model=PagoResponse)
async def update_payment_status(
    payment_id: uuid.UUID,
    status_in: PagoStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    pago = await PaymentService.update_payment_status(db, payment_id, status_in)
    if not pago:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pago no encontrado")
    return pago
