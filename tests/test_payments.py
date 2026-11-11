import pytest
import uuid
from datetime import date
from decimal import Decimal
from httpx import ASGITransport, AsyncClient

from src.main import app


@pytest.mark.asyncio
async def test_crud_payments_flow():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Login como Admin
        login_res = await ac.post(
            "/api/v1/auth/login",
            json={"email": "admin@impulsetech.com", "password": "Admin2026*!"}
        )
        assert login_res.status_code == 200
        token = login_res.json()["access_token"]
        admin_id = login_res.json()["user"]["id"]
        headers = {"Authorization": f"Bearer {token}"}

        # 2. Crear Cliente
        suffix = uuid.uuid4().hex[:6]
        client_res = await ac.post(
            "/api/v1/clients",
            json={
                "razon_social": f"Cliente Finanzas {suffix} C.A.",
                "rif_identificacion": f"J-{suffix.upper()}-9",
                "contacto_principal": "Gerente Pagos",
                "telefono_whatsapp": "+584120009988",
                "email": f"finanzas_{suffix}@test.com",
                "ejecutivo_id": admin_id,
            },
            headers=headers
        )
        assert client_res.status_code == 201
        cliente_id = client_res.json()["id"]

        # 3. Crear Servicio
        srv_res = await ac.post(
            "/api/v1/services",
            json={
                "cliente_id": cliente_id,
                "tipo": "SOFTWARE_MEDIDA",
                "nombre_servicio": "ERP B2B Fase 1",
                "modalidad": "PROYECTO_UNICO",
                "estado_operativo": "EN_ESPERA",
                "especialista_responsable": "Dev Lead",
                "monto_pactado_usd": "3500.00",
                "fecha_inicio": str(date.today()),
            },
            headers=headers
        )
        assert srv_res.status_code == 201
        servicio_id = srv_res.json()["id"]

        # 4. Crear Pago en USD con Zelle
        payment_payload = {
            "cliente_id": cliente_id,
            "servicio_id": servicio_id,
            "monto": "1750.00",
            "moneda": "USD",
            "medio_pago": "ZELLE",
            "referencia_bancaria": "ZEL-998877",
            "concepto": "ANTICIPO_50",
            "fecha_pago": str(date.today()),
            "notas": "Anticipo 50% vía Zelle recibido"
        }
        res_p = await ac.post("/api/v1/payments", json=payment_payload, headers=headers)
        assert res_p.status_code == 201
        p_data = res_p.json()
        assert p_data["moneda"] == "USD"
        assert p_data["estado_pago"] == "PENDIENTE"
        assert Decimal(str(p_data["monto_equivalente_usd"])) == Decimal("1750.00")
        payment_id = p_data["id"]

        # 5. Listar pagos
        res_list = await ac.get(f"/api/v1/payments?cliente_id={cliente_id}", headers=headers)
        assert res_list.status_code == 200
        items = res_list.json()
        assert len(items) >= 1
        assert items[0]["id"] == payment_id

        # 6. Pago en VES sin tasa BCV (debe fallar 422)
        bad_ves = {
            "cliente_id": cliente_id,
            "monto": "25000.00",
            "moneda": "VES",
            "medio_pago": "PAGO_MOVIL",
            "referencia_bancaria": "PM-123456"
        }
        res_bad = await ac.post("/api/v1/payments", json=bad_ves, headers=headers)
        assert res_bad.status_code == 422

        # 7. Pago en VES con tasa BCV (50.0000 => 25000 / 50 = 500.00 USD)
        good_ves = {
            "cliente_id": cliente_id,
            "monto": "25000.00",
            "moneda": "VES",
            "tasa_cambio_bcv": "50.0000",
            "medio_pago": "PAGO_MOVIL",
            "referencia_bancaria": "PM-123456",
            "concepto": "CUOTA_RETAINER",
            "fecha_pago": str(date.today())
        }
        res_good = await ac.post("/api/v1/payments", json=good_ves, headers=headers)
        assert res_good.status_code == 201
        assert Decimal(str(res_good.json()["monto_equivalente_usd"])) == Decimal("500.00")

        # 8. Pago en USDT y verificación
        usdt_p = {
            "cliente_id": cliente_id,
            "monto": "1200.00",
            "moneda": "USDT",
            "medio_pago": "USDT_BINANCE",
            "referencia_bancaria": "TXID-0x9948271",
            "concepto": "FINIQUITO",
            "fecha_pago": str(date.today())
        }
        res_usdt = await ac.post("/api/v1/payments", json=usdt_p, headers=headers)
        assert res_usdt.status_code == 201
        usdt_id = res_usdt.json()["id"]

        # Cambiar estado a VERIFICADO
        res_verif = await ac.patch(
            f"/api/v1/payments/{usdt_id}/status",
            json={"estado_pago": "VERIFICADO", "notas": "Verificado en Binance Pay con hash confirmado"},
            headers=headers
        )
        assert res_verif.status_code == 200
        assert res_verif.json()["estado_pago"] == "VERIFICADO"

        # 9. Consultar resumen financiero
        res_sum = await ac.get("/api/v1/payments/summary/balance", headers=headers)
        assert res_sum.status_code == 200
        summary = res_sum.json()
        assert summary["conteo_verificados"] >= 1
        assert float(summary["total_verificado_usd"]) >= 1200.00
