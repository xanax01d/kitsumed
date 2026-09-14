"""
English locale dictionary for Migrebot (Clean & Minimalist).
"""

MESSAGES = {
    # Main Menu & General
    "main_menu_title": "Main Menu:",
    "btn_log": "🤕 Log Episode",
    "btn_status": "⏹ Did Pain Pass?",
    "btn_history": "📊 My Episodes",
    "btn_export": "📥 Export Report",
    "btn_reminder": "⏰ Reminders",
    "btn_language": "🌐 Language",
    "btn_help": "ℹ️ Help",

    # Start & Help
    "start_welcome": (
        "<b>Migrebot</b> — headache and migraine diary.\n\n"
        "Tap <b>«🤕 Log Episode»</b> to record pain."
    ),
    "help_text": (
        "<b>Bot commands:</b>\n\n"
        "• <b>/log</b> — record an episode\n"
        "• <b>/status</b> — check if headache has passed\n"
        "• <b>/export</b> — download report (PDF / CSV)\n"
        "• <b>/reminder</b> — configure daily check-in\n"
        "• <b>/language</b> — switch interface language\n"
        "• <b>/cancel</b> — abort current action"
    ),

    # History
    "history_empty": "No headache records saved yet.",
    "history_title": "<b>Episode History:</b>\n\n",
    "history_card_status_completed": "Completed",
    "history_card_status_active": "Active",
    "history_card_status_not_resolved": "Not Resolved",
    "history_card_header": "Episode #{id} ({status})",
    "history_card_time": "• Time: <code>{time}</code>\n",
    "history_card_pain": "• Pain: <b>{intensity}/10</b> ({level})\n",
    "history_card_loc": "• Location: {loc} | {pt}\n",
    "history_card_sym": "• Symptoms: {sym}\n",
    "history_card_triggers": "• Triggers: {triggers}\n",
    "history_card_med": "• Medication: {med}",

    # Headache Log Steps
    "step_1_title": "<b>When did the pain start?</b>",
    "step_2_title": "<b>Pain Intensity (1–10)</b>\nStarted: <code>{time_str}</code>",
    "step_3_title": "<b>Pain Localization</b>\nPain: <b>{intensity}/10</b> ({level})",
    "step_4_title": "<b>Pain Type</b>\nLocation: <b>{loc_text}</b>",
    "step_5_title": "<b>Associated Symptoms</b>\nType: <b>{pt_text}</b>",
    "step_triggers_title": "<b>What triggered the episode?</b>\nSelect potential triggers or type your own:",
    "custom_trigger_prompt": "<b>Trigger / Provoking factor</b>\nEnter what might have triggered the pain (e.g. <i>skipped lunch, bright screen, weather</i>):",
    "btn_custom_trigger": "✍️ Custom trigger",
    "btn_no_triggers": "❌ No clear trigger",
    "step_6_title": "<b>Medication Taken</b>\nEnter drug name and dosage or select an option below:",
    "med_time_question": "<b>When did you take the medication ({medication}) relative to headache onset?</b>",
    "relief_time_question": "<b>How long after taking the pill did the pain completely subside?</b>",

    # Intensity labels
    "intensity_mild": "Mild",
    "intensity_moderate": "Moderate",
    "intensity_severe": "Severe",
    "intensity_unbearable": "Unbearable",

    # Summary
    "summary_title": "<b>Episode Summary</b>\n\n",
    "summary_time": "• Time: <code>{start_time}</code>\n",
    "summary_time_resolved": "• Time: <code>{start_time} → {end_time}</code> ({duration})\n",
    "summary_status_completed": "• Status: 🟢 Resolved (pain subsided)\n",
    "summary_status_active": "• Status: 🔴 Active (episode ongoing)\n",
    "summary_pain": "• Pain: <b>{intensity}/10</b> ({level})\n",
    "summary_location": "• Location: {loc_text}\n",
    "summary_pain_type": "• Type: {pt_text}\n",
    "summary_symptoms": "• Symptoms: {symptoms_str}\n",
    "summary_triggers": "• Triggers: {triggers_str}\n",
    "summary_medication": "• Medication: {med_text}\n\n",
    "summary_confirm": "Save this episode?",

    # Calendar
    "calendar_title": "<b>Headache Calendar</b> — {month_name} {year}\n\n🔴 Headache days: <b>{pain_days}</b>\n🟢 Pain-free days: <b>{healthy_days}</b>\n\n<i>Tap a day to view details:</i>",
    "calendar_btn_today": "📅 Current month",
    "calendar_day_healthy": "<b>{date_str}</b> — pain-free day 🟢\n\nNo headache episodes recorded.",
    "calendar_day_episodes_title": "<b>Episodes on {date_str}</b> (total: {count}):\n\n",
    "calendar_future_alert": "This day is in the future.",
    "calendar_btn_back": "⬅️ Back to calendar",

    # Navigation & Action Buttons
    "btn_cancel": "❌ Cancel",
    "btn_back": "⬅️ Back",
    "btn_save": "✅ Save",
    "btn_edit": "🔄 Edit",
    "action_cancelled": "Action cancelled.",
    "no_active_action": "No active action.",
    "saved_success": "<b>Episode saved</b> (#{episode_id})\n\nThe bot will automatically check in on you later.",
    "saved_completed_success": "<b>Episode recorded and resolved</b> (#{episode_id})\n\n🟢 Duration: <code>{duration}</code>.\nGlad you are feeling better!",

    # Follow-up Flow (Pain resolution & Medication efficacy)
    "fu_no_active": "No active episode to check.",
    "fu_pain_question": "<b>Has the headache passed?</b>",
    "fu_btn_passed": "✅ Yes, it passed",
    "fu_btn_not_passed": "❌ No, still hurts",
    "fu_when_question": "<b>When did the pain stop?</b>",
    "fu_when_now": "Just now",
    "fu_when_30m": "30 minutes ago",
    "fu_when_1h": "1 hour ago",
    "fu_when_2h": "2 hours ago",
    "fu_when_custom": "Enter time",
    "fu_when_custom_prompt": "<b>End Time</b>\nEnter time (e.g., <code>18:30</code> or <code>30 min ago</code>):",
    "fu_pain_resolved_recorded": "<b>Pain marked as resolved.</b>\nEnded at: <code>{end_time}</code>.",
    "fu_pain_not_resolved_recorded": "<b>Recorded: pain has not passed yet.</b>\nEpisode updated in your diary.",

    # Medication Relief Question
    "fu_med_question": "<b>Did the medication ({medication}) help?</b>",
    "fu_med_helped": "✅ Helped",
    "fu_med_partially": "⚡️ Partially",
    "fu_med_not_helped": "❌ Did not help",
    "fu_med_recorded": "Medication efficacy recorded.",

    # Reminders
    "reminder_title": (
        "<b>Daily Check-in</b>\n\n"
        "• Status: <b>{status_str}</b>\n"
        "• Time: <b>{reminder_time}</b>\n"
        "• Timezone: {tz_label} (current {local_time})"
    ),
    "reminder_status_enabled": "Enabled",
    "reminder_status_disabled": "Disabled",
    "reminder_daily_prompt": "<b>Did you have a headache today?</b>",
    "reminder_healthy_saved": "Logged: headache-free day.",
    "reminder_custom_time_prompt": "<b>Check-in Time</b>\nEnter time in <code>HH:MM</code> format (e.g., <code>20:30</code>):",
    "reminder_custom_time_invalid": "<b>Invalid time format</b>\nPlease enter time in <code>HH:MM</code> format (e.g., <code>21:30</code>):",
    "reminder_custom_time_saved": "Check-in time set to <b>{time}</b> ({tz_label}).",

    # Timezones
    "tz_menu_title": (
        "<b>Timezone</b>\n\n"
        "• Zone: <b>{tz_label}</b>\n"
        "• Local time: <b>{local_time}</b>"
    ),
    "tz_custom_prompt": "<b>Timezone</b>\nEnter offset or city (e.g. <code>UTC+5</code>, <code>+4</code> or <code>America/New_York</code>):",
    "tz_custom_invalid": "<b>Timezone not recognized</b>\nPlease enter offset (e.g. <code>UTC+4</code>) or IANA name (<code>Europe/London</code>):",
    "tz_custom_saved": "Timezone saved: <b>{tz_label}</b> (current {local_time})",

    # Export
    "export_empty": "No episodes in the diary to export.",
    "export_title": "<b>Export Diary</b> ({count} episodes)\n\nChoose file format:",
    "export_btn_pdf": "📄 Report (PDF)",
    "export_btn_csv": "📊 Spreadsheet (CSV)",
    "export_btn_both": "📦 Both formats",
    "export_caption_csv": "<b>Export Data (CSV)</b>\n\n• Episodes: <b>{count}</b>\n• Date: <code>{date}</code>",
    "export_caption_pdf": "<b>Medical Report (PDF)</b>\n\n• Episodes: <b>{count}</b>\n• Date: <code>{date}</code>",

    # Language Switcher
    "lang_menu_title": "<b>Language Selection</b>\n\nChoose your preferred language:",
    "lang_changed": "Language changed to <b>English</b> 🇬🇧",
}

LOCATION_MAP = {
    "left": "👈 Left side (unilateral)",
    "right": "Right side (unilateral) 👉",
    "both": "↔️ Both sides",
    "forehead_temples": "🎯 Forehead & temples",
    "back_head": "🔙 Back of head & neck",
    "diffuse": "🌐 Whole head (diffuse)",
    # Granular aliases
    "forehead": "Forehead",
    "temple_right": "Right temple",
    "temple_left": "Left temple",
    "temple_both": "Both temples",
    "one_half": "Hemilateral (half head)",
    "all_head": "Whole head",
    "crown": "Top of head (vertex)",
    "eyes": "Ocular / Eye area",
    "neck": "Neck & Skull base",
}

PAIN_TYPE_MAP = {
    "throbbing": "💓 Throbbing / Pulsating",
    "pulsating": "💓 Throbbing / Pulsating",
    "pressing": "🗜 Pressing / Tightening",
    "stabbing": "🎯 Stabbing / Sharp",
    "dull": "🌧 Dull ache",
    "bursting": "💥 Bursting / Explosive",
    "burning": "Burning",
}

SYMPTOMS_MAP = {
    "nausea": "Nausea",
    "vomiting": "Vomiting",
    "photophobia": "Light sensitivity",
    "phonophobia": "Sound sensitivity",
    "aura": "Visual aura",
    "dizziness": "Dizziness",
    "odor": "Smell sensitivity",
    "osmophobia": "Smell sensitivity",
    "none": "No associated symptoms",
}

MEDICATION_MAP = {
    "none": "None taken",
    "triptan": "Sumatriptan / Triptans",
    "nsaid": "Ibuprofen / NSAIDs",
    "paracetamol": "Paracetamol",
    "analgesic": "Analgesics / Spasmalgon",
    "citramon": "Citramon / Caffeine combo",
}

TRIGGERS_MAP = {
    "stress": "Stress / Fatigue",
    "sleep": "Lack of sleep",
    "oversleep": "Oversleeping / Too much sleep",
    "weather": "Weather / Pressure change",
    "food": "Hunger / Skipped meal",
    "alcohol": "Alcohol",
    "caffeine": "Caffeine",
    "sensory": "Noise / Bright light / Smells",
    "physical": "Physical exertion",
    "none": "No clear trigger",
}

