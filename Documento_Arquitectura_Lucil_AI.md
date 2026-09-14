# Documento de Arquitectura: Lucil AI

## 1. Visión y Objetivos
**Visión:** Crear "Lucil AI", una inteligencia artificial de nueva generación que actúe como un asistente personal avanzado. La interacción debe sentirse tan natural, coherente y útil como hablar con una persona altamente capacitada, sin intentar simular ser humana. Diseñada inicialmente para uso personal con una arquitectura robusta lista para escalar a una plataforma comercial SaaS (Software as a Service).

**Objetivos Principales:**
- **Mobile First:** Prioridad absoluta en aplicaciones nativas para Android e iOS.
- **Interacción Multimodal:** Chat por texto y voz en tiempo real, análisis de imágenes y lectura de documentos.
- **Memoria y Contexto:** Memoria configurable a corto y largo plazo, base de conocimiento privada y búsqueda inteligente.
- **Personalidad Objetiva y Segura:** Respuestas basadas en evidencia, neutralidad en temas controvertidos, rigor médico y nula alucinación.
- **Escalabilidad y Modularidad:** Arquitectura preparada para crecer durante años sin necesidad de refactorizaciones masivas.

## 2. Principios de Comportamiento de Lucil AI
- **Transparencia y Evidencia:** No inventar información (sin alucinaciones). Diferenciar claramente entre hechos demostrados, hipótesis, interpretaciones y preguntas abiertas.
- **Manejo de Controversias:** No negarse a hablar de temas debatidos; presentar múltiples perspectivas de manera objetiva.
- **Rigor Médico/Científico:** Explicar siempre el nivel de evidencia. Describir beneficios, riesgos y alternativas sin dar consejo médico definitivo.
- **Proactividad:** Solicitar información adicional o clarificaciones al usuario para proporcionar respuestas más precisas y útiles.

## 3. Casos de Uso Principales
- **Chat Conversacional:** Interacción fluida de texto y voz (tiempo real).
- **Gestión del Conocimiento:** Subida y análisis de archivos locales (PDF, Word, Excel).
- **Búsqueda Inteligente:** Recuperación de información (RAG - Retrieval-Augmented Generation) sobre el historial y documentos del usuario.
- **Organización:** Agrupación de conversaciones y documentos en "Proyectos".
- **Sistema de Plugins:** Capacidad para conectarse a herramientas externas.
- **Sincronización:** Datos en tiempo real entre múltiples dispositivos.

## 4. Diseño de la Arquitectura del Sistema (Alto Nivel)
La arquitectura seguirá un modelo de monolito modular inicialmente, preparado para separarse en microservicios, basado en APIs REST y WebSockets para comunicación bidireccional en tiempo real.

- **Capa de Presentación (Frontend):** Aplicación móvil (Android/iOS) que maneja la UI/UX, captura de audio/imágenes y gestión del estado local.
- **Capa de Puerta de Enlace (API Gateway / Proxy):** Enruta el tráfico, maneja rate-limiting y seguridad perimetral.
- **Capa de Aplicación (Backend Core):** Lógica de negocio, gestión de usuarios, proyectos, sistema de plugins y control de acceso.
- **Capa de Inteligencia Artificial (AI Engine):** Orquestación de LLMs, gestión de prompts, memoria semántica, procesamiento de voz (STT/TTS) y visión.
- **Capa de Datos:** Almacenamiento relacional (usuarios, chats), vectorial (embeddings) y de objetos (archivos crudos).

## 5. Stack Tecnológico Recomendado (con justificaciones)

### Frontend (Mobile First)
- **Tecnología:** **React Native (con Expo)**
- **Justificación:** Permite tener un solo código base (TypeScript) para Android e iOS con rendimiento casi nativo. Expo acelera el desarrollo (compilación en la nube, OTA updates). Al usar React, nuestro equipo full-stack y el diseñador UX/UI pueden iterar rápido, y se reaprovechan componentes cuando hagamos la versión Web.

### Backend (Core & AI Integration)
- **Tecnología:** **Python con FastAPI**
- **Justificación:** Python es el rey indiscutible del ecosistema de IA. FastAPI es un framework moderno, excepcionalmente rápido y con soporte asíncrono nativo (vital para manejar WebSockets y streaming de respuestas de voz y LLMs).

### Base de Datos y Almacenamiento
- **Base de Datos Principal (Relacional y Vectorial):** **PostgreSQL con extensión `pgvector`**
  - *Justificación:* PostgreSQL es extremadamente robusto para datos estructurados (usuarios, proyectos). Usar `pgvector` nos permite tener la base de datos vectorial (memoria semántica, búsqueda de conocimiento) en la misma infraestructura, reduciendo costos y complejidad inicial. Si escalamos masivamente, podemos migrar la capa vectorial a Pinecone o Weaviate.
- **Almacenamiento de Archivos (Object Storage):** **AWS S3** o **Google Cloud Storage**
  - *Justificación:* El estándar de la industria para almacenar PDFs, imágenes y audios de manera segura y escalable a bajo costo.

### Inteligencia Artificial (Modelos)
- **Motor LLM Base:** Arquitectura agnóstica usando **LangChain / LlamaIndex**. Empezaremos usando **OpenAI GPT-4o** o **Anthropic Claude 3.5 Sonnet** por su potencia de razonamiento y visión, pero el código permitirá conectar modelos Open Source (ej. Llama 3) para privacidad si el usuario lo requiere.
- **Voz a Texto (STT):** **Deepgram** (o Whisper). Deepgram es ultra-rápido, lo que reduce la latencia en chats de voz en tiempo real.
- **Texto a Voz (TTS):** **ElevenLabs** o la nueva API de **OpenAI (Realtime)**. ElevenLabs ofrece las voces más expresivas y naturales, fundamentales para que no suene robótico.
- **Visión:** GPT-4o Vision o Claude 3.5 Vision.

### Autenticación y Seguridad
- **Tecnología:** **Supabase Auth** (o Firebase Auth)
- **Justificación:** Soluciones Backend-as-a-Service (BaaS) comprobadas que manejan OAuth, JWT, recuperación de contraseñas y MFA con estándares bancarios de seguridad.

### Infraestructura y DevOps
- **Tecnología:** **Docker** desplegado en **AWS App Runner** o **Google Cloud Run** (Serverless Containers).
- **Justificación:** Permite escalar automáticamente desde cero a miles de peticiones sin gestionar servidores. Muy económico al inicio y fácilmente migrable a Kubernetes (EKS/GKE) cuando el tráfico lo exija.

## 6. Estructura de Carpetas Sugerida (Fase Inicial del Repositorio)

```text
lucil-ai/
├── mobile/                   # App React Native (Expo)
│   ├── src/
│   │   ├── components/       # Componentes UI reutilizables (Botones, Chat Bubbles)
│   │   ├── screens/          # Vistas (Chat, Proyectos, Ajustes)
│   │   ├── services/         # Llamadas a la API y WebSockets
│   │   ├── store/            # Gestión de estado global (Zustand)
│   │   └── theme/            # Tokens de diseño (UX/UI)
├── backend/                  # FastAPI Python
│   ├── app/
│   │   ├── api/              # Endpoints HTTP y WebSockets
│   │   ├── core/             # Configuraciones, seguridad, inyección de dependencias
│   │   ├── db/               # Conexión a PostgreSQL y repositorios
│   │   ├── schemas/          # Modelos de validación Pydantic
│   │   ├── services/         # Lógica de negocio core (Usuarios, Archivos)
│   │   └── ai_engine/        # Prompts, memoria, RAG, STT, TTS
│   ├── tests/                # Pruebas automatizadas
│   └── requirements.txt      # Dependencias de Python
└── docs/                     # Documentos de arquitectura y manuales
```

## 7. Plan de Desarrollo por Fases

Para mantener los estándares profesionales y mitigar riesgos, el proyecto se dividirá en fases estrictas. Cada fase será diseñada, desarrollada y aprobada antes de pasar a la siguiente.

### Fase 1: Cimientos y Chat Core (MVP Base)
- **Objetivo:** Infraestructura base, aplicación móvil inicial y chat de texto inteligente.
- **Entregables:**
  - Repositorios configurados y estructura base.
  - Sistema de autenticación de usuarios.
  - Backend con FastAPI conectado a PostgreSQL.
  - Prompt Engineering para definir la personalidad, neutralidad y rigor médico de Lucil AI.
  - App móvil conectada al backend capaz de chatear por texto (sin memoria a largo plazo aún).

### Fase 2: Memoria Persistente, Proyectos y RAG
- **Objetivo:** Darle a Lucil memoria a largo plazo y capacidad de leer documentos.
- **Entregables:**
  - Organización de la interfaz por "Proyectos".
  - Implementación de `pgvector` y pipelines de embeddings.
  - Subida de PDFs, Word y Excel (integración con S3).
  - Búsqueda semántica inteligente (Lucil puede responder basándose en los documentos del proyecto).

### Fase 3: Voz y Visión en Tiempo Real
- **Objetivo:** Multimodalidad completa para una interacción natural.
- **Entregables:**
  - Infraestructura de WebSockets bidireccionales.
  - Integración de STT (voz a texto) para dictado y streaming.
  - Integración de TTS (texto a voz) con voces humanas ultrarrealistas.
  - Envío y análisis de imágenes directamente desde la cámara del móvil.

### Fase 4: Ecosistema Comercial y Plugins
- **Objetivo:** Evolución de herramienta personal a plataforma comercial SaaS.
- **Entregables:**
  - Sistema de suscripciones y pagos (Stripe).
  - Sistema de Plugins (Búsqueda web, calendario, herramientas externas).
  - Desarrollo de versión Web interactiva (aprovechando React).
  - Pruebas de carga, auditoría de seguridad y optimización de base de datos.
