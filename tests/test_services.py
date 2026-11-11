import uuid
from datetime import date
import pytest
from httpx import ASGITransport, AsyncClient
from src.main import app


@pytest.mark.asyncio
async def test_crud_services_and_modalities():
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

        # 2. Crear un Cliente para asignarle servicios
        suffix = uuid.uuid4().hex[:6]
        client_res = await ac.post(
            "/api/v1/clients",
            json={
                "razon_social": f"Corporacion Servitest {suffix} C.A.",
                "rif_identificacion": f"J-{suffix.upper()}-8",
                "contacto_principal": "Roberto Gómez",
                "telefono_whatsapp": "+584123332211",
                "email": f"roberto_{suffix}@servitest.com",
                "ejecutivo_id": admin_id,
            },
            headers=headers
        )
        assert client_res.status_code == 201
        cliente_id = client_res.json()["id"]

        # 3. Crear Servicio 1: Modalidad PROYECTO_UNICO (Software a Medida)
        srv1_payload = {
            "cliente_id": cliente_id,
            "tipo": "SOFTWARE_MEDIDA",
            "nombre_servicio": "Desarrollo de Portal de Proveedores B2B",
            "modalidad": "PROYECTO_UNICO",
            "estado_operativo": "EN_ESPERA",
            "especialista_responsable": "Ing. Miguel Tech Lead",
            "monto_pactado_usd": "5000.00",
            "fecha_inicio": str(date.today()),
            "fecha_entrega_estimada": "2026-12-15",
            "notas": "Anticipo del 50% requerido antes del kickoff."
        }
        srv1_res = await ac.post("/api/v1/services", json=srv1_payload, headers=headers)
        assert srv1_res.status_code == 201
        srv1 = srv1_res.json()
        srv1_id = srv1["id"]
        assert srv1["modalidad"] == "PROYECTO_UNICO"
        assert srv1["estado_operativo"] == "EN_ESPERA"

        # 4. Crear Servicio 2: Modalidad RECURRENTE_MENSUAL (Retainer de Soporte e IA)
        srv2_payload = {
            "cliente_id": cliente_id,
            "tipo": "RETAINER_MENSUAL",
            "nombre_servicio": "Retainer Mantenimiento Agentes IA y Servidores",
            "modalidad": "RECURRENTE_MENSUAL",
            "estado_operativo": "ACTIVO_PRODUCCION",
            "especialista_responsable": "DevOps & Prompt Engineer Team",
            "monto_pactado_usd": "450.00",
            "fecha_inicio": str(date.today()),
            "dia_corte_mensual": 5,
            "notas": "Facturación automática el día 5 de cada mes."
        }
        srv2_res = await ac.post("/api/v1/services", json=srv2_payload, headers=headers)
        assert srv2_res.status_code == 201
        srv2 = srv2_res.json()
        srv2_id = srv2["id"]
        assert srv2["modalidad"] == "RECURRENTE_MENSUAL"
        assert srv2["dia_corte_mensual"] == 5

        # 5. Listar Servicios del Cliente y validar paralelismo (2 servicios activos)
        list_client_srvs = await ac.get(f"/api/v1/services?cliente_id={cliente_id}", headers=headers)
        assert list_client_srvs.status_code == 200
        client_srvs = list_client_srvs.json()
        assert len(client_srvs) == 2

        # 6. Actualizar Estado Operativo (PATCH status)
        status_res = await ac.patch(
            f"/api/v1/services/{srv1_id}/status",
            json={
                "estado_operativo": "EN_DESARROLLO",
                "notas_actualizacion": "Anticipo recibido vía Zelle. Sprint 1 iniciado."
            },
            headers=headers
        )
        assert status_res.status_code == 200
        assert status_res.json()["estado_operativo"] == "EN_DESARROLLO"
        assert "Sprint 1 iniciado" in status_res.json()["notas"]

        # 7. Validar regla de dia_corte_mensual obligatorio para RECURRENTE_MENSUAL
        invalid_retainer = {
            "cliente_id": cliente_id,
            "tipo": "RETAINER_MENSUAL",
            "nombre_servicio": "Iguala Legal Mensual",
            "modalidad": "RECURRENTE_MENSUAL",
            "especialista_responsable": "Dra. Abogado",
            "monto_pactado_usd": "300.00",
            "fecha_inicio": str(date.today()),
            "dia_corte_mensual": None
        }
        invalid_res = await ac.post("/api/v1/services", json=invalid_retainer, headers=headers)
        assert invalid_res.status_code == 400
        assert "día de corte" in invalid_res.json()["detail"].lower()

        # Cleanup
        await ac.delete(f"/api/v1/services/{srv1_id}", headers=headers)
        await ac.delete(f"/api/v1/services/{srv2_id}", headers=headers)
        await ac.delete(f"/api/v1/clients/{cliente_id}", headers=headers)
