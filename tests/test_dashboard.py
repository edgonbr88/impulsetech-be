import pytest
from httpx import ASGITransport, AsyncClient

from src.main import app


@pytest.mark.asyncio
async def test_get_dashboard_metrics():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Login
        login_res = await ac.post(
            "/api/v1/auth/login",
            json={"email": "admin@impulsetech.com", "password": "Admin2026*!"}
        )
        assert login_res.status_code == 200
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 2. Consultar Dashboard
        res = await ac.get("/api/v1/dashboard/metrics", headers=headers)
        assert res.status_code == 200
        data = res.json()

        # Validar estructura y claves principales
        assert "leads" in data
        assert "clientes" in data
        assert "servicios" in data
        assert "finanzas" in data
        assert "ultimos_pagos" in data
        assert "ultimos_leads" in data
        assert "servicios_destacados" in data

        assert isinstance(data["leads"]["total_leads"], int)
        assert isinstance(data["clientes"]["total_clientes"], int)
        assert isinstance(data["servicios"]["total_servicios"], int)
        assert "mrr_recurrente_usd" in data["servicios"]
        assert "total_verificado_usd" in data["finanzas"]
