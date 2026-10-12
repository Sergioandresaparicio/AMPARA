# __init__.py dentro de tools/interviewer
# Este archivo inicializa el módulo Case Interviewer para Hermes

from .state_machine import StateMachineInterview
import json
import os

# Cargar configuración del grafo de entrevista
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "interview_graph.json")

with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    INTERVIEW_GRAPH = json.load(f)

# Función de interfaz estándar para el orquestador Hermes (Tool 1)
def state_machine_interview(user_input: str, case_state: dict = None) -> dict:
    """
    Herramienta Case Interviewer para Hermes.
    Procesa el mensaje del usuario contra la máquina de estados del caso.
    """
    if case_state:
        sm = StateMachineInterview.from_dict(case_state, graph_config=INTERVIEW_GRAPH)
    else:
        sm = StateMachineInterview(graph_config=INTERVIEW_GRAPH)
    
    step_result = sm.process_step(user_input)
    step_result["case_state"] = sm.to_dict()
    return step_result

# Exponer la clase principal y la función de Hermes
__all__ = ["StateMachineInterview", "INTERVIEW_GRAPH", "state_machine_interview"]
