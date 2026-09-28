import sys
import uuid
import asyncio
import httpx

API_BASE = "http://localhost:8081"
API_V1 = f"{API_BASE}/api/v1"

async def main():
    print("=" * 60)
    print("      VERIFICACIÓN DE FLUJO COMPLETO - LUCIL BACKEND")
    print("=" * 60)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. Health Check
        print("\n1. Verificando Health Check (/health)...")
        r_health = await client.get(f"{API_BASE}/health")
        print(f"   Status: {r_health.status_code} | Body: {r_health.json()}")
        assert r_health.status_code == 200, "Health check falló"

        # 2. Documentación Swagger & OpenAPI
        print("\n2. Verificando Swagger UI y OpenAPI (/docs y /openapi.json)...")
        r_docs = await client.get(f"{API_BASE}/docs")
        r_openapi = await client.get(f"{API_BASE}/openapi.json")
        print(f"   Docs HTML Status: {r_docs.status_code} | OpenAPI Schema Status: {r_openapi.status_code}")
        assert r_docs.status_code == 200 and r_openapi.status_code == 200, "Swagger / OpenAPI falló"

        # 3. Registro de Usuario
        test_email = f"user_{uuid.uuid4().hex[:6]}@lucil.ai"
        test_pass = "LucilPass2026!"
        print(f"\n3. Registrando nuevo usuario ({test_email})...")
        r_reg = await client.post(f"{API_V1}/auth/register", json={"email": test_email, "password": test_pass})
        print(f"   Register Status: {r_reg.status_code} | Response: {r_reg.json()}")
        assert r_reg.status_code in [200, 201], f"Error en registro: {r_reg.text}"

        # 4. Login de Usuario
        print("\n4. Iniciando sesión para obtener Token JWT...")
        form_data = {"username": test_email, "password": test_pass}
        r_login = await client.post(f"{API_V1}/auth/login", data=form_data)
        print(f"   Login Status: {r_login.status_code}")
        assert r_login.status_code == 200, f"Error en login: {r_login.text}"
        
        token_data = r_login.json()
        token = token_data["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print(f"   [OK] Token recibido: {token[:25]}...")

        # 5. Crear Conversación
        print("\n5. Creando nueva conversación...")
        r_conv = await client.post(f"{API_V1}/conversations/", json={"title": "Conversación de Prueba Integrada"}, headers=headers)
        print(f"   Create Conv Status: {r_conv.status_code} | Body: {r_conv.json()}")
        assert r_conv.status_code == 200, f"Error creando conversación: {r_conv.text}"
        conv_id = r_conv.json()["id"]

        # 6. Listar Conversaciones
        print("\n6. Listando conversaciones del usuario...")
        r_list = await client.get(f"{API_V1}/conversations/", headers=headers)
        print(f"   List Conv Status: {r_list.status_code} | Total encontradas: {len(r_list.json())}")
        assert r_list.status_code == 200

        # 7. Crear Memoria del Usuario
        print("\n7. Registrando un dato de memoria personal del usuario...")
        r_mem = await client.post(f"{API_V1}/memories/", json={"category": "preferencias", "fact": "Al usuario le gusta el café sin azúcar"}, headers=headers)
        print(f"   Create Memory Status: {r_mem.status_code} | Body: {r_mem.json()}")
        assert r_mem.status_code in [200, 201]

        # 8. Enviar Mensaje (Respuesta Estándar)
        prompt_text = "Hola Lucil, ¿cuál es tu modelo y cómo me puedes ayudar?"
        print(f"\n8. Enviando mensaje al modelo: '{prompt_text}'...")
        r_msg = await client.post(
            f"{API_V1}/conversations/{conv_id}/messages",
            json={"role": "user", "content": prompt_text, "enable_web_search": False},
            headers=headers
        )
        print(f"   Message Status: {r_msg.status_code}")
        msg_body = r_msg.json()
        print(f"   [Respuesta Assistant]: {msg_body.get('content')}")
        assert r_msg.status_code == 200

        # 9. Enviar Mensaje en Streaming (SSE)
        stream_prompt = "Dime un dato curioso sobre la inteligencia artificial."
        print(f"\n9. Probando endpoint de Streaming (/conversations/{conv_id}/stream)...")
        async with client.stream(
            "POST",
            f"{API_V1}/conversations/{conv_id}/stream",
            json={"role": "user", "content": stream_prompt},
            headers=headers
        ) as stream_resp:
            print(f"   Stream Status: {stream_resp.status_code}")
            assert stream_resp.status_code == 200
            print("   [Streaming Chunks Recibidos]:")
            chunks_received = 0
            async for line in stream_resp.aiter_lines():
                if line.strip():
                    chunks_received += 1
                    if chunks_received <= 5 or "[DONE]" in line:
                        print(f"     -> {line}")
            print(f"   Total líneas recibidas en streaming: {chunks_received}")

        # 10. Obtener Detalle e Historial de la Conversación
        print("\n10. Consultando historial completo de la conversación...")
        r_detail = await client.get(f"{API_V1}/conversations/{conv_id}", headers=headers)
        print(f"    Get Conv Status: {r_detail.status_code}")
        assert r_detail.status_code == 200
        detail_data = r_detail.json()
        messages = detail_data.get("messages", [])
        print(f"    Total mensajes guardados en SQLite: {len(messages)}")
        for idx, m in enumerate(messages, 1):
            role = m["role"].upper()
            content_preview = m["content"][:70].replace("\n", " ")
            print(f"      [{idx}] {role}: {content_preview}...")

    print("\n" + "=" * 60)
    print("      ¡TODAS LAS PRUEBAS DEL FLUJO COMPLETADAS CON ÉXITO!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
