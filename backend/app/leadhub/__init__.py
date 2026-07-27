"""Cliente del Zuhma Lead Hub.

El Lead Hub (motor de atribución: Lead ID, CAPI, Google offline) AÚN NO EXISTE
(está en fase de diseño). Aquí definimos el CONTRATO de su API y una implementación
`stub` con datos de muestra. Cuando el Lead Hub esté en línea, se implementa
`LiveLeadHub` contra su REST y se cambia `LEADHUB_MODE=live` — sin tocar los routers.
"""

from app.config import get_settings
from app.leadhub.base import LeadHub
from app.leadhub.stub import StubLeadHub

_instance: LeadHub | None = None


def get_leadhub() -> LeadHub:
    global _instance
    if _instance is None:
        s = get_settings()
        if s.leadhub_mode == "live" and s.leadhub_base_url:
            from app.leadhub.live import LiveLeadHub

            _instance = LiveLeadHub(s.leadhub_base_url)
        else:
            _instance = StubLeadHub()
    return _instance


__all__ = ["LeadHub", "get_leadhub"]
