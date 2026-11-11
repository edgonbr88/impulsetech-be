import uuid
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, desc
from sqlalchemy.orm import selectinload

from src.modules.payments.models import Pago, EstadoPago, MonedaPago
from src.modules.payments.schemas import PagoCreate, PagoStatusUpdate, PagoResponse, PagoSummary
from src.modules.clients.models import Cliente
from src.modules.services.models import Servicio


def calcular_monto_equivalente_usd(monto: Decimal, moneda: MonedaPago, tasa_bcv: Optional[Decimal]) -> Decimal:
    if moneda in (MonedaPago.USD, MonedaPago.USDT):
        return monto.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    if moneda == MonedaPago.VES:
        if tasa_bcv and tasa_bcv > 0:
            return (monto / tasa_bcv).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return Decimal("0.00")
    return monto.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def pago_to_response(p: Pago) -> PagoResponse:
    equiv_usd = calcular_monto_equivalente_usd(p.monto, p.moneda, p.tasa_cambio_bcv)
    cliente_nombre = p.cliente.razon_social if p.cliente else None
    servicio_nombre = p.servicio.nombre_servicio if p.servicio else None
    
    return PagoResponse(
        id=p.id,
        cliente_id=p.cliente_id,
        servicio_id=p.servicio_id,
        monto=p.monto,
        moneda=p.moneda,
        tasa_cambio_bcv=p.tasa_cambio_bcv,
        medio_pago=p.medio_pago,
        referencia_bancaria=p.referencia_bancaria,
        concepto=p.concepto,
        estado_pago=p.estado_pago,
        fecha_pago=p.fecha_pago,
        comprobante_url=p.comprobante_url,
        notas=p.notas,
        created_at=p.created_at,
        updated_at=p.updated_at,
        cliente_nombre=cliente_nombre,
        servicio_nombre=servicio_nombre,
        monto_equivalente_usd=equiv_usd,
    )


class PaymentService:
    @staticmethod
    async def create_payment(session: AsyncSession, data: PagoCreate) -> PagoResponse:
        # Validar existencia de cliente
        client_res = await session.execute(select(Cliente).where(Cliente.id == data.cliente_id))
        cliente = client_res.scalar_one_or_none()
        if not cliente:
            raise ValueError(f"Cliente con id {data.cliente_id} no existe")

        # Validar existencia de servicio si se proporciona
        if data.servicio_id:
            srv_res = await session.execute(
                select(Servicio).where(and_(Servicio.id == data.servicio_id, Servicio.cliente_id == data.cliente_id))
            )
            servicio = srv_res.scalar_one_or_none()
            if not servicio:
                raise ValueError(f"Servicio con id {data.servicio_id} no existe o no pertenece al cliente")

        pago = Pago(
            cliente_id=data.cliente_id,
            servicio_id=data.servicio_id,
            monto=data.monto,
            moneda=data.moneda,
            tasa_cambio_bcv=data.tasa_cambio_bcv,
            medio_pago=data.medio_pago,
            referencia_bancaria=data.referencia_bancaria,
            concepto=data.concepto,
            estado_pago=EstadoPago.PENDIENTE,
            fecha_pago=data.fecha_pago,
            comprobante_url=data.comprobante_url,
            notas=data.notas,
        )

        session.add(pago)
        await session.commit()
        await session.refresh(pago)

        # Cargar relaciones
        q = (
            select(Pago)
            .options(selectinload(Pago.cliente), selectinload(Pago.servicio))
            .where(Pago.id == pago.id)
        )
        res = await session.execute(q)
        fresh_pago = res.scalar_one()

        return pago_to_response(fresh_pago)

    @staticmethod
    async def list_payments(
        session: AsyncSession,
        cliente_id: Optional[uuid.UUID] = None,
        servicio_id: Optional[uuid.UUID] = None,
        moneda: Optional[MonedaPago] = None,
        estado_pago: Optional[EstadoPago] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[PagoResponse]:
        conditions = []
        if cliente_id:
            conditions.append(Pago.cliente_id == cliente_id)
        if servicio_id:
            conditions.append(Pago.servicio_id == servicio_id)
        if moneda:
            conditions.append(Pago.moneda == moneda)
        if estado_pago:
            conditions.append(Pago.estado_pago == estado_pago)

        query = (
            select(Pago)
            .options(selectinload(Pago.cliente), selectinload(Pago.servicio))
            .order_by(desc(Pago.fecha_pago), desc(Pago.created_at))
            .limit(limit)
            .offset(offset)
        )
        if conditions:
            query = query.where(and_(*conditions))

        result = await session.execute(query)
        items = result.scalars().all()
        return [pago_to_response(p) for p in items]

    @staticmethod
    async def get_payment_by_id(session: AsyncSession, payment_id: uuid.UUID) -> Optional[PagoResponse]:
        query = (
            select(Pago)
            .options(selectinload(Pago.cliente), selectinload(Pago.servicio))
            .where(Pago.id == payment_id)
        )
        result = await session.execute(query)
        pago = result.scalar_one_or_none()
        if not pago:
            return None
        return pago_to_response(pago)

    @staticmethod
    async def update_payment_status(
        session: AsyncSession, payment_id: uuid.UUID, data: PagoStatusUpdate
    ) -> Optional[PagoResponse]:
        query = (
            select(Pago)
            .options(selectinload(Pago.cliente), selectinload(Pago.servicio))
            .where(Pago.id == payment_id)
        )
        result = await session.execute(query)
        pago = result.scalar_one_or_none()
        if not pago:
            return None

        pago.estado_pago = data.estado_pago
        if data.notas:
            pago.notas = (pago.notas or "") + f"\n[{pago.estado_pago.value}]: {data.notas}"

        await session.commit()
        await session.refresh(pago)
        return pago_to_response(pago)

    @staticmethod
    async def get_summary(session: AsyncSession) -> PagoSummary:
        query = select(Pago)
        result = await session.execute(query)
        pagos = result.scalars().all()

        total_verificado_usd = Decimal("0.00")
        total_pendiente_usd = Decimal("0.00")
        total_rechazado_usd = Decimal("0.00")
        c_verif = 0
        c_pend = 0
        c_rech = 0

        desglose = {
            "USD": {"total": Decimal("0.00"), "count": 0},
            "VES": {"total": Decimal("0.00"), "count": 0},
            "USDT": {"total": Decimal("0.00"), "count": 0},
        }

        for p in pagos:
            equiv = calcular_monto_equivalente_usd(p.monto, p.moneda, p.tasa_cambio_bcv)
            moneda_key = p.moneda.value
            if moneda_key in desglose:
                desglose[moneda_key]["total"] += p.monto
                desglose[moneda_key]["count"] += 1

            if p.estado_pago == EstadoPago.VERIFICADO:
                total_verificado_usd += equiv
                c_verif += 1
            elif p.estado_pago == EstadoPago.PENDIENTE:
                total_pendiente_usd += equiv
                c_pend += 1
            elif p.estado_pago == EstadoPago.RECHAZADO:
                total_rechazado_usd += equiv
                c_rech += 1

        return PagoSummary(
            total_verificado_usd=total_verificado_usd,
            total_pendiente_usd=total_pendiente_usd,
            total_rechazado_usd=total_rechazado_usd,
            conteo_verificados=c_verif,
            conteo_pendientes=c_pend,
            conteo_rechazados=c_rech,
            desglose_por_moneda={
                k: {"total": float(v["total"]), "count": v["count"]} for k, v in desglose.items()
            },
        )
