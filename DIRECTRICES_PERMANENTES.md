# Directrices Arquitectónicas Permanentes: Lucil AI (Uso Exclusivo Personal)

Este documento reemplaza cualquier enfoque SaaS/comercial previo. Lucil AI se concibe y diseña estrictamente como un **Asistente Experto Personal de Uso Exclusivo**.

## 1. Naturaleza del Proyecto
- **Uso Exclusivo:** Lucil AI es para un único usuario. No se tomarán decisiones arquitectónicas basadas en "economía de escala", multitenencia masiva o reducción extrema de costos por usuario. La prioridad absoluta es la **calidad, profundidad y personalización**.

## 2. Metas de Aprendizaje y Memoria Persistente
- **Aprendizaje Continuo:** El sistema debe integrar retroalimentación constante. Cada conversación, documento, imagen o preferencia debe retroalimentar el perfil del usuario.
- **Sincronización Total (Omnipresencia):** Todo el historial de memoria a corto y largo plazo (RAG) debe estar sincronizado en tiempo real a través de todos los dispositivos del usuario, atado a su cuenta maestra. Ninguna información se pierde.

## 3. Rol de Asistente Experto Multidisciplinario
- **Profundidad de Razonamiento:** Las respuestas deben priorizar el razonamiento profundo, el análisis exhaustivo y la evidencia científica/técnica.
- **Disciplinas Core:** Medicina, psiquiatría, psicología, farmacología, nutrición, ingeniería, programación y tecnología.
- **Búsqueda de Evidencia:** El sistema debe estar integrado con capacidades de Agente para consultar documentación oficial, artículos científicos (PubMed, arXiv, etc.) y bases de datos especializadas, antes de emitir un análisis crítico.

## 4. Arquitectura Modular Inquebrantable
- **Agnosticismo de Proveedores:** El diseño debe mantener interfaces completamente desacopladas (`BaseLLMProvider`, `BaseVoiceProvider`, `BaseVisionProvider`).
- **Flexibilidad Tecnológica:** El sistema debe poder cambiar de modelo base (ej. de GPT-4o a Claude 3.5 Sonnet, o Llama 3) de forma instantánea sin refactorizar la lógica del negocio o del chat.

## 5. Regla de Desarrollo
- *Prohibido implementar características diseñadas exclusivamente para monetización masiva, restricciones artificiales de rate-limiting (salvo protección de API), o arquitecturas que sacrifiquen calidad de razonamiento por ahorro de centavos.*
