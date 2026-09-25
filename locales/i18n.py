"""
i18n Localization Engine for Migrebot.
Supports 'ru' (Russian), 'en' (English), and 'meme' (Runet Memes).
"""

from typing import Dict, Any, Optional

from locales import ru, en, meme

SUPPORTED_LANGUAGES = {
    "ru": "🇷🇺 Русский",
    "en": "🇬🇧 English",
    "meme": "🎭 Мемный (Рунет)",
}

DEFAULT_LANGUAGE = "ru"

_MODULES = {
    "ru": ru,
    "en": en,
    "meme": meme,
}


def normalize_lang(lang: Optional[str]) -> str:
    if not lang:
        return DEFAULT_LANGUAGE
    cleaned = str(lang).strip().lower()
    if cleaned in SUPPORTED_LANGUAGES:
        return cleaned
    # Prefix matches or fallback
    if cleaned.startswith("en"):
        return "en"
    if "mem" in cleaned:
        return "meme"
    return DEFAULT_LANGUAGE


def get_text(key: str, lang: str = DEFAULT_LANGUAGE, **kwargs: Any) -> str:
    """Fetches localized string by key with keyword formatting and fallback to Russian."""
    lang_code = normalize_lang(lang)
    mod = _MODULES.get(lang_code, ru)
    tmpl = mod.MESSAGES.get(key)
    if tmpl is None:
        tmpl = ru.MESSAGES.get(key, f"[{key}]")

    if kwargs:
        try:
            return tmpl.format(**kwargs)
        except Exception:
            return tmpl
    return tmpl


def get_location_map(lang: str = DEFAULT_LANGUAGE) -> Dict[str, str]:
    lang_code = normalize_lang(lang)
    mod = _MODULES.get(lang_code, ru)
    return getattr(mod, "LOCATION_MAP", ru.LOCATION_MAP)


def get_pain_type_map(lang: str = DEFAULT_LANGUAGE) -> Dict[str, str]:
    lang_code = normalize_lang(lang)
    mod = _MODULES.get(lang_code, ru)
    return getattr(mod, "PAIN_TYPE_MAP", ru.PAIN_TYPE_MAP)


def get_symptoms_map(lang: str = DEFAULT_LANGUAGE) -> Dict[str, str]:
    lang_code = normalize_lang(lang)
    mod = _MODULES.get(lang_code, ru)
    return getattr(mod, "SYMPTOMS_MAP", ru.SYMPTOMS_MAP)


def get_medication_map(lang: str = DEFAULT_LANGUAGE) -> Dict[str, str]:
    lang_code = normalize_lang(lang)
    mod = _MODULES.get(lang_code, ru)
    return getattr(mod, "MEDICATION_MAP", ru.MEDICATION_MAP)


def get_intensity_label(val: int, lang: str = DEFAULT_LANGUAGE) -> str:
    lang_code = normalize_lang(lang)
    if val <= 3:
        return get_text("intensity_mild", lang_code)
    elif val <= 6:
        return get_text("intensity_moderate", lang_code)
    elif val <= 8:
        return get_text("intensity_severe", lang_code)
    else:
        return get_text("intensity_unbearable", lang_code)
