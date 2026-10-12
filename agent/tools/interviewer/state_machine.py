def get_user_consent():
    # Aquí simulas la obtención de consentimiento
    return {"status": "accepted", "date": "2026-10-06", "method": "digital signature"}

def detect_representation(text: str) -> dict:
    """
    Detecta si la acción se interpone a título propio (primera persona)
    o como agente oficioso / abogado (tercera persona).
    """
    if not text:
        return {
            "type": "PROPIO",
            "person_mode": "first_person",
            "agent_name": "",
            "agent_id": "",
            "agent_role": "paciente_titular",
            "agency_reason": ""
        }
    t_lower = text.lower()

    # Prioridad 1: Declaración explícita a título propio
    propio_triggers = [
        "título propio", "titulo propio", "a nombre propio", "en mi propio nombre",
        "propio nombre", "yo soy el paciente", "yo soy la paciente", "para mí", "para mi",
        "soy yo mismo", "soy yo misma", "directamente yo", "personalmente yo"
    ]
    for p_trig in propio_triggers:
        if p_trig in t_lower:
            return {
                "type": "PROPIO",
                "person_mode": "first_person",
                "agent_name": "",
                "agent_id": "",
                "agent_role": "paciente_titular",
                "agency_reason": ""
            }

    # Prioridad 2: Agente oficioso / apoderado / tercero
    agency_triggers = [
        "agente oficioso", "agencia oficiosa", "agente de", "abogado", "abogada",
        "apoderad", "en representacion", "en representación", "representante",
        "para mi mama", "para mi mamá", "para mi papa", "para mi papá",
        "para mi hijo", "para mi hija", "para mi madre", "para mi padre",
        "mi cliente", "el paciente no puede", "la paciente no puede", "como familiar", "tercero"
    ]
    for trig in agency_triggers:
        if trig in t_lower:
            role = "abogado" if any(w in t_lower for w in ["abogado", "abogada", "apoderad"]) else "familiar_agente"
            return {
                "type": "AGENTE_OFICIOSO",
                "person_mode": "third_person",
                "agent_name": "Dr(a). Abogado / Agente Oficioso" if role == "abogado" else "Familiar / Agente Oficioso",
                "agent_id": "",
                "agent_role": role,
                "agency_reason": "Imposibilidad física, de salud o condición de vulnerabilidad del titular"
            }

    return {
        "type": "PROPIO",
        "person_mode": "first_person",
        "agent_name": "",
        "agent_id": "",
        "agent_role": "paciente_titular",
        "agency_reason": ""
    }

def classify_case(user_input):
    # Clasificación automática del caso según palabras clave
    if "medicamento" in user_input.lower():
        return "medicamento"
    elif "cita" in user_input.lower():
        return "cita"
    elif "tratamiento" in user_input.lower():
        return "tratamiento"
    elif "procedimiento" in user_input.lower():
        return "procedimiento"
    else:
        return "respuesta_administrativa"

def required_fields(case_type):
    # Campos obligatorios según tipo de caso
    base_fields = ["request.description", "request.date_requested", "entity.name", "response.status", "impact.urgency"]
    if case_type == "medicamento":
        base_fields.append("documents.medical_order")
    return base_fields

def get_user_response(field):
    # Simulación: en Hermes esto se conecta al flujo conversacional
    return "respuesta simulada"

def validate_answer(answer, field):
    # Validación básica
    if answer and answer.strip():
        return answer
    return None

def assess_risk(case_data):
    # Evaluación simple de riesgo
    if case_data.get("impact.urgency") == "Crítica":
        return "high"
    elif case_data.get("impact.urgency") == "Alta":
        return "medium"
    else:
        return "low"

def calculate_confidence(case_data):
    # Score de confianza (ejemplo simple)
    return 0.95

def calculate_completion(case_data):
    # Score de completitud
    total = len(case_data.keys())
    filled = len([v for v in case_data.values() if v])
    return filled / total

def current_time():
    import datetime
    return datetime.datetime.now().isoformat()


import uuid
import re

class StateMachineInterview:
    """
    Máquina de estados para la fase 1 (Case Interviewer) de AMPARA en Hermes.
    Gestiona el ciclo: Consentimiento -> Clasificación -> Recolección guiada -> Evaluación de Riesgo -> Completitud.
    Preserva compatibilidad con las funciones base y el esquema de entrevista.
    """

    STATES = ["CONSENT", "CLASSIFICATION", "COLLECTION", "RISK_ASSESSMENT", "COMPLETED"]

    def __init__(self, case_id: str = None, graph_config: dict = None):
        self.case_id = case_id or f"AMP-{uuid.uuid4().hex[:8].upper()}"
        self.current_state = "CONSENT"
        self.phase = "pending"  # pending | in_progress | completed
        self.case_type = "medicamento"
        self.consent = {
            "status": "pending",
            "date": None,
            "method": "digital signature"
        }
        self.representation = {
            "type": "PROPIO",
            "person_mode": "first_person",
            "agent_name": "",
            "agent_id": "",
            "agent_role": "paciente_titular",
            "agency_reason": ""
        }
        self.facts = {
            "case_type": "medicamento",
            "representation": self.representation,
            "request": {
                "description": "",
                "date_requested": "",
                "method": "verbal_o_escrito",
                "radicado": ""
            },
            "entity": {
                "name": "",
                "type": "EPS",
                "regime": "Contributivo"
            },
            "response": {
                "status": "Sin respuesta",
                "date": None,
                "document": None
            },
            "impact": {
                "urgency": "Normal",
                "reason": ""
            },
            "documents": {
                "medical_order": "",
                "request_file": "",
                "response_file": "",
                "clinical_history": ""
            },
            "special_protection": {
                "is_protected": False,
                "category": ""
            }
        }
        self.risk_level = "low"  # low | medium | high | critical
        self.critical_flag = False
        self.critical_reason = None
        self.confidence_score = 0.85
        self.completion_score = 0.0
        self.history = []  # List of {role, content, timestamp}
        self.current_field_index = 0

        # Cargar configuración si está provista
        self.config = graph_config or {}
        self.flow_config = self.config.get("interview_flow", {})
        self.field_prompts = self.flow_config.get("field_prompts", {
            "entity.name": "¿A qué EPS te encuentras afiliado/a? (ej. Sura, Nueva EPS, Sanitas, Salud Total, Capital Salud)",
            "request.description": "¿Qué medicamento, cita o procedimiento específico te fue ordenado por tu médico tratante?",
            "request.date_requested": "¿En qué fecha te fue formulado o cuándo solicitaste el servicio a la EPS?",
            "response.status": "¿La EPS te dio alguna respuesta formal? (ej. Negado, Sin existencias, En trámite, o Sin respuesta)",
            "impact.urgency": "¿Cuál es la urgencia de tu situación de salud? (ej. Normal, Alta, Crítica)",
            "documents.medical_order": "¿Tienes la fórmula médica u orden a la mano? (Sí / No)"
        })

    def is_consent_given(self) -> bool:
        return self.consent.get("status") == "accepted"

    def is_critical(self) -> bool:
        return self.critical_flag or self.risk_level == "critical"

    def is_ready_for_next_phase(self) -> bool:
        return self.current_state == "COMPLETED" or self.phase == "completed"

    def get_missing_fields(self) -> list:
        required = required_fields(self.case_type)
        missing = []
        for field in required:
            val = self.get_field_value(field)
            if not val or not str(val).strip():
                missing.append(field)
        return missing

    def get_field_value(self, field_path: str):
        parts = field_path.split(".")
        target = self.facts
        for part in parts:
            if isinstance(target, dict) and part in target:
                target = target[part]
            else:
                return None
        return target

    def set_field_value(self, field_path: str, value):
        parts = field_path.split(".")
        target = self.facts
        for part in parts[:-1]:
            if part not in target or not isinstance(target[part], dict):
                target[part] = {}
            target = target[part]
        target[parts[-1]] = value

    def check_critical_triggers(self, text: str) -> bool:
        if not text:
            return False
        text_lower = text.lower()
        critical_keywords = [
            "cáncer", "quimioterapia", "diálisis", "uci", "infarto", "oxígeno",
            "trasplante", "inminente", "vih", "antirretroviral", "urgencia vital",
            "riesgo de muerte", "paro cardíaco", "convulsiones"
        ]
        for kw in critical_keywords:
            if kw in text_lower:
                self.critical_flag = True
                self.risk_level = "critical"
                self.critical_reason = f"Palabra clave de riesgo vital detectada: '{kw}'"
                return True
        return False

    def update_metrics(self):
        reqs = required_fields(self.case_type)
        if not reqs:
            self.completion_score = 1.0
            return
        filled = 0
        for r in reqs:
            val = self.get_field_value(r)
            if val and str(val).strip():
                filled += 1
        self.completion_score = round(filled / len(reqs), 2)
        
        # Evaluar riesgo si no es crítico ya
        if not self.critical_flag:
            urgency_str = str(self.facts.get("impact", {}).get("urgency", "Normal"))
            self.risk_level = assess_risk({"impact.urgency": urgency_str})
        
        # Calcular confianza
        self.confidence_score = calculate_confidence(self.facts)

    def get_next_prompt(self) -> str:
        if self.current_state == "CONSENT":
            return (
                "Bienvenido/a a **AMPARA**, tu asistente para la protección de tu derecho a la salud.\n\n"
                "Para poder orientarte y redactar los documentos pertinentes, necesitamos tu autorización para "
                "tratar tus datos personales y de salud con total confidencialidad (Ley 1581 de 2012).\n"
                "¿Autorizas el tratamiento de tus datos para este trámite? (Responde **Sí** o **No**)."
            )
        
        if self.current_state == "CLASSIFICATION":
            return (
                "Gracias. Para estructurar correctamente tu solicitud y la técnica de redacción de los hechos:\n\n"
                "1. ¿Esta acción de tutela la vas a presentar **a título propio** (directamente por el paciente) o como **agente oficioso / abogado** (en favor de otra persona)?\n"
                "*(Nota: Si es a título propio redactaremos en primera persona del singular; si es como agente oficioso o abogado redactaremos en tercera persona conforme al precedente constitucional).*\n\n"
                "2. Cuéntame brevemente: ¿cuál es tu caso o inconveniente con el servicio de salud? (ej. falta de entrega de medicamentos, cita especializada demorada, cirugía pendiente o negativa de autorización)."
            )

        if self.current_state == "COLLECTION":
            missing = self.get_missing_fields()
            if missing:
                next_field = missing[0]
                prompt = self.field_prompts.get(next_field)
                if not prompt:
                    prompt = f"Por favor indícanos información sobre: {next_field}"
                return prompt
            else:
                self.current_state = "RISK_ASSESSMENT"
                return self.get_next_prompt()

        if self.current_state == "RISK_ASSESSMENT":
            if self.is_critical():
                return (
                    f"**ALERTA DE PRIORIDAD VITAL DETECTADA**: Hemos identificado un caso de alta urgencia ({self.critical_reason}). "
                    "Se ha generado una bandera de atención inmediata. ¿Deseas agregar algún detalle clínico adicional antes de generar el borrador de acción legal?"
                )
            return (
                "Hemos completado la información base de tu caso. ¿Consideras que la falta de este servicio pone en riesgo tu salud de forma grave o genera dolor insoportable? (Normal / Alta / Crítica)"
            )

        if self.current_state == "COMPLETED":
            return (
                "¡Excelente! Toda la información requerida para tu caso ha sido recolectada y validada. "
                "Estamos listos para proceder a la búsqueda jurisprudencial y la generación de tu memorial (Derecho de Petición o Acción de Tutela)."
            )


        return "¿En qué más podemos ayudarte respecto a tu caso de salud?"

    def process_step(self, user_input: str) -> dict:
        """
        Procesa el turno conversacional del usuario según el estado actual de la máquina.
        Retorna un diccionario estructurado apto para el orquestador Hermes.
        """
        user_input_clean = user_input.strip() if user_input else ""
        self.history.append({
            "role": "user",
            "content": user_input_clean,
            "timestamp": current_time()
        })

        # Chequeo continuo de riesgo vital en cualquier mensaje
        self.check_critical_triggers(user_input_clean)

        next_action = "continue_interview"
        human_review_required = False

        if self.current_state == "CONSENT":
            lower_input = user_input_clean.lower()
            if any(pos in lower_input for pos in ["sí", "si", "acepto", "autorizo", "de acuerdo", "ok", "claro"]):
                self.consent = {
                    "status": "accepted",
                    "date": current_time()[:10],
                    "method": "digital signature"
                }
                self.current_state = "CLASSIFICATION"
                self.phase = "in_progress"
            elif any(neg in lower_input for neg in ["no", "rechazo", "no autorizo", "no acepto"]):
                self.consent = {
                    "status": "rejected",
                    "date": current_time()[:10],
                    "method": "digital signature"
                }
                return {
                    "status": "consent_rejected",
                    "message": "Entendido. Sin tu consentimiento no podemos almacenar ni procesar datos de salud. El proceso se detiene aquí.",
                    "phase": "stopped",
                    "human_review_required": False
                }
            else:
                return {
                    "status": "awaiting_consent",
                    "message": "Para continuar es necesario que nos confirmes si aceptas el tratamiento de tus datos de salud (Sí / No).",
                    "current_state": "CONSENT"
                }

        elif self.current_state == "CLASSIFICATION":
            rep = detect_representation(user_input_clean)
            self.representation = rep
            self.facts["representation"] = rep
            classified = classify_case(user_input_clean)
            self.case_type = classified
            self.facts["case_type"] = classified
            self.facts["request"]["description"] = user_input_clean
            self.current_state = "COLLECTION"

        elif self.current_state == "COLLECTION":
            missing = self.get_missing_fields()
            if missing:
                current_target_field = missing[0]
                val = validate_answer(user_input_clean, current_target_field)
                if val:
                    self.set_field_value(current_target_field, val)
                
                # Re-evaluar campos faltantes
                remaining_missing = self.get_missing_fields()
                if not remaining_missing:
                    self.current_state = "RISK_ASSESSMENT"

        elif self.current_state == "RISK_ASSESSMENT":
            if any(term in user_input_clean.lower() for term in ["crítica", "critica", "urgente", "vital", "inminente"]):
                self.facts["impact"]["urgency"] = "Crítica"
                self.critical_flag = True
                self.risk_level = "critical"
            elif any(term in user_input_clean.lower() for term in ["alta", "grave", "severo"]):
                self.facts["impact"]["urgency"] = "Alta"
                self.risk_level = "high"
            else:
                self.facts["impact"]["urgency"] = "Normal"
                self.risk_level = "low"
            
            self.current_state = "COMPLETED"
            self.phase = "completed"

        elif self.current_state == "COMPLETED":
            next_action = "proceed_to_legal_rag"

        self.update_metrics()

        # Determinar si requiere intervención humana (HITL)
        if self.is_critical():
            human_review_required = True

        response_prompt = self.get_next_prompt()
        self.history.append({
            "role": "assistant",
            "content": response_prompt,
            "timestamp": current_time()
        })

        return {
            "case_id": self.case_id,
            "current_state": self.current_state,
            "phase": self.phase,
            "prompt": response_prompt,
            "next_prompt": response_prompt,
            "missing_fields": self.get_missing_fields(),
            "completion_score": self.completion_score,
            "confidence_score": self.confidence_score,
            "risk_level": self.risk_level,
            "critical_escalation": self.is_critical(),
            "critical_reason": self.critical_reason,
            "human_review_required": human_review_required,
            "consent_status": self.consent.get("status"),
            "representation": self.representation,
            "representation_type": self.representation["type"],
            "person_mode": self.representation["person_mode"],
            "next_action": next_action
        }

    def to_dict(self) -> dict:
        """
        Serializa el estado del caso en el formato exacto de interview_graph.json
        y apto para el registro S4 de Hermes y persistencia en DB.
        """
        return {
            "case_id": self.case_id,
            "phase": self.phase,
            "facts": [self.facts],
            "representation": self.representation,
            "representation_type": self.representation["type"],
            "person_mode": self.representation["person_mode"],
            "missing_fields": self.get_missing_fields(),
            "confidence_score": self.confidence_score,
            "completion_score": self.completion_score,
            "consent": self.consent,
            "risk_level": self.risk_level,
            "critical_flag": self.critical_flag,
            "critical_reason": self.critical_reason,
            "current_state": self.current_state,
            "timestamp": current_time()
        }

    @classmethod
    def from_dict(cls, data: dict, graph_config: dict = None):
        """
        Reconstruye una instancia de StateMachineInterview desde un diccionario persistido.
        """
        instance = cls(case_id=data.get("case_id"), graph_config=graph_config)
        instance.phase = data.get("phase", "pending")
        instance.current_state = data.get("current_state", "CONSENT")
        if data.get("facts") and isinstance(data["facts"], list) and len(data["facts"]) > 0:
            instance.facts = data["facts"][0]
            instance.case_type = instance.facts.get("case_type", "medicamento")
            if "representation" in instance.facts:
                instance.representation = instance.facts["representation"]
        if "representation" in data:
            instance.representation = data["representation"]
        elif "representation_type" in data:
            rep_type = data["representation_type"]
            instance.representation = {
                "type": rep_type,
                "person_mode": "third_person" if "OFICI" in rep_type or "ABOGAD" in rep_type else "first_person",
                "agent_name": data.get("agent_name", ""),
                "agent_id": data.get("agent_id", ""),
                "agent_role": "abogado" if "ABOGAD" in rep_type else "paciente_titular",
                "agency_reason": ""
            }
        instance.facts["representation"] = instance.representation
        instance.consent = data.get("consent", instance.consent)
        instance.risk_level = data.get("risk_level", "low")
        instance.critical_flag = data.get("critical_flag", False)
        instance.critical_reason = data.get("critical_reason")
        instance.confidence_score = data.get("confidence_score", 0.85)
        instance.completion_score = data.get("completion_score", 0.0)
        return instance
