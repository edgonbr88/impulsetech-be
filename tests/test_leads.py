import uuid
import pytest
from httpx import ASGITransport, AsyncClient
from src.main import app


@pytest.mark.asyncio
async def test_leads_crud_and_embudos_flow():
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

        # 2. Crear un Lead en Embudo LEGAL_SAREN
        suffix = uuid.uuid4().hex[:6]
        lead_saren_payload = {
            "nombre_contacto": f"Dra. Maria {suffix}",
            "empresa_o_proyecto": f"Buffet Legal {suffix}",
            "telefono_whatsapp": "+584141112233",
            "email": f"maria_{suffix}@legal.com",
            "embudo": "LEGAL_SAREN",
            "etapa": "NUEVO",
            "valor_estimado_usd": "850.00",
            "ejecutivo_asignado_id": admin_id,
            "notas": "Trámite de constitución mercantil SAREN"
        }
        res_saren = await ac.post("/api/v1/leads", json=lead_saren_payload, headers=headers)
        assert res_saren.status_code == 201
        lead_saren = res_saren.json()
        saren_id = lead_saren["id"]
        assert lead_saren["embudo"] == "LEGAL_SAREN"
        assert lead_saren["etapa"] == "NUEVO"

        # 3. Crear un Lead en Embudo IA_AUTOMATIZACION
        lead_ia_payload = {
            "nombre_contacto": f"Ing. Pedro {suffix}",
            "empresa_o_proyecto": f"Clinica Dental {suffix}",
            "telefono_whatsapp": "+584124445566",
            "email": f"pedro_{suffix}@dental.com",
            "embudo": "IA_AUTOMATIZACION",
            "etapa": "DIAGNOSTICO",
            "valor_estimado_usd": "1200.00",
            "ejecutivo_asignado_id": admin_id,
            "notas": "Bot de agendamiento citas WhatsApp con IA"
        }
        res_ia = await ac.post("/api/v1/leads", json=lead_ia_payload, headers=headers)
        assert res_ia.status_code == 201
        ia_id = res_ia.json()["id"]

        # 4. Crear un Lead en Embudo SOFTWARE_MEDIDA
        lead_sw_payload = {
            "nombre_contacto": f"Lic. Andres {suffix}",
            "empresa_o_proyecto": f"Logistica Express {suffix}",
            "telefono_whatsapp": "+584247778899",
            "email": f"andres_{suffix}@express.com",
            "embudo": "SOFTWARE_MEDIDA",
            "etapa": "PROPUESTA",
            "valor_estimado_usd": "4500.00",
            "ejecutivo_asignado_id": admin_id,
            "notas": "Desarrollo de plataforma de rastreo de encomiendas"
        }
        res_sw = await ac.post("/api/v1/leads", json=lead_sw_payload, headers=headers)
        assert res_sw.status_code == 201
        sw_id = res_sw.json()["id"]

        # 5. Filtrar por Embudo LEGAL_SAREN
        filter_saren = await ac.get("/api/v1/leads?embudo=LEGAL_SAREN", headers=headers)
        assert filter_saren.status_code == 200
        saren_leads = filter_saren.json()
        assert any(l["id"] == saren_id for l in saren_leads)
        assert not any(l["id"] == ia_id for l in saren_leads)

        # 6. Filtrar por Embudo IA_AUTOMATIZACION
        filter_ia = await ac.get("/api/v1/leads?embudo=IA_AUTOMATIZACION", headers=headers)
        assert filter_ia.status_code == 200
        ia_leads = filter_ia.json()
        assert any(l["id"] == ia_id for l in ia_leads)
        assert not any(l["id"] == saren_id for l in ia_leads)

        # 7. Cambiar Etapa Comercial (PATCH stage) a NEGOCIACION
        stage_res = await ac.patch(
            f"/api/v1/leads/{saren_id}/stage",
            json={"etapa": "NEGOCIACION"},
            headers=headers
        )
        assert stage_res.status_code == 200
        assert stage_res.json()["etapa"] == "NEGOCIACION"

        # 8. Marcar Lead como PERDIDO con motivo
        lost_res = await ac.patch(
            f"/api/v1/leads/{saren_id}/stage",
            json={"etapa": "PERDIDO", "motivo_perdida": "Presupuesto fuera de alcance del cliente"},
            headers=headers
        )
        assert lost_res.status_code == 200
        assert lost_res.json()["etapa"] == "PERDIDO"
        assert "Presupuesto fuera" in lost_res.json()["motivo_perdida"]

        # 9. Cleanup
        await ac.delete(f"/api/v1/leads/{saren_id}", headers=headers)
        await ac.delete(f"/api/v1/leads/{ia_id}", headers=headers)
        await ac.delete(f"/api/v1/leads/{sw_id}", headers=headers)
