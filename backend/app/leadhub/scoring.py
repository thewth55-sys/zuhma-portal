"""Motor de propensidad configurable por cliente.

Una config (JSON, por tenant) define: preguntas con puntaje, penalizaciones, campos
informativos, puntaje máximo, bandas y el mapeo etapa→evento de conversión. `evaluate`
calcula el score y la banda a partir de las respuestas. Determinista y sin efectos.

NEXTCORE_CONFIG es la config de referencia (del documento del cliente). Otros clientes
tendrán la suya; por eso vive como dato, no como código.
"""

from __future__ import annotations

from typing import Any

# --- Config de referencia: Nextcore (máx 18) -------------------------------- #
# NOTA: los rangos de "tamaño de proyecto/empresa" en el documento original tenían
# un typo; aquí se usan buckets no solapados por Nº de usuarios. Confirmar con el cliente.
NEXTCORE_CONFIG: dict[str, Any] = {
    "name": "Nextcore — B2B IT / Microsoft",
    "max_score": 18,
    "questions": [
        {
            "key": "tamano_proyecto", "label": "Tamaño del proyecto (usuarios)",
            "type": "select", "section": "calificacion", "weight": 3,
            "options": [
                {"value": "gt100", "label": "+100", "points": 3},
                {"value": "80_100", "label": "80–100", "points": 2},
                {"value": "lt80", "label": "<80", "points": 1},
            ],
        },
        {
            "key": "tiempo_adquisicion", "label": "Tiempo estimado de adquisición",
            "type": "select", "section": "calificacion", "weight": 3,
            "options": [
                {"value": "este_trimestre", "label": "Este trimestre", "points": 3},
                {"value": "proximo_trimestre", "label": "Próximo trimestre", "points": 2},
                {"value": "indefinido", "label": "Indefinido", "points": 1},
            ],
        },
        {
            "key": "presupuesto", "label": "¿Tiene presupuesto autorizado?",
            "type": "select", "section": "calificacion", "weight": 3,
            "options": [
                {"value": "si", "label": "Sí", "points": 3},
                {"value": "no", "label": "No", "points": 0},
            ],
        },
        {
            "key": "quien_decide", "label": "¿Quién toma la decisión?",
            "type": "select", "section": "calificacion", "weight": 3,
            "options": [
                {"value": "individual", "label": "Individual", "points": 3},
                {"value": "comite", "label": "En comité", "points": 2},
                {"value": "no_influye", "label": "No influye", "points": 1},
            ],
        },
        {
            "key": "es_renovacion", "label": "¿Es una renovación?",
            "type": "select", "section": "calificacion", "weight": 2,
            "options": [
                {"value": "no", "label": "No", "points": 2},
                {"value": "si", "label": "Sí", "points": 0},
            ],
        },
        {
            "key": "tamano_empresa", "label": "Tamaño de la empresa (empleados)",
            "type": "select", "section": "calificacion", "weight": 2,
            "options": [
                {"value": "gt150", "label": "+150", "points": 3},
                {"value": "80_150", "label": "80–150", "points": 2},
                {"value": "lt80", "label": "<80", "points": 1},
            ],
        },
        {
            "key": "tienen_partner", "label": "¿Tienen partner?",
            "type": "select", "section": "calificacion", "weight": 2,
            "options": [
                {"value": "no", "label": "No", "points": 2},
                {"value": "si", "label": "Sí", "points": 0},
            ],
        },
    ],
    "penalties": [
        {
            "key": "sector", "label": "Sector (penalización)", "type": "multi", "section": "calificacion",
            "options": [
                {"value": "revendedor", "label": "Revendedor", "points": -2},
                {"value": "gobierno", "label": "Gobierno", "points": -2},
                {"value": "educacion", "label": "Educación", "points": -2},
            ],
        },
    ],
    "info_fields": [
        {"key": "cantidad_usuarios", "label": "Cantidad de usuarios", "type": "number", "section": "requerimiento"},
        {"key": "esquema", "label": "Esquema de adquisición", "type": "select", "section": "requerimiento",
         "options": [{"value": "anual", "label": "Anual"}, {"value": "mensual", "label": "Mensual"}]},
        {"key": "microsoft", "label": "Cuenta con productos Microsoft", "type": "boolean", "section": "requerimiento"},
    ],
    "bands": [
        {"band": "alta", "min": 16, "label": "Alta"},
        {"band": "media", "min": 10, "label": "Media"},
        {"band": "baja", "min": 0, "label": "Baja"},
    ],
    # status del lead → evento de conversión a disparar
    "stage_events": {
        "potential": {"event": "QualifiedLead", "destination": "both", "value": 0},
    },
}


def band_for(config: dict, score: int) -> str:
    bands = sorted(config.get("bands", []), key=lambda b: b["min"], reverse=True)
    for b in bands:
        if score >= b["min"]:
            return b["band"]
    return bands[-1]["band"] if bands else "baja"


def evaluate(config: dict, answers: dict) -> tuple[int, str]:
    """Devuelve (score, banda) a partir de las respuestas y la config del tenant."""
    score = 0

    for q in config.get("questions", []):
        val = answers.get(q["key"])
        for opt in q.get("options", []):
            if opt["value"] == val:
                pts = int(opt.get("points", 0))
                # Cap por factor: la contribución no excede el peso máximo del factor.
                # (Resuelve inconsistencias de la escala del documento y fija el máx total.)
                weight = q.get("weight")
                if weight is not None:
                    pts = min(pts, int(weight))
                score += pts
                break

    for pen in config.get("penalties", []):
        val = answers.get(pen["key"])
        selected = val if isinstance(val, list) else ([val] if val else [])
        for opt in pen.get("options", []):
            if opt["value"] in selected:
                score += int(opt.get("points", 0))

    return score, band_for(config, score)


def get_config_for(tenant_slug: str | None) -> dict:
    """Config por defecto cuando el tenant no tiene una guardada. Hoy todos heredan
    la de Nextcore como base; se personaliza guardando LeadConfig por tenant."""
    return NEXTCORE_CONFIG
