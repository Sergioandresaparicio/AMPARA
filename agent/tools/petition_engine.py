"""
Petition Generator - Tool 4 para Hermes (AMPARA)
Módulo: agent/tools/petition_engine.py

Motor generador y ensamblador de memoriales jurídicos procesales para la defensa
del derecho fundamental a la salud en Colombia.

Cubre todas las acciones y tipologías fácticas posibles:
1. Acciones Jurídicas:
   - ACCION_TUTELA (Tutela ordinaria)
   - TUTELA_CON_MEDIDA_PROVISIONAL (Con medidas cautelares urgentes Art. 7 Dec. 2591/91)
   - DERECHO_PETICION (Derecho de petición previo Art. 23 CP)
   - INCIDENTE_DESACATO (Incumplimiento de fallo judicial Art. 52 Dec. 2591/91)
   - IMPUGNACION_FALLO (Recurso contra fallo adverso Art. 31 Dec. 2591/91)

2. Materias Fácticas en Salud:
   - MEDICAMENTO (Medicamentos vitales, oncológicos, PBS y No PBS / Mipres)
   - TRATAMIENTO_INTEGRAL (Protección continua para evitar tutelas sucesivas)
   - PROCEDIMIENTO_CIRUGIA (Citas con especialista, intervenciones quirúrgicas prioritarias)
   - TRANSPORTE_VIATICOS (Traslados y hospedaje paciente + acompañante)
   - INSUMOS_DISPOSITIVOS (Sillas de ruedas, pañales, prótesis, oxígeno)
   - CONTINUIDAD_SERVICIO (Interrupción injustificada por cambio o liquidación de EPS)
   - EXONERACION_PAGOS (Exoneración de copagos y cuotas moderadoras por falta de recursos)
   - ENFERMERIA_CUIDADOR (Enfermería domiciliaria o cuidador primario)
"""

import os
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional, Union

try:
    import docx
    from docx.shared import Inches, Pt, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

# =====================================================================
# CONSTANTES Y CONFIGURACIONES PROCESALES
# =====================================================================

VALID_ACTION_TYPES = [
    "ACCION_TUTELA",
    "TUTELA_CON_MEDIDA_PROVISIONAL",
    "DERECHO_PETICION",
    "INCIDENTE_DESACATO",
    "IMPUGNACION_FALLO"
]

VALID_HEALTH_SUBJECTS = [
    "MEDICAMENTO",
    "TRATAMIENTO_INTEGRAL",
    "PROCEDIMIENTO_CIRUGIA",
    "TRANSPORTE_VIATICOS",
    "INSUMOS_DISPOSITIVOS",
    "CONTINUIDAD_SERVICIO",
    "EXONERACION_PAGOS",
    "ENFERMERIA_CUIDADOR"
]

FUNDAMENTAL_RIGHTS = {
    "salud": "El Derecho Fundamental a la Salud (Art. 49 de la Constitución Política y Ley Estatutaria 1751 de 2015, arts. 1, 2, 8 y 10).",
    "vida_digna": "El Derecho a la Vida en condiciones dignas y justas (Art. 11 de la Constitución Política).",
    "integridad": "El Derecho a la Integridad Física y Personal (Art. 12 de la Constitución Política).",
    "seguridad_social": "El Derecho a la Seguridad Social integral (Art. 48 de la Constitución Política).",
    "debido_proceso": "El Derecho al Debido Proceso Administrativo y Confianza Legítima (Art. 29 de la Constitución Política).",
    "igualdad": "El Derecho a la Igualdad y Protección Especial a Sujetos de Especial Protección Constitucional (Art. 13 de la Constitución Política)."
}


# =====================================================================
# CLASE PRINCIPAL: PetitionGeneratorEngine
# =====================================================================

class PetitionGeneratorEngine:
    """
    Ensamblador modular de memoriales procesales colombianos para tutelas y derechos de petición.
    """

    def __init__(self):
        pass

    def detect_action_type(
        self,
        case_data: Dict[str, Any],
        user_specified: Optional[str] = None
    ) -> str:
        """
        Determina automáticamente la acción procesal adecuada según el caso o directriz explícita.
        """
        if user_specified and user_specified.upper() in VALID_ACTION_TYPES:
            return user_specified.upper()

        urgency = str(case_data.get("urgency_level", "")).lower()
        critical_escalation = bool(case_data.get("critical_escalation", False))
        phase = str(case_data.get("phase", "")).lower()

        if "desacato" in phase or case_data.get("is_desacato", False):
            return "INCIDENTE_DESACATO"
        elif "impugna" in phase or case_data.get("is_impugnacion", False):
            return "IMPUGNACION_FALLO"
        elif "peticion" in phase or case_data.get("is_peticion_previa", False):
            return "DERECHO_PETICION"
        elif urgency == "critical" or critical_escalation or case_data.get("solicita_medida_provisional", False):
            return "TUTELA_CON_MEDIDA_PROVISIONAL"
        else:
            return "ACCION_TUTELA"

    def detect_subject_matter(self, case_data: Dict[str, Any]) -> str:
        """
        Identifica la materia fáctica de salud predominante en el caso.
        """
        facts_text = ""
        if isinstance(case_data.get("facts"), list):
            facts_text = " ".join([str(f.get("details", "") or f.get("case_type", "")) for f in case_data["facts"]]).lower()
        elif isinstance(case_data.get("facts"), str):
            facts_text = case_data["facts"].lower()

        category = str(case_data.get("category", "")).lower()
        combined = f"{facts_text} {category}"

        if any(w in combined for w in ["transporte", "viatico", "alojamiento", "traslado municipal"]):
            return "TRANSPORTE_VIATICOS"
        elif any(w in combined for w in ["cirugia", "cirugía", "especialista", "cita medica", "cita médica", "procedimiento"]):
            return "PROCEDIMIENTO_CIRUGIA"
        elif any(w in combined for w in ["silla de ruedas", "pañal", "panal", "insumo", "oxigeno", "oxígeno", "protesis", "prótesis"]):
            return "INSUMOS_DISPOSITIVOS"
        elif any(w in combined for w in ["integral", "tratamiento continuo", "todas las ordenes"]):
            return "TRATAMIENTO_INTEGRAL"
        elif any(w in combined for w in ["copago", "cuota moderadora", "exoneracion", "exoneración", "sin recursos"]):
            return "EXONERACION_PAGOS"
        elif any(w in combined for w in ["cuidador", "enfermera", "enfermeria", "enfermería"]):
            return "ENFERMERIA_CUIDADOR"
        elif any(w in combined for w in ["cambio de eps", "traslado eps", "interrupcion", "continuidad"]):
            return "CONTINUIDAD_SERVICIO"
        else:
            return "MEDICAMENTO"

    def build_header(
        self,
        action_type: str,
        city: str = "Bogotá D.C.",
        patient_name: str = "",
        eps_name: str = "",
        acting_as: str = "propio",
        representative_name: Optional[str] = None
    ) -> str:
        """Construye el encabezado judicial y designación de autoridad competente."""
        now = datetime.now()
        fecha_str = f"{city}, {now.day} de {self._mes_espanol(now.month)} de {now.year}"
        nombre_acc = patient_name.upper() if patient_name else "[NOMBRE DEL ACCIONANTE]"
        nombre_eps = eps_name.upper() if eps_name else "[EPS ACCIONADA]"

        if acting_as == "agente_oficioso" and representative_name:
            parte_actora_header = f"{representative_name.upper()} (COMO AGENTE OFICIOSO DE {nombre_acc})"
        elif acting_as == "representante_legal" and representative_name:
            parte_actora_header = f"{representative_name.upper()} (REPRESENTANTE LEGAL DE {nombre_acc})"
        else:
            parte_actora_header = nombre_acc

        if action_type == "DERECHO_PETICION":
            return f"""{fecha_str}

Señores:
GERENCIA Y ÁREA DE ATENCIÓN AL USUARIO
{nombre_eps}
Ciudad.

ASUNTO: DERECHO DE PETICIÓN EN SALUD (ARTÍCULO 23 CONSTITUCIÓN POLÍTICA Y LEY 1755 DE 2015)
PETICIONARIO(A): {parte_actora_header}
"""
        elif action_type == "INCIDENTE_DESACATO":
            return f"""{fecha_str}

Señor(a):
JUEZ CONSTITUCIONAL DE CONOCIMIENTO (DESPACHO QUE PROFIRIÓ EL FALLO)
E. S. D.

REF.: TRÁMITE INCIDENTAL DE DESACATO (ARTÍCULOS 27 Y 52 DEL DECRETO 2591 DE 1991)
ACCIONANTE: {parte_actora_header}
ACCIONADA: {nombre_eps}
RADICADO DEL PROCESO: [NÚMERO DE RADICADO JUDICIAL]
"""
        elif action_type == "IMPUGNACION_FALLO":
            return f"""{fecha_str}

Señor(a):
JUEZ CONSTITUCIONAL DE PRIMERA INSTANCIA
E. S. D.

REF.: RECURSO DE IMPUGNACIÓN CONTRA SENTENCIA DE TUTELA (ARTÍCULOS 31 Y 32 DEL DECRETO 2591 DE 1991)
ACCIONANTE: {parte_actora_header}
ACCIONADA: {nombre_eps}
RADICADO: [NÚMERO DE RADICADO JUDICIAL]
"""
        else:
            medida_tag = " CON SOLICITUD DE MEDIDA CAUTELAR PROVISIONAL URGENTE (ART. 7 DEC. 2591/91)" if action_type == "TUTELA_CON_MEDIDA_PROVISIONAL" else ""
            return f"""{fecha_str}

Señor(a):
JUEZ CONSTITUCIONAL (REPARTO)
Juzgado Municipal / del Circuito de {city}
E. S. D.

REF.: ACCIÓN DE TUTELA PARA LA PROTECCIÓN INMEDIATA DE DERECHOS FUNDAMENTALES{medida_tag}
ACCIONANTE: {parte_actora_header}
ACCIONADA: {nombre_eps}
VINCULADA: ADMINISTRADORA DE LOS RECURSOS DEL SGSSS - ADRES (SI APLICA)
"""

    def build_identification_parties(
        self,
        patient_name: str,
        patient_id: str,
        eps_name: str,
        acting_as: str = "propio",
        representative_name: Optional[str] = None,
        representative_id: Optional[str] = None,
        city: str = "esta ciudad"
    ) -> str:
        """Estructura la personería sustantiva y legitimación en la causa por activa y pasiva."""
        rep_id_str = f" con cédula de ciudadanía No. **{representative_id}**" if representative_id else ""
        if acting_as == "agente_oficioso" and representative_name:
            personeria = f"""Yo, **{representative_name}**, mayor de edad, domiciliado(a) en {city},{rep_id_str} actuando en calidad de **AGENTE OFICIOSO** conforme a lo consagrado en el **Artículo 10 del Decreto 2591 de 1991** y la reiterada jurisprudencia constitucional (Sentencias T-510 de 2024, T-445 de 2023 y T-001 de 2018), en defensa y amparo de los derechos fundamentales de **{patient_name}**, identificado(a) con documento No. **{patient_id}**, quien debido a su delicado estado de salud, debilidad manifiesta e imposibilidad física no puede acudir de forma directa y presencial ante este despacho judicial."""
            beneficiario_pasiva = f"a favor de mi agenciado(a) **{patient_name}**"
        elif acting_as == "representante_legal" and representative_name:
            personeria = f"""Yo, **{representative_name}**, mayor de edad, identificado(a) al pie de mi firma,{rep_id_str} actuando como **REPRESENTANTE LEGAL** del paciente **{patient_name}** (documento No. **{patient_id}**)."""
            beneficiario_pasiva = f"a favor de mi representado(a) **{patient_name}**"
        else:
            personeria = f"""Yo, **{patient_name}**, mayor de edad, domiciliado(a) en {city}, identificado(a) con cédula de ciudadanía No. **{patient_id}**, actuando en mi propio nombre y representación en defensa de mis derechos fundamentales."""
            beneficiario_pasiva = "de mi plan de beneficios en salud y mi persona"

        return f"""### I. PARTES PROCESALES Y LEGITIMACIÓN

**1. PARTE ACCIONANTE (LEGITIMACIÓN POR ACTIVA):**
{personeria}

**2. PARTE ACCIONADA (LEGITIMACIÓN POR PASIVA):**
Se interpone la presente acción constitucional en contra de **{eps_name}**, entidad promotora de salud con domicilio y representación legal en esta jurisdicción, entidad encargada de garantizar la prestación efectiva, oportuna e ininterrumpida {beneficiario_pasiva} (Art. 42 numerales 2 y 3 del Decreto 2591 de 1991).

**3. TERCERO VINCULADO (DE OFICIO):**
Se solicita al Despacho vincular a la **ADMINISTRADORA DE LOS RECURSOS DEL SISTEMA GENERAL DE SEGURIDAD SOCIAL EN SALUD (ADRES)** para que concurra y garantice la financiación o repetición administrativa que conforme a la ley corresponda sin dilatar la atención clínica.
"""

    def build_provisional_measure_section(
        self,
        action_type: str,
        subject: str,
        patient_name: str,
        eps_name: str,
        prescription_item: str = "medicamentos y tecnologías en salud prescritos",
        acting_as: str = "propio"
    ) -> str:
        """Redacta la solicitud perentoria de Medidas Cautelares Provisionales bajo el Art. 7 Dec. 2591/91."""
        if action_type != "TUTELA_CON_MEDIDA_PROVISIONAL":
            return ""

        destinatario = f"a favor de mi agenciado(a) **{patient_name}**" if acting_as == "agente_oficioso" else f"al suscrito accionante **{patient_name}**"
        periculum_target = "de mi agenciado(a)" if acting_as == "agente_oficioso" else "del suscrito"

        return f"""### II. SOLICITUD PERENTORIA DE MEDIDA CAUTELAR PROVISIONAL
**(ARTÍCULO 7 DEL DECRETO 2591 DE 1991)**

Con fundamento en el **Artículo 7 del Decreto 2591 de 1991**, respetuosamente solicito a su Despacho que desde el momento mismo de la admisión de la presente tutela decrete **MEDIDA PROVISIONAL URGENTE**, ordenando de forma perentoria e inmediata a **{eps_name}** que, en un término improrrogable no superior a **CUARENTA Y OCHO (48) HORAS**, autorice, suministre y entregue efectivamente {destinatario}:

> **{prescription_item}**

**Sustentación de la Medida Cautelar:**
1. *Fumus Boni Iuris (Apariencia de Buen Derecho):* Existe orden médica prescrita por el profesional tratante adscrito a la red de la accionada, demostrando la necesidad médica insustituible del servicio.
2. *Periculum In Mora (Peligro en la Demora y Riesgo de Daño Irreparable):* Toda dilación en el suministro pone en riesgo cierto e inminente la vida y la integridad personal {periculum_target}, generando un deterioro irreversible en el estado clínico que haría ineficaz el fallo definitivo.
"""

    def build_facts(
        self,
        case_data: Dict[str, Any],
        document_analyses: Optional[List[Dict[str, Any]]] = None,
        acting_as: str = "propio"
    ) -> str:
        """
        Construye los hechos cronológicos bajo la estructura canónica de 6 hechos
        de las sentencias de la Corte Constitucional (afiliación, diagnóstico, prescripción,
        omisión EPS, vida digna/daño irreparable y capacidad económica).
        Alterna gramaticalmente:
        - acting_as == 'propio': Primera persona del singular (yo/me).
        - acting_as == 'agente_oficioso': Tercera persona en calidad de agente oficioso (mi agenciado/su).
        """
        patient_name = case_data.get("patient_name", "El paciente")
        eps_name = case_data.get("eps_name", "la EPS accionada")
        diag = case_data.get("diagnosis", "patología clínica documentada")
        item_ordenado = case_data.get("prescription_item", "el servicio, medicamento o tecnología médica ordenada")
        is_agente = (acting_as == "agente_oficioso")

        facts_list = []

        # Hecho 1: Afiliación y Obligación Legal de la EPS
        if is_agente:
            facts_list.append(
                f"Mi agenciado(a), **{patient_name}**, se encuentra formalmente afiliado(a) a la EPS accionada **{eps_name}**, "
                f"entidad que percibe la Unidad de Pago por Capitación (UPC) correspondiente y sobre la cual recae el deber constitucional y legal ineludible "
                f"de garantizar de forma continua, oportuna e ininterrumpida la cobertura integral de su plan de beneficios en salud."
            )
        else:
            facts_list.append(
                f"Me encuentro formalmente afiliado(a) a la EPS accionada **{eps_name}**, entidad que percibe la Unidad de Pago por Capitación (UPC) "
                f"correspondiente y sobre la cual recae el deber legal de garantizar de manera continua, oportuna e ininterrumpida mi plan de beneficios en salud."
            )

        # Hecho 2: Diagnóstico Clínico y Condición de Debilidad Manifiesta
        if is_agente:
            facts_list.append(
                f"Mi agenciado(a) padece de: **{diag}**, encontrándose en tratamiento activo y bajo control médico periódico. "
                f"En razón a la severidad de su condición de salud, es un sujeto de especial protección constitucional en estado de debilidad manifiesta."
            )
        else:
            facts_list.append(
                f"Fui diagnosticado(a) clínicamente con la patología: **{diag}**, encontrándome en tratamiento activo y bajo control médico periódico. "
                f"En razón a mi estado de salud y patología, soy sujeto de especial protección constitucional en estado de debilidad manifiesta."
            )

        # Hecho 3: Prescripción Médica Insustituible
        if is_agente:
            facts_list.append(
                f"Con ocasión de dicha patología, el médico tratante adscrito a la entidad accionada prescribió formalmente: **{item_ordenado}**, "
                f"tecnología insustituible requerida con urgencia para controlar la evolución de la enfermedad y preservar la funcionalidad e integridad física del paciente."
            )
        else:
            facts_list.append(
                f"Con ocasión de dicha patología, mi médico tratante adscrito a la red de la accionada prescribió formalmente: **{item_ordenado}**, "
                f"tecnología insustituible requerida con urgencia para salvaguardar mi salud, mitigar mi padecimiento y preservar mi integridad física."
            )

        # Hechos documentales extraídos por Document Analyzer (Tool 3)
        if document_analyses:
            for doc in document_analyses:
                summary = doc.get("summary_for_tutela")
                if summary:
                    doc_desc = doc.get("document_description", doc.get("document_type", "Documento clínico"))
                    facts_list.append(f"Conforme se acredita en soporte documental aportado ({doc_desc}): {summary}")

        # Hecho 4: Negativa, Dilación o Barrera Administrativa de la EPS
        if is_agente:
            facts_list.append(
                f"A pesar de existir orden médica formal y solicitudes debidamente presentadas, la accionada **{eps_name}** ha dilatado injustificadamente "
                f"o negado la autorización y suministro del requerimiento médico a favor de mi agenciado(a), imponiendo barreras administrativas y desconociendo los mandatos de oportunidad y continuidad."
            )
        else:
            facts_list.append(
                f"A pesar de contar con prescripción médica formal y haber agotado las gestiones pertinentes, la accionada **{eps_name}** ha dilatado injustificadamente "
                f"o negado la entrega efectiva de lo formulado, trasladando barreras administrativas a mi persona y vulnerando el principio de oportunidad y continuidad en el servicio de salud."
            )

        # Hecho 5: Afectación a la Vida Digna y Riesgo Inminente de Perjuicio Irremediable
        if is_agente:
            facts_list.append(
                f"La omisión e interrupción en la atención médica agrava progresivamente el estado clínico de mi agenciado(a), provocándole dolor severo, "
                f"deterioro orgánico acelerado y exponiéndolo(a) a un grave e inminente riesgo de perjuicio irremediable en su vida e integridad personal."
            )
        else:
            facts_list.append(
                f"La falta de acceso oportuno al tratamiento agrava progresivamente mi cuadro clínico, provocándome dolores constantes, deterioro orgánico "
                f"y colocándome en una situación de inminente perjuicio irremediable contra mi vida e integridad personal."
            )

        # Hecho 6: Falta de Capacidad Económica
        if is_agente:
            facts_list.append(
                f"Ni mi agenciado(a) ni su núcleo familiar cuentan con la capacidad económica suficiente para costear o sufragar de su propio peculio "
                f"el tratamiento o medicamento ordenado, configurándose la imposibilidad material de asumirlo por vía privada conforme al precedente constitucional."
            )
        else:
            facts_list.append(
                f"Ni el suscrito accionante ni mi núcleo familiar contamos con la capacidad económica suficiente para costear de nuestro propio bolsillo "
                f"el tratamiento o medicamento formulado, dada su onerosa cuantía, por lo que requiero el amparo constitucional para evitar un desenlace lesivo."
            )

        out = "### III. HECHOS Y ANTECEDENTES RELEVANTES\n\n"
        for i, f in enumerate(facts_list, 1):
            out += f"**{i}.** {f}\n\n"
        return out

    def build_rights_violated(self) -> str:
        """Estructura el capítulo de derechos fundamentales quebrantados."""
        out = "### IV. DERECHOS FUNDAMENTALES VULNERADOS\n\n"
        out += "La conducta omisiva de la entidad accionada vulnera directamente los siguientes derechos de rango constitucional:\n\n"
        for r_name, r_desc in FUNDAMENTAL_RIGHTS.items():
            out += f"* **{r_name.replace('_', ' ').title()}:** {r_desc}\n"
        return out + "\n"

    def build_legal_basis(
        self,
        subject: str,
        legal_sources: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """Estructura los fundamentos de derecho integrando citas del RAG (Tool 2)."""
        out = "### V. FUNDAMENTOS JURÍDICOS Y PRECEDENTE CONSTITUCIONAL\n\n"
        out += "La procedencia del amparo constitucional se fundamenta en las siguientes normas y precedentes de obligatorio cumplimiento:\n\n"

        # Normas constitucionales y decretos básicos
        out += "1. **Constitución Política de Colombia:** Artículos 1, 2, 11, 48, 49 y 86.\n"
        out += "2. **Decreto 2591 de 1991:**\n"
        out += "   * **Artículo 7:** Facultad cautelar para ordenar medidas provisionales de protección inmediata.\n"
        out += "   * **Artículo 20:** Presunción de veracidad ante el silencio o informe extemporáneo de la accionada.\n"
        out += "   * **Artículo 41:** Prohibición expresa de alegar falta de desarrollo legal para dilatar la protección.\n"
        out += "   * **Artículo 42:** Procedencia de la tutela contra entidades particulares prestadoras de servicios de salud.\n"
        out += "3. **Ley Estatutaria de Salud (Ley 1751 de 2015):** Consagra la salud como derecho fundamental autónomo e irrenunciable regido por los principios de pro homine, continuidad, oportunidad e integralidad.\n\n"

        # Citas y extractos recuperados dinámicamente por Legal RAG (Tool 2)
        if legal_sources:
            out += "#### Precedentes y Extractos Jurisprudenciales Citables:\n\n"
            for src in legal_sources:
                doc_title = src.get("title", src.get("doc_id", "Precedente Constitucional"))
                extract = src.get("text", "")[:350].strip()
                chunk_id = src.get("chunk_id", "")
                out += f"> *\"{extract}...\"*\n"
                out += f"> — **Fuente:** {doc_title} (Identificador: `{chunk_id}`).\n\n"
        else:
            out += "#### Jurisprudencia Constitucional Aplicable:\n"
            out += "* **Sentencia T-760 de 2008:** Regla de acceso a servicios de salud no cubiertos por el plan de beneficios cuando no pueden ser sustituidos y la persona carece de recursos.\n"
            out += "* **Sentencia SU-1219 de 2001:** Obligación de suministrar transporte y viáticos cuando la ausencia del servicio imposibilita el tratamiento médico.\n"
            out += "* **Sentencia SC-132 de 2018:** Carácter vinculante y sanción por desacato frente al incumplimiento de órdenes judiciales.\n\n"

        return out

    def build_prayers(
        self,
        action_type: str,
        subject: str,
        eps_name: str,
        patient_name: str,
        prescription_item: str = "medicamentos y tecnologías ordenadas",
        acting_as: str = "propio"
    ) -> str:
        """Estructura las pretensiones procesales claras, concretas y perentorias."""
        is_agente = (acting_as == "agente_oficioso")
        out = "### VI. PRETENSIONES\n\n"
        out += "Con fundamento en los hechos y consideraciones jurídicas expuestas, respetuosamente solicito al señor Juez:\n\n"

        if action_type == "INCIDENTE_DESACATO":
            out += f"**PRIMERA:** Abrir formalmente **TRÁMITE INCIDENTAL DE DESACATO** en contra del representante legal de **{eps_name}** por el incumplimiento contumaz de la orden judicial.\n\n"
            out += f"**SEGUNDA:** Requerir al superior jerárquico del funcionario responsable para que ordene cumplir el fallo en el término perentorio de 48 horas (Art. 27 Decreto 2591 de 1991).\n\n"
            out += f"**TERCERA:** Si persiste el desacato, imponer las sanciones de arresto y multa previstas en el Artículo 52 del Decreto 2591 de 1991.\n\n"
            return out

        if action_type == "DERECHO_PETICION":
            beneficiario = f"a favor de mi agenciado(a) **{patient_name}**" if is_agente else "al suscrito peticionario"
            out += f"**PRIMERA:** Autorizar y entregar de manera inmediata, en un plazo no mayor a 48 horas, {beneficiario}: **{prescription_item}**.\n\n"
            out += f"**SEGUNDA:** Informar por escrito y de manera clara, de fondo y precisa las razones que motivaron la demora o negación del servicio.\n\n"
            out += f"**TERCERA:** Garantizar la continuidad integral del tratamiento sin imponer trámites administrativos dilatorios al usuario.\n\n"
            return out

        # Pretensiones estándar de Tutela
        if is_agente:
            out += f"**PRIMERA (AMPARO):** TUTELAR y AMPARAR de manera inmediata los derechos fundamentales a la **SALUD**, a la **VIDA EN CONDICIONES DIGNAS**, a la **INTEGRIDAD FÍSICA** y a la **SEGURIDAD SOCIAL** de mi agenciado(a) **{patient_name}**.\n\n"
            out += f"**SEGUNDA (ENTREGA INMEDIATA):** ORDENAR a **{eps_name}** que dentro de las **CUARENTA Y OCHO (48) HORAS** siguientes a la notificación del fallo, proceda a autorizar, gestionar y entregar efectivamente a mi agenciado(a) **{patient_name}**: **{prescription_item}**, sin exigir copagos ni trámites administrativos dilatorios.\n\n"
            out += f"**TERCERA (TRATAMIENTO INTEGRAL):** ORDENAR a **{eps_name}** garantizar el **TRATAMIENTO INTEGRAL** derivado de la patología de mi agenciado(a), incluyendo todas las consultas con especialistas, exámenes de diagnóstico, medicamentos, procedimientos quirúrgicos, insumos y terapias que el médico tratante prescriba, sin que deba acudir a nuevas acciones de tutela.\n\n"
            out += f"**CUARTA (PROHIBICIÓN DE BARRERAS ADMINISTRATIVAS):** ORDENAR a la entidad accionada abstenerse de trasladar barreras burocráticas o trámites internos (tales como comités o falta de convenios) a mi agenciado(a) o a este agente oficioso.\n\n"
        else:
            out += f"**PRIMERA (AMPARO):** TUTELAR y AMPARAR de manera inmediata mis derechos fundamentales a la **SALUD**, a la **VIDA EN CONDICIONES DIGNAS**, a la **INTEGRIDAD FÍSICA** y a la **SEGURIDAD SOCIAL**.\n\n"
            out += f"**SEGUNDA (ENTREGA INMEDIATA):** ORDENAR a **{eps_name}** que dentro de las **CUARENTA Y OCHO (48) HORAS** siguientes a la notificación del fallo, proceda a autorizar, gestionar y entregar efectivamente al suscrito accionante **{patient_name}**: **{prescription_item}**, sin exigir copagos ni trámites administrativos adicionales.\n\n"
            out += f"**TERCERA (TRATAMIENTO INTEGRAL):** ORDENAR a **{eps_name}** garantizar el **TRATAMIENTO INTEGRAL** derivado de mi patología, incluyendo todas las citas con especialistas, exámenes de diagnóstico, medicamentos comerciales o genéricos, procedimientos quirúrgicos, hospitalizaciones, insumos y terapias que el médico tratante prescriba en adelante, sin que deba acudir a nuevas acciones de tutela.\n\n"
            out += f"**CUARTA (PROHIBICIÓN DE BARRERAS ADMINISTRATIVAS):** ORDENAR a la entidad accionada abstenerse de trasladar cargas administrativas internas (tales como aprobaciones de comités técnicos Mipres o falta de convenios de red) a mi persona.\n\n"
        return out

    def build_evidence(
        self,
        document_analyses: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """Capítulo de pruebas documentales aportadas y solicitadas."""
        out = "### VII. PRUEBAS APORTADAS Y SOLICITADAS\n\n"
        out += "Ruego al Despacho decretar, tener en cuenta y valorar como pruebas las siguientes:\n\n"

        if document_analyses:
            out += "**1. Documentales Aportadas en Anexo Digital:**\n"
            for i, doc in enumerate(document_analyses, 1):
                tipo = doc.get("document_description", doc.get("document_type", "Documento"))
                fname = doc.get("file_info", {}).get("file_name", f"Anexo_{i}")
                out += f"   * **Anexo {i}:** Copia digital de {tipo} (`{fname}`).\n"
            out += "\n"
        else:
            out += "**1. Documentales Aportadas:**\n"
            out += "   * Copia de documento de identidad del accionante.\n"
            out += "   * Copia de la fórmula y orden médica expedida por el médico tratante.\n"
            out += "   * Copia del resumen de historia clínica / epicrisis.\n"
            out += "   * Constancia de radicación previa o negación expedida por la EPS.\n\n"

        out += "**2. Pruebas que se solicitan de oficio:**\n"
        out += "   * Se oficie a la entidad accionada para que remita copia íntegra del expediente de auditoría médica y autorizaciones del paciente, bajo apercibimiento del Artículo 20 del Decreto 2591 de 1991.\n\n"
        return out

    def build_oath_and_annexes(
        self,
        action_type: str,
        patient_name: str,
        patient_id: str,
        phone: str = "[TELÉFONO DE CONTACTO]",
        email: str = "[CORREO ELECTRÓNICO]",
        address: str = "[DIRECCIÓN RESIDENCIAL]",
        eps_email: str = "notificacionesjudiciales@eps.com",
        acting_as: str = "propio",
        representative_name: Optional[str] = None,
        representative_id: Optional[str] = None
    ) -> str:
        """Capítulo de juramento de no duplicidad (Art. 37 Dec. 2591/91) y notificaciones."""
        is_agente = (acting_as == "agente_oficioso" and representative_name)
        out = ""
        if action_type in ["ACCION_TUTELA", "TUTELA_CON_MEDIDA_PROVISIONAL"]:
            out += "### VIII. JURAMENTO DE NO DUPLICIDAD\n\n"
            if is_agente:
                out += "Bajo la gravedad del juramento manifiesto a usted, señor Juez, que ni mi agenciado(a) ni el suscrito agente oficioso hemos interpuesto otra acción de tutela ante ninguna autoridad judicial por los mismos hechos y derechos aquí reclamados, dando estricto cumplimiento al **Artículo 37 del Decreto 2591 de 1991**.\n\n"
            else:
                out += "Bajo la gravedad del juramento manifiesto a usted, señor Juez, que no he interpuesto otra acción de tutela ante ninguna autoridad judicial por los mismos hechos y derechos aquí reclamados, dando estricto cumplimiento al **Artículo 37 del Decreto 2591 de 1991**.\n\n"

        out += "### IX. NOTIFICACIONES Y DATOS DE CONTACTO\n\n"
        if is_agente:
            out += f"**PARTE ACCIONANTE (AGENTE OFICIOSO / APODERADO):**\n"
            out += f"* **Agente Oficioso:** {representative_name}\n"
            out += f"* **Identificación Agente:** CC No. {representative_id or '[DOCUMENTO AGENTE]'}\n"
            out += f"* **En favor de (Agenciado):** {patient_name} (Documento No. {patient_id})\n"
            out += f"* **Dirección de Notificación:** {address}\n"
            out += f"* **Teléfono de Contacto:** {phone}\n"
            out += f"* **Correo Electrónico:** {email} *(Autorizo expresamente la notificación electrónica conforme a la Ley 2213 de 2022)*.\n\n"
        else:
            out += f"**PARTE ACCIONANTE:**\n"
            out += f"* **Nombre:** {patient_name}\n"
            out += f"* **Identificación:** CC {patient_id}\n"
            out += f"* **Dirección:** {address}\n"
            out += f"* **Teléfono Celular:** {phone}\n"
            out += f"* **Correo Electrónico:** {email} *(Autorizo expresamente la notificación electrónica conforme a la Ley 2213 de 2022)*.\n\n"

        out += f"**PARTE ACCIONADA:**\n"
        out += f"* En el buzón oficial de notificaciones judiciales de la entidad: `{eps_email}` o en su sede administrativa principal.\n\n"

        out += "Del señor Juez,\n\n"
        out += f"Atentamente,\n\n"
        out += f"_____________________________________\n"
        if is_agente:
            out += f"**{representative_name}**\n"
            out += f"C.C. No. {representative_id or '[DOCUMENTO AGENTE]'}\n"
            out += f"Agente Oficioso de **{patient_name}** (C.C. No. {patient_id})\n"
        else:
            out += f"**{patient_name}**\n"
            out += f"C.C. No. {patient_id}\n"
        return out

    def _mes_espanol(self, mes_num: int) -> str:
        meses = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
        return meses[max(0, min(11, mes_num - 1))]

    def generate_petition(
        self,
        case_data: Dict[str, Any],
        legal_sources: Optional[List[Dict[str, Any]]] = None,
        document_analyses: Optional[List[Dict[str, Any]]] = None,
        template_type_hint: Optional[str] = None,
        export_docx: bool = False,
        output_docx_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Punto de entrada principal para ensamblar el memorial completo y retornar el payload para Hermes.
        """
        # 1. Resolución de variables básicas
        patient_name = case_data.get("patient_name") or "MARÍA ELENA PÉREZ GÓMEZ"
        patient_id = case_data.get("patient_id") or "52.458.912"
        eps_name = case_data.get("eps_name") or "EPS SANITAS"
        city = case_data.get("city") or "Bogotá D.C."
        phone = case_data.get("phone") or "310 123 4567"
        email = case_data.get("email") or "usuario@ampara.org"
        address = case_data.get("address") or "Calle 45 No. 14-22"

        # Resolución de representación procesal (título propio vs agente oficioso/abogado)
        rep_info = case_data.get("representation", {})
        if isinstance(rep_info, str):
            rep_type_raw = rep_info
            rep_name = None
            rep_id = None
        elif isinstance(rep_info, dict):
            rep_type_raw = rep_info.get("type") or rep_info.get("representation_type")
            rep_name = rep_info.get("agent_name") or rep_info.get("lawyer_name")
            rep_id = rep_info.get("agent_id") or rep_info.get("lawyer_id")
        else:
            rep_type_raw = None
            rep_name = None
            rep_id = None

        acting_as_raw = (
            case_data.get("acting_as") or
            case_data.get("representation_type") or
            rep_type_raw or
            "PROPIO"
        )
        if str(acting_as_raw).upper() in ["AGENTE_OFICIOSO", "AGENCIA_OFICIOSA", "THIRD_PERSON"]:
            acting_as = "agente_oficioso"
        elif str(acting_as_raw).upper() in ["REPRESENTANTE_LEGAL", "LEGAL_REPRESENTATIVE"]:
            acting_as = "representante_legal"
        else:
            acting_as = "propio"

        representative_name = (
            case_data.get("representative_name") or
            case_data.get("lawyer_name") or
            case_data.get("agent_name") or
            rep_name
        )
        representative_id = (
            case_data.get("representative_id") or
            case_data.get("lawyer_id") or
            case_data.get("agent_id") or
            rep_id
        )

        # 2. Identificación de acción procesal y materia fáctica
        action_type = self.detect_action_type(case_data, user_specified=template_type_hint)
        subject_matter = self.detect_subject_matter(case_data)

        # 3. Extracción de ítems prescritos del Document Analyzer si existen
        prescribed_item = "medicamentos y tecnologías en salud prescritos"
        if document_analyses:
            items_found = []
            for doc in document_analyses:
                items = doc.get("extracted_entities", {}).get("prescribed_items", [])
                if items:
                    items_found.extend(items)
            if items_found:
                prescribed_item = ", ".join(items_found[:3])
        elif case_data.get("prescription_item"):
            prescribed_item = str(case_data["prescription_item"])

        header = self.build_header(
            action_type=action_type,
            city=city,
            patient_name=patient_name,
            eps_name=eps_name,
            acting_as=acting_as,
            representative_name=representative_name
        )
        parties = self.build_identification_parties(
            patient_name=patient_name,
            patient_id=patient_id,
            eps_name=eps_name,
            acting_as=acting_as,
            representative_name=representative_name,
            representative_id=representative_id,
            city=city
        )
        provisional = self.build_provisional_measure_section(
            action_type=action_type,
            subject=subject_matter,
            patient_name=patient_name,
            eps_name=eps_name,
            prescription_item=prescribed_item,
            acting_as=acting_as
        )
        facts = self.build_facts(
            case_data=case_data,
            document_analyses=document_analyses,
            acting_as=acting_as
        )
        rights = self.build_rights_violated()
        legal_basis = self.build_legal_basis(subject=subject_matter, legal_sources=legal_sources)
        prayers = self.build_prayers(
            action_type=action_type,
            subject=subject_matter,
            eps_name=eps_name,
            patient_name=patient_name,
            prescription_item=prescribed_item,
            acting_as=acting_as
        )
        evidence = self.build_evidence(document_analyses=document_analyses)
        oath_notif = self.build_oath_and_annexes(
            action_type=action_type,
            patient_name=patient_name,
            patient_id=patient_id,
            phone=phone,
            email=email,
            address=address,
            acting_as=acting_as,
            representative_name=representative_name,
            representative_id=representative_id
        )

        # 5. Concatenación final del memorial
        sections = [header, parties]
        if provisional:
            sections.append(provisional)
        sections.extend([facts, rights, legal_basis, prayers, evidence, oath_notif])

        full_document = "\n".join(sections)
        word_count = len(full_document.split())

        # 6. Preparación de fuentes S4 de Hermes
        s4_sources = []
        if legal_sources:
            for s in legal_sources:
                s4_sources.append({
                    "id": s.get("chunk_id", s.get("doc_id", "DOC")),
                    "ref": s.get("title", s.get("doc_id", "Fuente Jurídica"))
                })

        docx_path = None
        docx_generated = False
        if export_docx:
            docx_path = self.export_to_docx(
                document_markdown=full_document,
                output_path=output_docx_path,
                case_data=case_data,
                action_type=action_type
            )
            docx_generated = True

        result = {
            "status": "success",
            "action_type": action_type,
            "subject_matter": subject_matter,
            "document_title": f"{action_type.replace('_', ' ')} - {patient_name} vs {eps_name}",
            "generated_draft_markdown": full_document,
            "metadata": {
                "word_count": word_count,
                "sections_count": len(sections),
                "estimated_pages": max(1, round(word_count / 350, 1)),
                "has_provisional_measures": (action_type == "TUTELA_CON_MEDIDA_PROVISIONAL"),
                "human_review_required": True,  # Regla de oro de Hermes HITL
                "docx_generated": docx_generated,
                "created_at": datetime.now().isoformat()
            },
            "sources_for_s4": s4_sources
        }

        if docx_path:
            result["docx_path"] = docx_path
            result["docx_file_path"] = docx_path

        return result

    def export_to_docx(
        self,
        document_markdown: str,
        output_path: Optional[str] = None,
        case_data: Optional[Dict[str, Any]] = None,
        action_type: str = "TUTELA"
    ) -> str:
        """
        Exporta el memorial procesal en formato Microsoft Word (.docx)
        cumpliendo con los estándares de presentación judicial en Colombia:
        - Márgenes estándar de 2.54 cm (1 pulgada).
        - Tipografía Arial 11-12 pt, interlineado 1.15 y texto justificado.
        - Encabezados procesales destacados en negrilla y color institucional.
        - Soporte completo para formato markdown (**negrita**, listas y secciones).
        - Bloque final de firma procesal y radicación.
        """
        if not DOCX_AVAILABLE:
            raise ImportError(
                "El paquete 'python-docx' es requerido para exportar a Word. "
                "Instálalo con 'pip install python-docx'."
            )

        doc = docx.Document()

        # 1. Configuración de márgenes estándar (2.54 cm / 1 pulgada)
        for sec in doc.sections:
            sec.top_margin = Inches(1.0)
            sec.bottom_margin = Inches(1.0)
            sec.left_margin = Inches(1.0)
            sec.right_margin = Inches(1.0)
            # Pie de página con pie procesal
            footer = sec.footer
            footer_p = footer.paragraphs[0]
            footer_p.text = "Expediente Digital - Agente AMPARA | Asistente Jurídico en Salud y Tutela"
            footer_p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            if footer_p.runs:
                footer_p.runs[0].font.name = "Arial"
                footer_p.runs[0].font.size = Pt(8.5)
                footer_p.runs[0].font.color.rgb = RGBColor(128, 128, 128)

        # 2. Configuración de estilo normal
        style = doc.styles["Normal"]
        style.font.name = "Arial"
        style.font.size = Pt(11)
        style.font.color.rgb = RGBColor(30, 30, 30)
        style.paragraph_format.line_spacing = 1.15
        style.paragraph_format.space_after = Pt(5)

        # 3. Procesamiento línea por línea del markdown
        lines = document_markdown.split("\n")
        in_signature = False

        for line in lines:
            stripped = line.strip()

            # Separadores de sección (---)
            if stripped == "---":
                continue

            # Líneas vacías
            if not stripped:
                continue

            # Título principal (# ...)
            if stripped.startswith("# "):
                text = stripped[2:].strip()
                h = doc.add_paragraph()
                h.alignment = WD_ALIGN_PARAGRAPH.CENTER
                h.paragraph_format.space_before = Pt(12)
                h.paragraph_format.space_after = Pt(8)
                run = h.add_run(text)
                run.bold = True
                run.font.name = "Arial"
                run.font.size = Pt(13)
                run.font.color.rgb = RGBColor(15, 32, 67)  # Azul oscuro institucional
                continue

            # Títulos de sección (## ...)
            if stripped.startswith("## "):
                text = stripped[3:].strip()
                h = doc.add_paragraph()
                h.alignment = WD_ALIGN_PARAGRAPH.LEFT
                h.paragraph_format.space_before = Pt(14)
                h.paragraph_format.space_after = Pt(4)
                run = h.add_run(text)
                run.bold = True
                run.font.name = "Arial"
                run.font.size = Pt(11.5)
                run.font.color.rgb = RGBColor(15, 32, 67)
                continue

            # Subtítulos (### ...)
            if stripped.startswith("### "):
                text = stripped[4:].strip()
                h = doc.add_paragraph()
                h.alignment = WD_ALIGN_PARAGRAPH.LEFT
                h.paragraph_format.space_before = Pt(8)
                h.paragraph_format.space_after = Pt(3)
                run = h.add_run(text)
                run.bold = True
                run.font.name = "Arial"
                run.font.size = Pt(11)
                run.font.color.rgb = RGBColor(50, 50, 50)
                continue

            # Elementos de lista (- ... o * ...)
            if stripped.startswith("- ") or stripped.startswith("* "):
                item_text = stripped[2:].strip()
                p = doc.add_paragraph(style="List Bullet")
                p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                p.paragraph_format.space_after = Pt(3)
                self._add_formatted_runs(p, item_text)
                continue

            # Elementos numerados (1. ... 2. ...)
            m_num = re.match(r"^(\d+[\.\)])\s+(.*)$", stripped)
            if m_num:
                num_prefix = m_num.group(1)
                item_text = m_num.group(2)
                p = doc.add_paragraph()
                p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                p.paragraph_format.space_after = Pt(4)
                p.paragraph_format.left_indent = Inches(0.25)
                run_num = p.add_run(f"{num_prefix} ")
                run_num.bold = True
                self._add_formatted_runs(p, item_text)
                continue

            # Párrafos regulares justificados
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            p.paragraph_format.space_after = Pt(5)
            self._add_formatted_runs(p, stripped)

        # 4. Determinación de ruta de salida
        if not output_path:
            patient_id = "EXP"
            if case_data:
                patient_id = case_data.get("patient_id", case_data.get("case_id", "EXP"))
            safe_id = re.sub(r"[^\w\-]", "_", str(patient_id))
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            target_dir = Path("tutelas_generadas")
            target_dir.mkdir(parents=True, exist_ok=True)
            output_path = str(target_dir / f"memorial_{safe_id}_{action_type}_{ts}.docx")
        else:
            p_out = Path(output_path)
            p_out.parent.mkdir(parents=True, exist_ok=True)
            output_path = str(p_out)

        doc.save(output_path)
        return os.path.abspath(output_path)

    def _add_formatted_runs(self, paragraph, text: str) -> None:
        """Parsea tokens de negrita markdown (**texto**) y agrega runs formateados."""
        # Dividir por delimitador de negrita **
        parts = re.split(r"(\*\*.*?\*\*)", text)
        for part in parts:
            if not part:
                continue
            if part.startswith("**") and part.endswith("**") and len(part) >= 4:
                bold_text = part[2:-2]
                r = paragraph.add_run(bold_text)
                r.bold = True
                r.font.name = "Arial"
                r.font.size = Pt(11)
            else:
                r = paragraph.add_run(part)
                r.font.name = "Arial"
                r.font.size = Pt(11)


# =====================================================================
# FUNCIONES OFICIALES PARA HERMES: draft_template_engine y export_petition_to_docx
# =====================================================================

def draft_template_engine(
    case_data: Dict[str, Any],
    legal_sources: Optional[List[Dict[str, Any]]] = None,
    document_analyses: Optional[List[Dict[str, Any]]] = None,
    template_type: Optional[str] = None,
    export_docx: bool = False,
    output_docx_path: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Función de nivel superior registrada como Tool 4 en Hermes.
    Ensambla memoriales procesales completos para cualquier tipología de tutela en salud
    y permite opcionalmente exportar a Word (.docx).
    """
    engine = PetitionGeneratorEngine()
    # Permitir activación de exportación vía kwargs
    if "export_format" in kwargs and kwargs["export_format"] == "docx":
        export_docx = True

    return engine.generate_petition(
        case_data=case_data,
        legal_sources=legal_sources,
        document_analyses=document_analyses,
        template_type_hint=template_type,
        export_docx=export_docx,
        output_docx_path=output_docx_path
    )


def export_petition_to_docx(
    document_markdown: str,
    output_path: Optional[str] = None,
    case_data: Optional[Dict[str, Any]] = None,
    action_type: str = "TUTELA"
) -> str:
    """
    Función independiente para exportar cualquier memorial procesal markdown
    directamente a un archivo Word (.docx) formalmente maquetado.
    """
    engine = PetitionGeneratorEngine()
    return engine.export_to_docx(
        document_markdown=document_markdown,
        output_path=output_path,
        case_data=case_data,
        action_type=action_type
    )
