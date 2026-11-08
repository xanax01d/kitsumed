# 🌐 Contributing Localizations to KitsuMed

<p align="center">
  <a href="LOCALIZATION.md"><b>🇷🇺 Русский</b></a> &nbsp;•&nbsp; <a href="LOCALIZATION_be.md"><b>🇧🇾 Беларуская</b></a> &nbsp;•&nbsp; 🇬🇧 <b>English</b>
</p>

We welcome community translations! Whether you want to add a national language (German, Spanish, French, Polish, Ukrainian, etc.) or a fun thematic persona (Fantasy, Sci-Fi, Retro), follow this guide to add your localization to KitsuMed.

---

## 🚀 Quick Start (5 Steps)

1. **Fork the repository** on GitHub: `https://github.com/xanax01d/kitsumed`.
2. **Copy the template or canonical English file**:
   ```bash
   cp locales/en.json locales/<language_code>.json
   # Example: cp locales/en.json locales/de.json
   ```
   *Use the standard 2-letter [ISO 639-1 code](https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes) (e.g., `de`, `es`, `fr`, `pl`, `uk`, `ja`).*

3. **Translate the strings** inside your new `locales/<language_code>.json` file.
4. **Validate your translation** with our validator script:
   ```bash
   python scripts/validate_locale.py locales/<language_code>.json
   ```
5. **Submit a Pull Request** to the `dev` branch!

---

## 📂 File Structure Overview

Each locale file is a single UTF-8 JSON document containing metadata and 6 translation sections:

```json
{
  "meta": {
    "code": "de",
    "name": "🇩🇪 Deutsch"
  },
  "messages": { ... },
  "location_map": { ... },
  "pain_type_map": { ... },
  "symptoms_map": { ... },
  "medication_map": { ... },
  "triggers_map": { ... }
}
```

### 0. `meta` (Locale Metadata)
- `code`: The unique lowercase language identifier matching the file stem (e.g. `"de"`, `"fr"`, `"pl"`).
- `name`: Display title with emoji for the language picker button (e.g. `"🇩🇪 Deutsch"`). KitsuMed dynamically renders this in the `/language` menu without requiring bot recompilation!

### 1. `messages` (UI Strings & Dialogues)
Contains all text prompts, navigation buttons, alerts, and report labels.
- **Variables / Placeholders**: Some strings contain placeholders like `{id}`, `{time}`, `{dur}`, `{count}`. **Do NOT translate variable names inside `{}`**, keep them exact:
  ```json
  "saved_completed_text": "Episode <b>#{id}</b> marked as resolved ({dur})."
  ```
- **Telegram Rich UI (TG-13)**: Strings may include in-message interactive tags:
  - `<tg-button-row>` and `<tg-button type="callback_data" data="...">Button Text</tg-button>`
  - `<blockquote expandable>Collapsible secondary text</blockquote>`
  - Standard HTML formatting: `<b>bold</b>`, `<i>italic</i>`, `<code>code/dosages</code>`.

### 2. `location_map` (Headache Locations)
Maps anatomical regions (e.g. `forehead`, `temples`, `back_of_head`, `left`, `right`, `bilateral`, `diffuse`).

### 3. `pain_type_map` (Pain Character)
Clinical characteristics (e.g. `throbbing`, `pressing`, `stabbing`, `dull`).

### 4. `symptoms_map` (Associated Symptoms)
ICHD-3 migraine criteria (e.g. `nausea`, `vomiting`, `photophobia`, `phonophobia`, `aura`, `dizziness`).

### 5. `medication_map` (Medications)
Default medication presets with standard dosages.

### 6. `triggers_map` (Provoking Triggers)
Common provoking factors (e.g. `stress`, `lack_of_sleep`, `oversleep`, `weather`, `alcohol`, `skip_food`).

---

## 🦊 (Optional) Add a Mascot Hero Banner

Every locale in KitsuMed has its own unique stylized anime fox girl (kitsune) mascot representing the cultural or thematic vibe!

If you want to contribute artwork for your language:
1. Format: **16:9 widescreen horizontal image** (`1376x768` or `1280x720`).
2. Placement: `assets/images/<language_code>/hero_banner.png`.
3. Aesthetic: Cozy, charming anime art style (Kyoto Animation / Makoto Shinkai vibe) featuring a kitsune fox girl with fluffy ears and tail, dressed in an outfit reflecting the culture or setting.
*If a locale does not supply its own banner, the bot automatically falls back to the English banner.*

---

## 🔍 Validation Script

Before submitting your PR, always run:

```bash
# Validate your specific file
python scripts/validate_locale.py locales/<language_code>.json

# Or validate all locales at once
python scripts/validate_locale.py
```

The validator checks:
- Valid JSON syntax.
- Required `meta` block (`code` and `name`).
- All required keys from canonical `en.json` are present.
- No empty translated strings.
- All template placeholder variables (`{id}`, `{time}`, etc.) are preserved.

---

## 🤝 Questions & Support

Feel free to open an Issue or start a Discussion on GitHub if you need clarification on medical terminology or clinical nuance. Thank you for making KitsuMed accessible to people worldwide! 🦊💖
