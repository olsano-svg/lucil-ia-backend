class AgentManager:
    """
    Gestor de Agentes Especializados y Plugins (Herramientas Externas).
    Base preparada desde la Fase 1 para el futuro soporte de herramientas.
    """
    def __init__(self):
        self.registered_tools = {}
        self.registered_agents = {}
        
    def register_tool(self, name: str, tool_callable):
        """Registra un plugin o herramienta externa (ej. buscar en web, calendario)."""
        self.registered_tools[name] = tool_callable
        
    def get_specialized_agent(self, domain: str):
        """Devuelve un agente especializado (ej. 'medical_agent', 'coding_agent')."""
        pass
