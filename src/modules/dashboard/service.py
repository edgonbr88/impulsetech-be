from decimal import Decimal
from typing import Dict, List, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload

from src.modules.leads.models import Lead
from src.modules.clients.models import Cliente
from src.modules.services.models import Servicio
from src.modules.payments.models import Pago, EstadoPago, MonedaPago
from src.modules.payments.service import calcular_monto_equivalente_usd
from src.modules.dashboard.schemas import (
    DashboardMetricsResponse,
    LeadsMetrics,
    ClientesMetrics,
    ServiciosMetrics,
    FinanzasMetrics,
    RecienteItem,
)


class DashboardService:
    @staticmethod
    async def get_metrics(session: AsyncSession) -> DashboardMetricsResponse:
        # 1. Leads Metrics
        leads_res = await session.execute(select(Lead))
        all_leads = leads_res.scalars().all()

        total_leads = len(all_leads)
        leads_ganados = 0
        leads_perdidos = 0
        valor_pipeline_usd = Decimal("0.00")
        desglose_embudo: Dict[str, int] = {
            "LEGAL_SAREN": 0,
            "IA_AUTOMATIZACION": 0,
            "SOFTWARE_MEDIDA": 0,
        }

        for l in all_leads:
            if l.embudo in desglose_embudo:
                desglose_embudo[l.embudo] += 1

            if l.etapa == "GANADO":
                leads_ganados += 1
            elif l.etapa == "PERDIDO":
                leads_perdidos += 1
            else:
                if l.valor_estimado_usd:
                    valor_pipeline_usd += l.valor_estimado_usd

        tasa_conversion = (
            round((leads_ganados / total_leads) * 100, 1) if total_leads > 0 else 0.0
        )

        leads_metrics = LeadsMetrics(
            total_leads=total_leads,
            leads_ganados=leads_ganados,
            leads_perdidos=leads_perdidos,
            tasa_conversion=tasa_conversion,
            valor_pipeline_usd=valor_pipeline_usd,
            desglose_por_embudo=desglose_embudo,
        )

        # 2. Clientes Metrics
        clients_res = await session.execute(select(Cliente))
        all_clients = clients_res.scalars().all()

        total_clientes = len(all_clients)
        clientes_activos = sum(1 for c in all_clients if c.estado == "ACTIVO")
        clientes_morosos = sum(1 for c in all_clients if c.estado == "MOROSO")
        clientes_inactivos = sum(1 for c in all_clients if c.estado == "INACTIVO")

        clientes_metrics = ClientesMetrics(
            total_clientes=total_clientes,
            clientes_activos=clientes_activos,
            clientes_morosos=clientes_morosos,
            clientes_inactivos=clientes_inactivos,
        )

        # 3. Servicios Metrics
        srv_res = await session.execute(
            select(Servicio).options(selectinload(Servicio.cliente))
        )
        all_services = srv_res.scalars().all()

        total_servicios = len(all_services)
        proyectos_activos = 0
        retainers_activos = 0
        mrr_recurrente_usd = Decimal("0.00")
        desglose_tipo_srv: Dict[str, int] = {}

        for s in all_services:
            tipo_val = s.tipo
            desglose_tipo_srv[tipo_val] = desglose_tipo_srv.get(tipo_val, 0) + 1

            if s.estado_operativo not in ("FINALIZADO", "PAUSADO"):
                if s.modalidad == "PROYECTO_UNICO":
                    proyectos_activos += 1
                elif s.modalidad == "RECURRENTE_MENSUAL":
                    retainers_activos += 1
                    if s.monto_pactado_usd:
                        mrr_recurrente_usd += s.monto_pactado_usd

        servicios_metrics = ServiciosMetrics(
            total_servicios=total_servicios,
            proyectos_activos=proyectos_activos,
            retainers_activos=retainers_activos,
            mrr_recurrente_usd=mrr_recurrente_usd,
            servicios_por_tipo=desglose_tipo_srv,
        )

        # 4. Finanzas Metrics
        payments_res = await session.execute(
            select(Pago).options(selectinload(Pago.cliente), selectinload(Pago.servicio))
        )
        all_payments = payments_res.scalars().all()

        total_verif_usd = Decimal("0.00")
        total_pend_usd = Decimal("0.00")
        c_verif = 0
        c_pend = 0

        desglose_moneda = {
            "USD": {"total": Decimal("0.00"), "count": 0},
            "VES": {"total": Decimal("0.00"), "count": 0},
            "USDT": {"total": Decimal("0.00"), "count": 0},
        }

        for p in all_payments:
            eq = calcular_monto_equivalente_usd(p.monto, p.moneda, p.tasa_cambio_bcv)
            moneda_key = p.moneda.value if hasattr(p.moneda, "value") else str(p.moneda)
            if moneda_key in desglose_moneda:
                desglose_moneda[moneda_key]["total"] += p.monto
                desglose_moneda[moneda_key]["count"] += 1

            if p.estado_pago == EstadoPago.VERIFICADO:
                total_verif_usd += eq
                c_verif += 1
            elif p.estado_pago == EstadoPago.PENDIENTE:
                total_pend_usd += eq
                c_pend += 1

        finanzas_metrics = FinanzasMetrics(
            total_verificado_usd=total_verif_usd,
            total_pendiente_usd=total_pend_usd,
            conteo_verificados=c_verif,
            conteo_pendientes=c_pend,
            desglose_por_moneda={
                k: {"total": float(v["total"]), "count": v["count"]}
                for k, v in desglose_moneda.items()
            },
        )

        # 5. Listas de actividad reciente
        recent_payments_q = (
            select(Pago)
            .options(selectinload(Pago.cliente))
            .order_by(desc(Pago.fecha_pago), desc(Pago.created_at))
            .limit(5)
        )
        recent_p = (await session.execute(recent_payments_q)).scalars().all()
        ultimos_pagos = [
            RecienteItem(
                id=str(p.id),
                titulo=p.cliente.razon_social if p.cliente else "Cliente General",
                subtitulo=f"{p.medio_pago} - {p.concepto}",
                monto_o_tag=f"{p.monto} {p.moneda}",
                estado=p.estado_pago.value if hasattr(p.estado_pago, "value") else str(p.estado_pago),
                fecha=str(p.fecha_pago),
            )
            for p in recent_p
        ]

        # Últimos leads
        recent_leads_q = select(Lead).order_by(desc(Lead.created_at)).limit(5)
        recent_l = (await session.execute(recent_leads_q)).scalars().all()
        ultimos_leads = [
            RecienteItem(
                id=str(l.id),
                titulo=l.nombre_contacto,
                subtitulo=f"{l.embudo} ({l.empresa_o_proyecto})",
                monto_o_tag=f"${l.valor_estimado_usd}" if l.valor_estimado_usd else None,
                estado=l.etapa,
                fecha=str(l.created_at.date() if l.created_at else ""),
            )
            for l in recent_l
        ]

        # Servicios destacados
        srv_destacados = [
            RecienteItem(
                id=str(s.id),
                titulo=s.nombre_servicio,
                subtitulo=s.cliente.razon_social if s.cliente else "Cliente General",
                monto_o_tag=f"${s.monto_pactado_usd}",
                estado=s.estado_operativo,
                fecha=str(s.fecha_inicio),
            )
            for s in all_services[:5]
        ]

        return DashboardMetricsResponse(
            leads=leads_metrics,
            clientes=clientes_metrics,
            servicios=servicios_metrics,
            finanzas=finanzas_metrics,
            ultimos_pagos=ultimos_pagos,
            ultimos_leads=ultimos_leads,
            servicios_destacados=srv_destacados,
        )
