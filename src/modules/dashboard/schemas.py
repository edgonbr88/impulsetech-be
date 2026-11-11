from decimal import Decimal
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, ConfigDict


class LeadsMetrics(BaseModel):
    total_leads: int
    leads_ganados: int
    leads_perdidos: int
    tasa_conversion: float
    valor_pipeline_usd: Decimal
    desglose_por_embudo: Dict[str, int]


class ClientesMetrics(BaseModel):
    total_clientes: int
    clientes_activos: int
    clientes_morosos: int
    clientes_inactivos: int


class ServiciosMetrics(BaseModel):
    total_servicios: int
    proyectos_activos: int
    retainers_activos: int
    mrr_recurrente_usd: Decimal
    servicios_por_tipo: Dict[str, int]


class FinanzasMetrics(BaseModel):
    total_verificado_usd: Decimal
    total_pendiente_usd: Decimal
    conteo_verificados: int
    conteo_pendientes: int
    desglose_por_moneda: Dict[str, Any]


class RecienteItem(BaseModel):
    id: str
    titulo: str
    subtitulo: str
    monto_o_tag: Optional[str] = None
    estado: str
    fecha: str


class DashboardMetricsResponse(BaseModel):
    leads: LeadsMetrics
    clientes: ClientesMetrics
    servicios: ServiciosMetrics
    finanzas: FinanzasMetrics
    ultimos_pagos: List[RecienteItem]
    ultimos_leads: List[RecienteItem]
    servicios_destacados: List[RecienteItem]
