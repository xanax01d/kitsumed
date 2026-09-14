"""
Locales package for Migrebot.
"""

from locales.i18n import (
    SUPPORTED_LANGUAGES,
    DEFAULT_LANGUAGE,
    normalize_lang,
    get_text,
    get_location_map,
    get_pain_type_map,
    get_symptoms_map,
    get_medication_map,
    get_intensity_label,
)

__all__ = [
    "SUPPORTED_LANGUAGES",
    "DEFAULT_LANGUAGE",
    "normalize_lang",
    "get_text",
    "get_location_map",
    "get_pain_type_map",
    "get_symptoms_map",
    "get_medication_map",
    "get_intensity_label",
]
