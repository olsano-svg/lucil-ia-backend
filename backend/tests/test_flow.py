import sys
import asyncio
import httpx

API_BASE = "http://localhost:8081/api/v1"

async def test_full_flow():
    print("=== TEST DE FLUJO COMPLETO LUCIL AI ===")
    async with httpx.AsyncClient(timeout=180.0) as client:
        # 1. Login
        print("\n1. Probando inicio de sesión...")
        form_data = {"username": "admin", "password": "delarosa00"}
        r = await client.post(f"{API_BASE}/auth/login", data=form_data)
        if r.status_code != 200:
            print(f"FAILED LOGIN: {r.status_code}, {r.text}")
            # Intentar registro si no existe
            r_reg = await client.post(f"{API_BASE}/auth/register", json={"email": "admin@lucil.ai", "password": "delarosa00"})
            print(f"Registro fallback: {r_reg.status_code}")
            r = await client.post(f"{API_BASE}/auth/login", data=form_data)
        
        token_data = r.json()
        token = token_data.get("access_token")
        print(f"[OK] Login exitoso. Token recibido ({token[:15]}...)")
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # 2. Crear conversación
        print("\n2. Creando nueva conversación...")
        r_conv = await client.post(f"{API_BASE}/conversations/", json={"title": "Test de Pregunta-Respuesta IA"}, headers=headers)
        assert r_conv.status_code == 200, f"Error creando conv: {r_conv.text}"
        conv_data = r_conv.json()
        conv_id = conv_data["id"]
        print(f"[OK] Conversación creada ID: {conv_id}")
        
        # 3. Enviar pregunta
        question = "¿Cuál es el planeta más grande del sistema solar y una característica suya?"
        print(f"\n3. Enviando pregunta a Lucil AI: '{question}'...")
        r_msg = await client.post(
            f"{API_BASE}/conversations/{conv_id}/messages",
            json={"role": "user", "content": question},
            headers=headers
        )
        assert r_msg.status_code == 200, f"Error en mensaje: {r_msg.text}"
        msg_data = r_msg.json()
        print(f"[OK] Respuesta recibida de Lucil AI:\n{msg_data.get('content')}")
        
        # 4. Obtener conversación para verificar persistencia en DB
        print("\n4. Verificando persistencia en base de datos...")
        r_get = await client.get(f"{API_BASE}/conversations/{conv_id}", headers=headers)
        assert r_get.status_code == 200
        messages = r_get.json().get("messages", [])
        print(f"[OK] Total mensajes persistidos en DB: {len(messages)}")
        for m in messages:
            print(f"  [{m['role'].upper()}]: {m['content'][:80]}...")

if __name__ == "__main__":
    asyncio.run(test_full_flow())
