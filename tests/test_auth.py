import pytest
from httpx import ASGITransport, AsyncClient
from src.main import app


@pytest.mark.asyncio
async def test_login_success_admin():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/auth/login",
            json={"email": "admin@impulsetech.com", "password": "Admin2026*!"}
        )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "admin@impulsetech.com"
    assert data["user"]["rol"] == "ADMIN"
    assert data["user"]["activo"] is True


@pytest.mark.asyncio
async def test_login_invalid_password():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/auth/login",
            json={"email": "admin@impulsetech.com", "password": "WrongPassword123*"}
        )
    assert response.status_code == 401
    assert "incorrectos" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_login_nonexistent_email():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/auth/login",
            json={"email": "fantasma@impulsetech.com", "password": "SomePassword123"}
        )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me_authenticated():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Login
        login_res = await ac.post(
            "/api/v1/auth/login",
            json={"email": "admin@impulsetech.com", "password": "Admin2026*!"}
        )
        token = login_res.json()["access_token"]

        # 2. Get me
        me_res = await ac.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
    assert me_res.status_code == 200
    user_data = me_res.json()
    assert user_data["email"] == "admin@impulsetech.com"
    assert user_data["rol"] == "ADMIN"


@pytest.mark.asyncio
async def test_get_me_unauthorized():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me_invalid_token():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer token_falso_invalido_123"}
        )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_active_ejecutivos():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Login
        login_res = await ac.post(
            "/api/v1/auth/login",
            json={"email": "admin@impulsetech.com", "password": "Admin2026*!"}
        )
        token = login_res.json()["access_token"]

        # List ejecutivos
        res = await ac.get(
            "/api/v1/users/ejecutivos",
            headers={"Authorization": f"Bearer {token}"}
        )
    assert res.status_code == 200
    users = res.json()
    assert isinstance(users, list)
    assert len(users) >= 1


@pytest.mark.asyncio
async def test_admin_create_and_login_new_user():
    test_email = "ejecutivo.carlos@impulsetech.com"
    test_pass = "Carlos2026*!"

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Login Admin
        login_admin = await ac.post(
            "/api/v1/auth/login",
            json={"email": "admin@impulsetech.com", "password": "Admin2026*!"}
        )
        token = login_admin.json()["access_token"]

        # 2. Create user (or handle if already exists)
        create_res = await ac.post(
            "/api/v1/users",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "nombre": "Carlos Ejecutivo",
                "email": test_email,
                "password": test_pass,
                "rol": "EJECUTIVO",
                "activo": True
            }
        )
        assert create_res.status_code in [201, 409]

        # 3. Login as new user
        login_user = await ac.post(
            "/api/v1/auth/login",
            json={"email": test_email, "password": test_pass}
        )
        assert login_user.status_code == 200
        user_data = login_user.json()
        assert user_data["user"]["email"] == test_email
        assert user_data["user"]["rol"] == "EJECUTIVO"
