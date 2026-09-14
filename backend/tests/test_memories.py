import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.db.database import AsyncSessionLocal
from app.db.init_db import init_tables
from app.models.user import User
from app.models.memory import MemoryItem
from app.ai_engine.memory import TieredMemory

@pytest.mark.asyncio
async def test_memories_crud_and_context():
    await init_tables()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Registro de usuario de prueba
        email = "test_memory_user@lucil.ai"
        password = "Password123!"
        reg_resp = await client.post("/api/v1/auth/register", json={"email": email, "password": password})
        if reg_resp.status_code == 400: # Ya existía
            pass
            
        # 2. Login para obtener token
        login_resp = await client.post(
            "/api/v1/auth/login",
            data={"username": email, "password": password},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        assert login_resp.status_code == 200
        token = login_resp.json()["access_token"]
        auth_headers = {"Authorization": f"Bearer {token}"}

        # 3. Crear Recuerdo (POST /api/v1/memories/)
        create_resp = await client.post(
            "/api/v1/memories/",
            json={"category": "salud", "fact": "Soy alérgico a la penicilina y a la aspirina."},
            headers=auth_headers
        )
        assert create_resp.status_code == 201
        mem_data = create_resp.json()
        memory_id = mem_data["id"]
        assert mem_data["fact"] == "Soy alérgico a la penicilina y a la aspirina."
        assert mem_data["category"] == "salud"

        # 4. Listar Recuerdos (GET /api/v1/memories/)
        list_resp = await client.get("/api/v1/memories/", headers=auth_headers)
        assert list_resp.status_code == 200
        items = list_resp.json()
        assert any(m["id"] == memory_id for m in items)

        # 5. Modificar Recuerdo (PUT /api/v1/memories/{id})
        update_resp = await client.put(
            f"/api/v1/memories/{memory_id}",
            json={"fact": "Soy alérgico únicamente a la penicilina."},
            headers=auth_headers
        )
        assert update_resp.status_code == 200
        assert update_resp.json()["fact"] == "Soy alérgico únicamente a la penicilina."

        # 6. Validar que TieredMemory inyecta el recuerdo real en el perfil semántico
        async with AsyncSessionLocal() as db:
            tiered_memory = TieredMemory()
            user_id = mem_data["user_id"]
            profile = await tiered_memory.get_semantic_profile(db, user_id)
            assert "salud" in profile
            assert any("penicilina" in f for f in profile["salud"])

        # 7. Eliminar Recuerdo (DELETE /api/v1/memories/{id})
        del_resp = await client.delete(f"/api/v1/memories/{memory_id}", headers=auth_headers)
        assert del_resp.status_code == 204

        # 8. Verificar que ya no existe
        get_resp = await client.get(f"/api/v1/memories/{memory_id}", headers=auth_headers)
        assert get_resp.status_code == 404
