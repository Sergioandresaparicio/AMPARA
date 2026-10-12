"""
Case Tracker - Tool 5 para Hermes (AMPARA)
Módulo: agent/tools/case_tracker.py

Sistema de persistencia relacional en SQLite y monitoreo de expedientes procesales:
- Registro y actualización de expedientes digitales (casos de salud)
- Trazabilidad y línea de tiempo procesal (historial de eventos y estados)
- Cálculo y monitoreo perentorio de términos procesales colombianos:
  * 10 días hábiles para fallo de tutela (Art. 86 CP y Art. 29 Dec. 2591/91)
  * 15 días hábiles para respuesta a Derecho de Petición (Ley 1755 de 2015)
  * 48 horas continuas para cumplimiento de Medida Cautelar Provisional (Art. 7 Dec. 2591/91)
  * 3 días hábiles para interponer recurso de Impugnación de tutela (Art. 31 Dec. 2591/91)
  * 48 horas para requerimiento previo al desacato (Art. 27 Dec. 2591/91)
"""

import os
import json
import sqlite3
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union

DEFAULT_DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "data",
    "ampara_vector.db"
)

VALID_PHASES = [
    "interview",
    "doc_analysis",
    "draft_generated",
    "human_review",
    "filed_in_court",
    "provisional_ordered",
    "ruling_granted",
    "ruling_denied",
    "appeal_filed",
    "compliance_monitoring",
    "contempt_filed",
    "resolved_closed"
]

# Días festivos fijos colombianos estándar para cálculo de días hábiles
COLOMBIAN_FIXED_HOLIDAYS = [
    (1, 1),   # Año Nuevo
    (5, 1),   # Día del Trabajo
    (7, 20),  # Día de la Independencia
    (8, 7),   # Batalla de Boyacá
    (12, 8),  # Inmaculada Concepción
    (12, 25)  # Navidad
]


class CaseTracker:
    """
    Gestor CRUD de base de datos relacional para expedientes y seguimiento de tutelas.
    """

    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        self.db_path = db_path
        self._mem_conn = None
        if db_path == ":memory:":
            self._mem_conn = sqlite3.connect(":memory:")
            self._mem_conn.row_factory = sqlite3.Row
            self._init_tables(self._mem_conn)
        else:
            os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
            with self.get_connection() as conn:
                self._init_tables(conn)

    def get_connection(self) -> sqlite3.Connection:
        if self._mem_conn is not None:
            self._mem_conn.row_factory = sqlite3.Row
            return self._mem_conn
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    @staticmethod
    def _row_to_dict(cursor: sqlite3.Cursor, row: Any) -> Optional[Dict[str, Any]]:
        if row is None:
            return None
        if isinstance(row, sqlite3.Row):
            return dict(row)
        cols = [d[0] for d in cursor.description]
        return dict(zip(cols, row))

    def _init_tables(self, conn: sqlite3.Connection):
        """Inicializa las tablas de casos y eventos procesales si no existen."""
        cursor = conn.cursor()
        # 1. Tabla de expedientes (cases)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cases (
                case_id TEXT PRIMARY KEY,
                patient_name TEXT NOT NULL,
                patient_id TEXT,
                eps_name TEXT NOT NULL,
                case_type TEXT,
                urgency_level TEXT DEFAULT 'Normal',
                phase TEXT DEFAULT 'interview',
                court_filing_number TEXT,
                court_name TEXT,
                filing_date TEXT,
                deadline_date TEXT,
                facts_json TEXT,
                documents_json TEXT,
                metadata_json TEXT,
                created_at TIMESTAMP,
                updated_at TIMESTAMP
            )
        """)

        # Migración segura: agregar columnas faltantes si cases fue creada previamente con esquema reducido
        cursor.execute("PRAGMA table_info(cases)")
        existing_cols = {col[1] for col in cursor.fetchall()}
        cols_to_add = {
            "patient_id": "TEXT",
            "court_filing_number": "TEXT",
            "court_name": "TEXT",
            "filing_date": "TEXT",
            "deadline_date": "TEXT",
            "documents_json": "TEXT",
            "metadata_json": "TEXT"
        }
        for col_name, col_type in cols_to_add.items():
            if col_name not in existing_cols:
                cursor.execute(f"ALTER TABLE cases ADD COLUMN {col_name} {col_type}")


        # 2. Tabla de auditoría / eventos de la línea de tiempo (case_events)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS case_events (
                event_id TEXT PRIMARY KEY,
                case_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                phase_at_event TEXT,
                description TEXT,
                event_data_json TEXT,
                timestamp TIMESTAMP,
                FOREIGN KEY (case_id) REFERENCES cases(case_id)
            )
        """)
        conn.commit()

    # =================================================================
    # OPERACIONES CRUD
    # =================================================================

    def create_case(self, case_data: Dict[str, Any]) -> Dict[str, Any]:
        """Crea un nuevo expediente digital en la base de datos."""
        now_str = datetime.now().isoformat()
        raw_id = case_data.get("case_id")
        if not raw_id:
            year = datetime.now().year
            short_uuid = uuid.uuid4().hex[:6].upper()
            case_id = f"AMP-{year}-{short_uuid}"
        else:
            case_id = raw_id

        patient_name = case_data.get("patient_name", "Sin Nombre")
        patient_id = case_data.get("patient_id", "")
        eps_name = case_data.get("eps_name", "EPS No especificada")
        case_type = case_data.get("case_type", "medicamento")
        urgency_level = case_data.get("urgency_level", "Normal")
        phase = case_data.get("phase", "interview")

        facts_json = json.dumps(case_data.get("facts", []), ensure_ascii=False)
        docs_json = json.dumps(case_data.get("documents", []), ensure_ascii=False)
        meta_json = json.dumps(case_data.get("metadata", {}), ensure_ascii=False)

        filing_date = case_data.get("filing_date")
        court_filing = case_data.get("court_filing_number")
        court_name = case_data.get("court_name")

        # Cálculo automático de fecha límite si hay radicación
        deadline_date = case_data.get("deadline_date")
        if filing_date and not deadline_date:
            deadline_info = self.calculate_legal_deadline(filing_date, action_type=case_type)
            deadline_date = deadline_info.get("deadline_iso")

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO cases (
                    case_id, patient_name, patient_id, eps_name, case_type,
                    urgency_level, phase, court_filing_number, court_name,
                    filing_date, deadline_date, facts_json, documents_json,
                    metadata_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                case_id, patient_name, patient_id, eps_name, case_type,
                urgency_level, phase, court_filing, court_name,
                filing_date, deadline_date, facts_json, docs_json,
                meta_json, now_str, now_str
            ))
            # Evento inicial
            self._log_event(
                conn, case_id, "CASE_CREATED", phase,
                f"Expediente aperturado para {patient_name} contra {eps_name}."
            )
            conn.commit()

        return self.get_case(case_id)

    def get_case(self, case_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene un expediente completo con sus metadatos y cálculo de términos."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM cases WHERE case_id = ?", (case_id,))
            row = cursor.fetchone()
            if not row:
                return None

            c = self._row_to_dict(cursor, row)
            # Deserializar campos JSON
            c["facts"] = json.loads(c["facts_json"]) if c.get("facts_json") else []
            c["documents"] = json.loads(c["documents_json"]) if c.get("documents_json") else []
            c["metadata"] = json.loads(c["metadata_json"]) if c.get("metadata_json") else {}

            # Monitoreo de término legal si tiene fecha límite
            if c.get("deadline_date"):
                c["deadline_monitoring"] = self.check_deadline_status(c["deadline_date"])
            else:
                c["deadline_monitoring"] = None

            return c

    def update_case_phase(
        self,
        case_id: str,
        new_phase: str,
        notes: str = "",
        extra_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Actualiza la fase procesal del caso y registra el hito en la auditoría."""
        if new_phase not in VALID_PHASES:
            raise ValueError(f"Fase no válida: {new_phase}. Válidas: {VALID_PHASES}")

        now_str = datetime.now().isoformat()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE cases
                SET phase = ?, updated_at = ?
                WHERE case_id = ?
            """, (new_phase, now_str, case_id))

            self._log_event(
                conn, case_id, "PHASE_CHANGED", new_phase,
                notes or f"Fase actualizada a: {new_phase}",
                extra_data
            )
            conn.commit()

        return self.get_case(case_id)

    def record_court_filing(
        self,
        case_id: str,
        filing_number: str,
        court_name: str,
        filing_date_str: Optional[str] = None,
        action_type: str = "TUTELA"
    ) -> Dict[str, Any]:
        """Registra la radicación formal ante el juzgado y programa el término perentorio."""
        now_date = filing_date_str or datetime.now().strftime("%Y-%m-%d")
        deadline_info = self.calculate_legal_deadline(now_date, action_type=action_type)
        deadline_iso = deadline_info["deadline_iso"]

        now_str = datetime.now().isoformat()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE cases
                SET court_filing_number = ?, court_name = ?,
                    filing_date = ?, deadline_date = ?,
                    phase = 'filed_in_court', updated_at = ?
                WHERE case_id = ?
            """, (filing_number, court_name, now_date, deadline_iso, now_str, case_id))

            self._log_event(
                conn, case_id, "COURT_FILED", "filed_in_court",
                f"Radicada tutela ante {court_name}. No. Radicado: {filing_number}. Término de fallo vence el {deadline_iso}.",
                deadline_info
            )
            conn.commit()

        return self.get_case(case_id)

    def list_cases(
        self,
        phase: Optional[str] = None,
        urgency: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Lista expedientes con filtros opcionales por fase y nivel de riesgo."""
        query = "SELECT case_id, patient_name, eps_name, case_type, urgency_level, phase, deadline_date, updated_at FROM cases WHERE 1=1"
        params = []
        if phase:
            query += " AND phase = ?"
            params.append(phase)
        if urgency:
            query += " AND urgency_level = ?"
            params.append(urgency)

        query += " ORDER BY updated_at DESC LIMIT ?"
        params.append(limit)

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, tuple(params))
            results = []
            for row in cursor.fetchall():
                c = self._row_to_dict(cursor, row)
                if c.get("deadline_date"):
                    c["deadline_monitoring"] = self.check_deadline_status(c["deadline_date"])
                results.append(c)
            return results

    def get_timeline(self, case_id: str) -> List[Dict[str, Any]]:
        """Recupera la línea de tiempo completa de eventos de un expediente."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM case_events
                WHERE case_id = ?
                ORDER BY timestamp ASC
            """, (case_id,))
            events = []
            for row in cursor.fetchall():
                ev = self._row_to_dict(cursor, row)
                if ev.get("event_data_json"):
                    ev["event_data"] = json.loads(ev["event_data_json"])
                events.append(ev)
            return events

    def _log_event(
        self,
        conn: sqlite3.Connection,
        case_id: str,
        event_type: str,
        phase: str,
        description: str,
        event_data: Optional[Dict[str, Any]] = None
    ):
        cursor = conn.cursor()
        ev_id = f"EV-{uuid.uuid4().hex[:8].upper()}"
        data_json = json.dumps(event_data, ensure_ascii=False) if event_data else None
        cursor.execute("""
            INSERT INTO case_events (
                event_id, case_id, event_type, phase_at_event, description, event_data_json, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (ev_id, case_id, event_type, phase, description, data_json, datetime.now().isoformat()))

    # =================================================================
    # MOTOR DE TÉRMINOS LEGALES COLOMBIANOS
    # =================================================================

    def calculate_legal_deadline(
        self,
        start_date_str: str,
        action_type: str = "TUTELA"
    ) -> Dict[str, Any]:
        """
        Calcula con rigor procesal la fecha de vencimiento según la acción:
        - TUTELA: 10 días hábiles (Art. 86 CP y Art. 29 Dec. 2591/91)
        - DERECHO_PETICION: 15 días hábiles (Ley 1755 de 2015)
        - MEDIDA_PROVISIONAL: 48 horas continuas (Art. 7 Dec. 2591/91)
        - IMPUGNACION: 3 días hábiles (Art. 31 Dec. 2591/91)
        """
        try:
            start_dt = datetime.strptime(start_date_str[:10], "%Y-%m-%d")
        except ValueError:
            start_dt = datetime.now()

        action_norm = action_type.upper()

        if "PROVISIONAL" in action_norm or "MEDIDA" in action_norm:
            # 48 horas continuas
            deadline_dt = start_dt + timedelta(hours=48)
            business_days = 2
            rule = "48 horas continuas (Art. 7 Decreto 2591 de 1991)"
        elif "PETICION" in action_norm:
            # 15 días hábiles
            deadline_dt = self._add_business_days(start_dt, 15)
            business_days = 15
            rule = "15 días hábiles (Ley 1755 de 2015 / Art. 23 C.P.)"
        elif "IMPUGNA" in action_norm:
            # 3 días hábiles
            deadline_dt = self._add_business_days(start_dt, 3)
            business_days = 3
            rule = "3 días hábiles perentorios (Art. 31 Decreto 2591 de 1991)"
        else:
            # Tutela estándar: 10 días hábiles
            deadline_dt = self._add_business_days(start_dt, 10)
            business_days = 10
            rule = "10 días hábiles constitucionales para dictar fallo (Art. 86 C.P. y Art. 29 Dec. 2591/91)"

        return {
            "start_date": start_dt.strftime("%Y-%m-%d"),
            "deadline_date": deadline_dt.strftime("%Y-%m-%d"),
            "deadline_iso": deadline_dt.isoformat(),
            "business_days_allocated": business_days,
            "legal_rule": rule
        }

    def check_deadline_status(self, deadline_str: str) -> Dict[str, Any]:
        """Calcula el estado actual de cumplimiento de un plazo legal."""
        try:
            deadline_dt = datetime.strptime(deadline_str[:10], "%Y-%m-%d")
        except ValueError:
            return {"status": "UNKNOWN", "days_remaining": 0}

        today = datetime.now().date()
        target = deadline_dt.date()
        diff = (target - today).days

        if diff < 0:
            status = "OVERDUE"
            message = f"VENCIDO: El plazo legal expiró hace {abs(diff)} día(s). Procede solicitar impulso o activar desacato."
        elif diff <= 2:
            status = "NEAR_DEADLINE"
            message = f"ALERTA PRÓXIMO A VENCER: Quedan {diff} día(s) para el término judicial."
        else:
            status = "ON_TIME"
            message = f"En término regular. Quedan {diff} día(s) hábiles aproximados."

        return {
            "status": status,
            "days_remaining": diff,
            "message": message,
            "requires_action": (status in ["OVERDUE", "NEAR_DEADLINE"])
        }

    def _add_business_days(self, from_date: datetime, n_days: int) -> datetime:
        """Añade n días hábiles excluyendo fines de semana y festivos fijos colombianos."""
        cur = from_date
        added = 0
        while added < n_days:
            cur += timedelta(days=1)
            # 5 = Sábado, 6 = Domingo
            if cur.weekday() >= 5:
                continue
            # Festivo fijo
            if (cur.month, cur.day) in COLOMBIAN_FIXED_HOLIDAYS:
                continue
            added += 1
        return cur


# =====================================================================
# FUNCIÓN OFICIAL PARA HERMES: case_db_crud
# =====================================================================

_TRACKER_REGISTRY = {}

def get_tracker(db_path: str = DEFAULT_DB_PATH) -> CaseTracker:
    if db_path not in _TRACKER_REGISTRY:
        _TRACKER_REGISTRY[db_path] = CaseTracker(db_path=db_path)
    return _TRACKER_REGISTRY[db_path]

def case_db_crud(
    action: str,
    case_id: Optional[str] = None,
    case_data: Optional[Dict[str, Any]] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Función de nivel superior registrada como Tool 5 en Hermes.
    Acciones soportadas:
    - 'create': Crea expediente (requiere case_data)
    - 'get': Obtiene expediente por case_id
    - 'update_phase': Actualiza fase (requiere case_id, new_phase)
    - 'record_filing': Registra radicación judicial y calcula términos
    - 'list': Lista expedientes (admite filter_phase, filter_urgency)
    - 'timeline': Devuelve historial de eventos
    - 'calculate_deadline': Calcula días hábiles y fecha límite
    """
    db_path = kwargs.get("db_path", DEFAULT_DB_PATH)
    tracker = kwargs.get("tracker") or get_tracker(db_path=db_path)
    action_lower = action.lower()

    if action_lower == "create":
        if not case_data:
            raise ValueError("La acción 'create' requiere 'case_data'")
        res = tracker.create_case(case_data)
        return {"status": "success", "action": "create", "case": res}

    elif action_lower == "get":
        if not case_id:
            raise ValueError("La acción 'get' requiere 'case_id'")
        res = tracker.get_case(case_id)
        if not res:
            return {"status": "not_found", "case_id": case_id}
        return {"status": "success", "action": "get", "case": res}

    elif action_lower == "update_phase":
        if not case_id:
            raise ValueError("La acción 'update_phase' requiere 'case_id'")
        new_phase = kwargs.get("new_phase") or (case_data.get("phase") if case_data else None)
        if not new_phase:
            raise ValueError("Se requiere 'new_phase' para actualizar")
        notes = kwargs.get("notes", "")
        res = tracker.update_case_phase(case_id, new_phase, notes=notes)
        return {"status": "success", "action": "update_phase", "case": res}

    elif action_lower == "record_filing":
        if not case_id:
            raise ValueError("La acción 'record_filing' requiere 'case_id'")
        filing_no = kwargs.get("filing_number") or (case_data.get("court_filing_number") if case_data else "RAD-PENDING")
        court = kwargs.get("court_name") or (case_data.get("court_name") if case_data else "Juzgado Municipal")
        filing_date = kwargs.get("filing_date")
        act_type = kwargs.get("action_type", "TUTELA")
        res = tracker.record_court_filing(case_id, filing_no, court, filing_date_str=filing_date, action_type=act_type)
        return {"status": "success", "action": "record_filing", "case": res}

    elif action_lower == "list":
        phase = kwargs.get("phase") or kwargs.get("filter_phase")
        urgency = kwargs.get("urgency") or kwargs.get("filter_urgency")
        limit = kwargs.get("limit", 50)
        cases = tracker.list_cases(phase=phase, urgency=urgency, limit=limit)
        return {"status": "success", "action": "list", "total": len(cases), "cases": cases}

    elif action_lower == "timeline":
        if not case_id:
            raise ValueError("La acción 'timeline' requiere 'case_id'")
        events = tracker.get_timeline(case_id)
        return {"status": "success", "action": "timeline", "case_id": case_id, "events": events}

    elif action_lower == "calculate_deadline":
        start_date = kwargs.get("start_date", datetime.now().strftime("%Y-%m-%d"))
        act_type = kwargs.get("action_type", "TUTELA")
        dl = tracker.calculate_legal_deadline(start_date, act_type)
        return {"status": "success", "action": "calculate_deadline", "deadline_info": dl}

    else:
        raise ValueError(f"Acción no reconocida en case_db_crud: {action}")
