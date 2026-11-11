import uuid
import pytest
from httpx import ASGITransport, AsyncClient
from src.main import app


@pytest.mark.asyncio
async def test_crud_clientes_flow():
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
        random_suffix = uuid.uuid4().hex[:6].upper()
        cliente_payload = {
            "razon_social": f"Corporacion Alpha {random_suffix} C.A.",
            "rif_identificacion": f"J-{random_suffix}-0",
            "contacto_principal": "Carlos Mendoza",
            "telefono_whatsapp": "+584121234567",
            "email": f"carlos_{random_suffix.lower()}@alpha.com",
            "direccion_ciudad": "Caracas, Venezuela",
            "ejecutivo_id": admin_id,
            "estado": "ACTIVO",
            "notas": "Cliente de prueba automatizada"
        }
        create_res = await ac.post("/api/v1/clients", json=cliente_payload, headers=headers)
        assert create_res.status_code == 201
        created_client = create_res.json()
        cliente_id = created_client["id"]
        assert created_client["razon_social"] == cliente_payload["razon_social"]
        assert created_client["rif_identificacion"] == cliente_payload["rif_identificacion"]
        assert created_client["ejecutivo"]["id"] == admin_id

        # 3. Listar Clientes y verificar que aparece
        list_res = await ac.get("/api/v1/clients", headers=headers)
        assert list_res.status_code == 200
        clients = list_res.json()
        assert any(c["id"] == cliente_id for c in clients)

        # 4. Filtrar por búsqueda
        search_res = await ac.get(f"/api/v1/clients?search={random_suffix}", headers=headers)
        assert search_res.status_code == 200
        search_results = search_res.json()
        assert len(search_results) >= 1
        assert search_results[0]["id"] == cliente_id

        # 5. Obtener Cliente por ID
        get_res = await ac.get(f"/api/v1/clients/{cliente_id}", headers=headers)
        assert get_res.status_code == 200
        assert get_res.json()["id"] == cliente_id

        # 6. Actualizar Cliente (cambiar estado a MOROSO)
        update_res = await ac.put(
            f"/api/v1/clients/{cliente_id}",
            json={"estado": "MOROSO", "notas": "Actualizado a moroso en prueba"},
            headers=headers
        )
        assert update_res.status_code == 200
        assert update_res.json()["estado"] == "MOROSO"

        # 7. Validación de RIF Duplicado
        duplicate_res = await ac.post("/api/v1/clients", json=cliente_payload, headers=headers)
        assert duplicate_res.status_code == 400
        assert "ya existe un cliente" in duplicate_res.json()["detail"].lower()

        # 8. Eliminar Cliente (solo Admin)
        delete_res = await ac.delete(f"/api/v1/clients/{cliente_id}", headers=headers)
        assert delete_res.status_code == 204

        # 9. Verificar que ya no existe (404)
        get_after_delete = await ac.get(f"/api/v1/clients/{cliente_id}", headers=headers)
        assert get_after_delete.status_code == 404


@pytest.mark.asyncio
async def test_reassign_and_cartera_filter():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Login como Admin
        login_res = await ac.post(
            "/api/v1/auth/login",
            json={"email": "admin@impulsetech.com", "password": "Admin2026*!"}
        )
        token = login_res.json()["access_token"]
        admin_id = login_res.json()["user"]["id"]
        headers = {"Authorization": f"Bearer {token}"}

        # 2. Crear un segundo usuario (Ejecutivo)
        exec_email = f"ejecutivo_{uuid.uuid4().hex[:6]}@impulsetech.com"
        create_exec_res = await ac.post(
            "/api/v1/users",
            json={"nombre": "Ejecutivo Ventas", "email": exec_email, "password": "Password2026*!", "rol": "EJECUTIVO"},
            headers=headers
        )
        assert create_exec_res.status_code == 201
        exec_id = create_exec_res.json()["id"]

        # 3. Crear Cliente asignado al Admin
        random_suffix = uuid.uuid4().hex[:6].upper()
        create_res = await ac.post(
            "/api/v1/clients",
            json={
                "razon_social": f"Empresa Cartera {random_suffix}",
                "rif_identificacion": f"J-{random_suffix}-1",
                "contacto_principal": "Valeria Silva",
                "telefono_whatsapp": "+584149876543",
                "email": f"valeria_{random_suffix.lower()}@cartera.com",
                "ejecutivo_id": admin_id,
            },
            headers=headers
        )
        assert create_res.status_code == 201
        cliente_id = create_res.json()["id"]

        # 4. Probar filtro solo_mi_cartera con el Admin
        cartera_res = await ac.get("/api/v1/clients?solo_mi_cartera=true", headers=headers)
        assert cartera_res.status_code == 200
        assert any(c["id"] == cliente_id for c in cartera_res.json())

        # 5. Reasignar cliente al nuevo ejecutivo
        reassign_res = await ac.patch(
            f"/api/v1/clients/{cliente_id}/reassign",
            json={"nuevo_ejecutivo_id": exec_id, "motivo": "Transferencia de cartera para atención personalizada"},
            headers=headers
        )
        assert reassign_res.status_code == 200
        reassigned_data = reassign_res.json()
        assert reassigned_data["ejecutivo"]["id"] == exec_id
        assert "Transferencia de cartera" in reassigned_data["notas"]

        # 6. Verificar que con filtro de cartera del Admin ya no aparece
        cartera_admin_after = await ac.get("/api/v1/clients?solo_mi_cartera=true", headers=headers)
        assert not any(c["id"] == cliente_id for c in cartera_admin_after.json())

        # 7. Verificar que con filtro por ejecutivo_id del nuevo ejecutivo sí aparece
        cartera_exec = await ac.get(f"/api/v1/clients?ejecutivo_id={exec_id}", headers=headers)
        assert any(c["id"] == cliente_id for c in cartera_exec.json())

        # Cleanup
        await ac.delete(f"/api/v1/clients/{cliente_id}", headers=headers)
