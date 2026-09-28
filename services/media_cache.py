import hashlib
import json
import logging
from pathlib import Path
from typing import Optional, Union, Any
from aiogram.types import FSInputFile, InputMediaPhoto, Message

logger = logging.getLogger(__name__)

CACHE_FILE = Path(__file__).parent.parent / "assets" / "image_cache.json"
ASSETS_DIR = Path(__file__).parent.parent / "assets" / "images"

# In-memory storage for telegram photo file_ids
_FILE_ID_CACHE: dict[str, Any] = {}


def get_localized_asset(rel_path: str, lang: str = "ru") -> Path:
    """
    Returns path to localized asset if available (e.g. 'steps/pain_scale.png' with lang='en'
    looks in 'en/steps/pain_scale.png', then falls back to 'ru/steps/pain_scale.png').
    """
    loc = "en" if lang == "en" else "ru"
    target = ASSETS_DIR / loc / rel_path
    if target.is_file():
        return target
    fallback = ASSETS_DIR / "ru" / rel_path
    return fallback


def _compute_file_hash(p: Path) -> Optional[str]:
    """Computes MD5 hash of an image file if it exists on disk."""
    try:
        if not p.is_file():
            return None
        h = hashlib.md5()
        with open(p, "rb") as f:
            while chunk := f.read(65536):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return None


def _get_keys(image_path: Union[Path, str]) -> list[str]:
    """
    Generates candidate keys for cache lookup.
    Prioritizes specific relative path under ASSETS_DIR (e.g. 'ru/steps/pain_scale.png'
    vs 'en/steps/pain_scale.png'). Does NOT use bare filename if the path is inside ASSETS_DIR
    to avoid cross-language cache collisions!
    """
    p = Path(image_path)
    keys: list[str] = []
    is_under_assets = False
    try:
        resolved_p = p.resolve()
        resolved_assets = ASSETS_DIR.resolve()
        if resolved_assets in resolved_p.parents or p.is_relative_to(ASSETS_DIR):
            rel = str(p.relative_to(ASSETS_DIR))
            keys.append(rel)
            is_under_assets = True
    except Exception:
        pass

    keys.append(str(p))
    if not is_under_assets:
        keys.append(p.name)
    return keys


def load_media_cache() -> None:
    """Loads cached file_ids from disk into memory."""
    global _FILE_ID_CACHE
    if CACHE_FILE.is_file():
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    _FILE_ID_CACHE.update(data)
                    logger.info(f"Loaded {len(_FILE_ID_CACHE)} cached media file_ids from {CACHE_FILE.name}")
        except Exception as e:
            logger.warning(f"Could not load media cache from {CACHE_FILE}: {e}")


def save_media_cache() -> None:
    """Persists memory cache to disk."""
    try:
        CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(_FILE_ID_CACHE, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.warning(f"Could not save media cache to {CACHE_FILE}: {e}")


def get_cached_file_id(image_path: Union[Path, str]) -> Optional[str]:
    """
    Retrieves telegram file_id if cached and file hash is unchanged.
    Invalidates stale cache if the local image file was modified.
    """
    p = Path(image_path)
    current_hash = _compute_file_hash(p)
    keys = _get_keys(image_path)
    for k in keys:
        if k in _FILE_ID_CACHE:
            val = _FILE_ID_CACHE[k]
            if isinstance(val, dict):
                fid = val.get("file_id")
                cached_hash = val.get("hash")
                if current_hash is not None and cached_hash is not None:
                    if current_hash != cached_hash:
                        logger.info(f"Media cache hash mismatch for {k}, invalidating.")
                        del _FILE_ID_CACHE[k]
                        save_media_cache()
                        continue
                return fid
            elif isinstance(val, str):
                if current_hash is not None:
                    logger.info(f"Invalidating legacy unhashed cache entry for {k}")
                    del _FILE_ID_CACHE[k]
                    save_media_cache()
                    continue
                return val
    return None


def record_photo_file_id(image_path: Union[Path, str], file_id: str) -> None:
    """Stores file_id and file hash for given image path and persists cache."""
    if not isinstance(file_id, str) or not file_id.strip():
        return
    p = Path(image_path)
    file_hash = _compute_file_hash(p)
    updated = False
    for k in _get_keys(image_path):
        entry = {"file_id": file_id, "hash": file_hash}
        if _FILE_ID_CACHE.get(k) != entry:
            _FILE_ID_CACHE[k] = entry
            updated = True
    if updated:
        save_media_cache()
        logger.info(f"Cached file_id for {p.name}: {file_id[:16]}...")


def extract_and_record(image_path: Union[Path, str], result: Any) -> None:
    """Extracts photo file_id from aiogram Message result and caches it."""
    if hasattr(result, "photo") and result.photo and isinstance(result.photo, list):
        highest_res = result.photo[-1]
        fid = getattr(highest_res, "file_id", None)
        if isinstance(fid, str) and fid.strip():
            record_photo_file_id(image_path, fid)


def get_input_media(image_path: Union[Path, str], caption: str) -> InputMediaPhoto:
    """
    Returns InputMediaPhoto using cached file_id (string) for lightning-fast payload,
    or falls back to FSInputFile if not yet cached.
    """
    cached_id = get_cached_file_id(image_path)
    if cached_id:
        return InputMediaPhoto(media=cached_id, caption=caption)
    return InputMediaPhoto(media=FSInputFile(str(image_path)), caption=caption)


def get_photo_source(image_path: Union[Path, str]) -> Union[str, FSInputFile]:
    """
    Returns cached file_id string or FSInputFile for use in answer_photo(photo=...).
    """
    cached_id = get_cached_file_id(image_path)
    if cached_id:
        return cached_id
    return FSInputFile(str(image_path))


# Auto-load cache on module import
load_media_cache()
