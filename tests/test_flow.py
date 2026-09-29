import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch
import json

from keyboards.headache_kb import (
    get_start_time_keyboard,
    get_intensity_keyboard,
    get_location_keyboard,
    get_pain_type_keyboard,
    get_symptoms_keyboard,
    get_medication_keyboard,
    get_medication_relief_keyboard,
    get_confirm_keyboard,
    get_cancel_keyboard,
    get_export_keyboard,
    TimeCallback,
    IntensityCallback,
    LocationCallback,
    PainTypeCallback,
    SymptomCallback,
    MedicationCallback,
    MedicationReliefCallback,
    ExportCallback,
    NavCallback,
)
from keyboards.main_menu import get_main_menu_keyboard
from keyboards.reminder_kb import (
    get_reminder_settings_keyboard,
    get_reminder_prompt_keyboard,
    get_reminder_custom_cancel_keyboard,
    get_timezone_keyboard,
    get_timezone_cancel_keyboard,
    get_tz_label,
    get_tz_local_time,
    ReminderCallback,
    ReminderPromptCallback,
)
from states.headache import HeadacheLogSG
from states.reminder import ReminderSG
from handlers.headache import (
    callback_back,
    callback_cancel,
    cmd_cancel,
    process_medication_skip,
    process_medication_input,
    process_medication_relief,
    format_summary,
)
from handlers.reminderHandler import (
    TIME_REGEX,
    resolve_timezone,
    process_custom_time_input,
    process_daily_healthy,
    process_daily_headache,
    _format_reminder_text,
    _format_timezone_text,
)
import db.database as db_mod
from main import get_redis_client, get_fsm_storage
from services import generate_csv, generate_pdf


class TestHeadacheFlow(unittest.IsolatedAsyncioTestCase):

    def test_keyboards_structure(self):
        menu = get_main_menu_keyboard()
        self.assertGreaterEqual(len(menu.keyboard), 2)

        for lang in ["ru", "en", "meme", "cyberpunk"]:
            self.assertIsNotNone(get_start_time_keyboard(lang=lang))
            self.assertIsNotNone(get_location_keyboard(lang=lang))
            self.assertIsNotNone(get_pain_type_keyboard(lang=lang))
            self.assertIsNotNone(get_symptoms_keyboard(set(), lang=lang))
            self.assertIsNotNone(get_symptoms_keyboard({"nausea", "aura"}, lang=lang))
            self.assertIsNotNone(get_medication_keyboard(lang=lang))
            self.assertIsNotNone(get_medication_relief_keyboard(lang=lang))
            self.assertIsNotNone(get_confirm_keyboard(lang=lang))
            self.assertIsNotNone(get_export_keyboard(lang=lang))

    def test_callback_packing(self):
        cb_time = TimeCallback(preset="now").pack()
        self.assertTrue(cb_time.startswith("hdt:now"))

        cb_int = IntensityCallback(value=7).pack()
        self.assertIn("7", cb_int)

        cb_loc = LocationCallback(value="left").pack()
        self.assertIn("left", cb_loc)

        cb_pt = PainTypeCallback(value="throbbing").pack()
        self.assertIn("throbbing", cb_pt)

        cb_sym = SymptomCallback(action="toggle", value="nausea").pack()
        self.assertIn("nausea", cb_sym)

        cb_med = MedicationCallback(value="triptan").pack()
        self.assertIn("triptan", cb_med)

        cb_relief = MedicationReliefCallback(value="helped").pack()
        self.assertTrue(cb_relief.startswith("hdmr:helped"))

        cb_exp = ExportCallback(format="pdf").pack()
        self.assertIn("pdf", cb_exp)

    def test_redis_fsm_storage_config(self):
        client = get_redis_client()
        self.assertIsNotNone(client)
        storage = get_fsm_storage(client)
        self.assertIsNotNone(storage)

    def test_postgres_dsn_generation(self):
        with patch.dict("os.environ", {
            "POSTGRES_HOST": "localhost",
            "POSTGRES_PORT": "5432",
            "POSTGRES_USER": "myuser",
            "POSTGRES_PASSWORD": "mypassword",
            "POSTGRES_DB": "mydb"
        }, clear=True):
            dsn = db_mod.get_postgres_dsn()
            self.assertEqual(dsn, "postgresql://myuser:mypassword@localhost:5432/mydb")

    def test_csv_and_pdf_generation(self):
        episodes = [
            {
                "id": 1,
                "start_time": "2026-09-10 14:30",
                "end_time": "2026-09-10 17:00",
                "intensity": 8,
                "location": "left",
                "pain_type": "throbbing",
                "symptoms": ["nausea", "aura"],
                "medication": "triptan",
                "status": "completed"
            }
        ]
        csv_bytes = generate_csv(episodes)
        self.assertGreater(len(csv_bytes), 50)
        self.assertTrue(csv_bytes.startswith(b"\xef\xbb\xbf"))  # UTF-8 BOM

        pdf_bytes = generate_pdf(episodes, user_title="Test User")
        self.assertGreater(len(pdf_bytes), 500)
        self.assertTrue(pdf_bytes.startswith(b"%PDF"))

    async def test_postgres_db_lifecycle_mocked(self):
        mock_conn = AsyncMock()
        mock_conn.fetchrow.side_effect = [
            {"id": 42},  # create_episode
            {             # get_active_episode
                "id": 42,
                "user_id": 12345,
                "start_time": "2026-09-13 21:00",
                "end_time": None,
                "intensity": 8,
                "location": "left",
                "pain_type": "throbbing",
                "symptoms": json.dumps(["nausea", "aura"]),
                "medication": "triptan",
                "status": "active",
                "created_at": None,
            }
        ]
        mock_conn.execute.return_value = "UPDATE 1"
        mock_conn.fetch.side_effect = [
            [
                {
                    "id": 42,
                    "user_id": 12345,
                    "start_time": "2026-09-13 21:00",
                    "end_time": "2026-09-13 23:00",
                    "intensity": 8,
                    "location": "left",
                    "pain_type": "throbbing",
                    "symptoms": ["nausea", "aura"],
                    "medication": "triptan",
                    "status": "completed",
                    "created_at": None,
                }
            ],
            [
                {
                    "id": 42,
                    "user_id": 12345,
                    "start_time": "2026-09-13 21:00",
                    "end_time": "2026-09-13 23:00",
                    "intensity": 8,
                    "location": "left",
                    "pain_type": "throbbing",
                    "symptoms": ["nausea", "aura"],
                    "medication": "triptan",
                    "status": "completed",
                    "created_at": None,
                }
            ]
        ]

        mock_pool = MagicMock()
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn

        with patch.object(db_mod, "_pool", mock_pool):
            # 1. Upsert user
            await db_mod.upsert_user(12345, "tester", "TestUser")
            mock_conn.execute.assert_called()

            # 2. Create episode
            ep_id = await db_mod.create_episode(12345, {
                "start_time": "2026-09-13 21:00",
                "intensity": 8,
                "location": "left",
                "pain_type": "throbbing",
                "symptoms": ["nausea", "aura"],
                "medication": "triptan"
            })
            self.assertEqual(ep_id, 42)

            # 3. Get active episode
            active = await db_mod.get_active_episode(12345)
            self.assertIsNotNone(active)
            self.assertEqual(active["id"], 42)
            self.assertIn("nausea", active["symptoms"])

            # 4. Finish episode
            finished = await db_mod.finish_episode(12345, "2026-09-13 23:00")
            self.assertTrue(finished)

            # 5. Get recent episodes
            recent = await db_mod.get_recent_episodes(12345)
            self.assertEqual(len(recent), 1)
            self.assertEqual(recent[0]["id"], 42)

            # 6. Get all episodes
            all_eps = await db_mod.get_all_episodes(12345)
            self.assertEqual(len(all_eps), 1)
            self.assertEqual(all_eps[0]["id"], 42)

    def test_cjk_and_nickname_export(self):
        episodes = [
            {
                "id": 1,
                "start_time": "2026-09-13 16:33",
                "end_time": "2026-09-13 18:37",
                "intensity": 8,
                "location": "both",
                "pain_type": "dull",
                "symptoms": ["nausea", "aura"],
                "medication": "nsaid",
                "status": "completed"
            }
        ]
        # Test with Japanese Katakana + Telegram nickname
        user_title = "ザカライア (@xanax01d)"
        pdf_bytes = generate_pdf(episodes, user_title=user_title)
        self.assertTrue(pdf_bytes.startswith(b"%PDF"))
        self.assertGreater(len(pdf_bytes), 1000)

        csv_bytes = generate_csv(episodes)
        self.assertTrue(csv_bytes.startswith(b"\xef\xbb\xbf"))
        csv_text = csv_bytes.decode("utf-8-sig")
        self.assertIn("С обеих сторон", csv_text)
        self.assertIn("Тупая / ноющая", csv_text)

    def test_nav_callbacks_packing(self):
        cb_back = NavCallback(action="back").pack()
        self.assertTrue(cb_back.startswith("hdn:back"))

        cb_cancel = NavCallback(action="cancel").pack()
        self.assertTrue(cb_cancel.startswith("hdn:cancel"))

    def test_navigation_buttons_presence_in_keyboards(self):
        def extract_nav_actions(kb):
            actions = set()
            for row in kb.inline_keyboard:
                for btn in row:
                    if btn.callback_data and btn.callback_data.startswith("hdn:"):
                        action = btn.callback_data.split(":")[1]
                        actions.add(action)
            return actions

        # 1. Start time has cancel, no back (first step)
        start_actions = extract_nav_actions(get_start_time_keyboard())
        self.assertIn("cancel", start_actions)
        self.assertNotIn("back", start_actions)

        # 2. Intensity has both back and cancel
        int_actions = extract_nav_actions(get_intensity_keyboard())
        self.assertIn("back", int_actions)
        self.assertIn("cancel", int_actions)

        # 3. Location has both back and cancel
        loc_actions = extract_nav_actions(get_location_keyboard())
        self.assertIn("back", loc_actions)
        self.assertIn("cancel", loc_actions)

        # 4. Pain type has both back and cancel
        pt_actions = extract_nav_actions(get_pain_type_keyboard())
        self.assertIn("back", pt_actions)
        self.assertIn("cancel", pt_actions)

        # 5. Symptoms has both back and cancel
        sym_actions = extract_nav_actions(get_symptoms_keyboard(set()))
        self.assertIn("back", sym_actions)
        self.assertIn("cancel", sym_actions)

        # 6. Medication has both back and cancel
        med_actions = extract_nav_actions(get_medication_keyboard())
        self.assertIn("back", med_actions)
        self.assertIn("cancel", med_actions)

        # 6b. Medication relief has both back and cancel
        medr_actions = extract_nav_actions(get_medication_relief_keyboard())
        self.assertIn("back", medr_actions)
        self.assertIn("cancel", medr_actions)

        # 7. Confirmation has both back and cancel
        conf_actions = extract_nav_actions(get_confirm_keyboard())
        self.assertIn("back", conf_actions)
        self.assertIn("cancel", conf_actions)

        # 8. Cancel/text input keyboard has both back and cancel
        cancel_actions = extract_nav_actions(get_cancel_keyboard(show_back=True))
        self.assertIn("back", cancel_actions)
        self.assertIn("cancel", cancel_actions)

    async def test_navigation_back_fsm_transitions(self):
        # Test back button transitions through all FSM steps (with no medication taken)
        transitions = [
            (HeadacheLogSG.custom_start_time.state, HeadacheLogSG.start_time),
            (HeadacheLogSG.intensity.state, HeadacheLogSG.start_time),
            (HeadacheLogSG.location.state, HeadacheLogSG.intensity),
            (HeadacheLogSG.pain_type.state, HeadacheLogSG.location),
            (HeadacheLogSG.symptoms.state, HeadacheLogSG.pain_type),
            (HeadacheLogSG.medication.state, HeadacheLogSG.symptoms),
            (HeadacheLogSG.confirm.state, HeadacheLogSG.medication),
            (HeadacheLogSG.medication_relief.state, HeadacheLogSG.medication),
        ]

        for from_state, expected_to_state in transitions:
            mock_state = AsyncMock()
            mock_state.get_state.return_value = from_state
            mock_state.get_data.return_value = {
                "start_time": "2026-09-13 22:00",
                "intensity": 7,
                "location": "left",
                "pain_type": "throbbing",
                "symptoms": ["nausea"],
                "medication": "none"
            }

            mock_cb = AsyncMock()
            mock_cb.message = AsyncMock()

            await callback_back(mock_cb, mock_state)
            mock_state.set_state.assert_called_with(expected_to_state)
            mock_cb.answer.assert_called()

        # Test back button from confirm when medication was taken -> goes to medication_relief
        mock_state_med = AsyncMock()
        mock_state_med.get_state.return_value = HeadacheLogSG.confirm.state
        mock_state_med.get_data.return_value = {
            "start_time": "2026-09-13 22:00",
            "medication": "Суматриптан 50мг",
            "medication_relief": "helped"
        }
        mock_cb_med = AsyncMock()
        mock_cb_med.message = AsyncMock()

        await callback_back(mock_cb_med, mock_state_med)
        mock_state_med.set_state.assert_called_with(HeadacheLogSG.medication_relief)

    async def test_cancel_flow_clears_state(self):
        # 1. Callback cancel
        mock_state = AsyncMock()
        mock_cb = AsyncMock()
        mock_cb.message = AsyncMock()

        await callback_cancel(mock_cb, mock_state)
        mock_state.clear.assert_called_once()
        mock_cb.answer.assert_called_once()

        # 2. Text command cancel with active state
        mock_state_cmd = AsyncMock()
        mock_state_cmd.get_state.return_value = HeadacheLogSG.intensity.state
        mock_msg = AsyncMock()

        await cmd_cancel(mock_msg, mock_state_cmd)
        mock_state_cmd.clear.assert_called_once()

    def test_reminder_keyboards_and_callbacks(self):
        # Settings keyboard enabled
        kb_on = get_reminder_settings_keyboard("21:00", enabled=True, current_tz="Europe/Moscow")
        self.assertIsNotNone(kb_on)
        self.assertGreater(len(kb_on.inline_keyboard), 3)

        # Settings keyboard disabled
        kb_off = get_reminder_settings_keyboard("21:00", enabled=False, current_tz="Asia/Yekaterinburg")
        self.assertIsNotNone(kb_off)

        # Timezone selection keyboard
        kb_tz = get_timezone_keyboard("Europe/Moscow")
        self.assertIsNotNone(kb_tz)
        self.assertGreater(len(kb_tz.inline_keyboard), 5)

        kb_tz_cancel = get_timezone_cancel_keyboard()
        self.assertEqual(len(kb_tz_cancel.inline_keyboard), 1)

        # Daily inquiry prompt keyboard
        kb_prompt = get_reminder_prompt_keyboard()
        self.assertEqual(len(kb_prompt.inline_keyboard), 3)

        # Custom time cancel keyboard
        kb_cancel = get_reminder_custom_cancel_keyboard()
        self.assertEqual(len(kb_cancel.inline_keyboard), 1)

        # Packing callbacks
        cb_set = ReminderCallback(action="set_time", value="20:00").pack()
        self.assertTrue(cb_set.startswith("rem|set_time|20:00"))

        cb_tz = ReminderCallback(action="set_tz", value="Europe/Samara").pack()
        self.assertTrue(cb_tz.startswith("rem|set_tz|Europe/Samara"))

        cb_toggle = ReminderCallback(action="toggle").pack()
        self.assertTrue(cb_toggle.startswith("rem|toggle"))

        cb_headache = ReminderPromptCallback(action="headache").pack()
        self.assertTrue(cb_headache.startswith("rem_p|headache"))

        cb_healthy = ReminderPromptCallback(action="healthy").pack()
        self.assertTrue(cb_healthy.startswith("rem_p|healthy"))

    def test_timezone_resolution_and_formatting(self):
        # 1. Direct IANA timezones
        self.assertEqual(resolve_timezone("Europe/Minsk"), "Europe/Minsk")
        self.assertEqual(resolve_timezone("Asia/Yekaterinburg"), "Asia/Yekaterinburg")

        # 2. Case-insensitive preset matching
        self.assertEqual(resolve_timezone("Москва"), "Europe/Moscow")
        self.assertEqual(resolve_timezone("новосибирск"), "Asia/Novosibirsk")
        self.assertEqual(resolve_timezone("Калининград"), "Europe/Kaliningrad")

        # 3. UTC offsets (matching presets where available, falling back to Etc/GMT)
        self.assertEqual(resolve_timezone("UTC+5"), "Asia/Yekaterinburg")
        self.assertEqual(resolve_timezone("+4"), "Europe/Samara")
        self.assertEqual(resolve_timezone("-3"), "Etc/GMT+3")
        self.assertEqual(resolve_timezone("UTC-8"), "Etc/GMT+8")
        self.assertEqual(resolve_timezone("+13"), "Etc/GMT-13")

        # 4. Invalid timezone
        self.assertIsNone(resolve_timezone("not_a_timezone_123"))
        self.assertIsNone(resolve_timezone("+25:00"))

        # 5. Label formatting
        self.assertIn("Москва", get_tz_label("Europe/Moscow"))
        self.assertEqual(get_tz_label("Etc/GMT-4"), "UTC+4")

        # 6. Local time formatting (HH:MM)
        loc_time = get_tz_local_time("Europe/Moscow")
        self.assertEqual(len(loc_time), 5)
        self.assertIn(":", loc_time)

    def test_reminder_custom_time_validation(self):
        valid_times = ["21:00", "09:30", "8:15", "0:00", "23:59", "00:00"]
        for t in valid_times:
            self.assertIsNotNone(TIME_REGEX.match(t), f"Expected {t} to be valid")

        invalid_times = ["24:00", "25:30", "12:60", "abc", "2100", "-1:00", "12:5"]
        for t in invalid_times:
            self.assertIsNone(TIME_REGEX.match(t), f"Expected {t} to be invalid")

    async def test_reminder_db_methods_mocked(self):
        mock_pool = MagicMock()
        mock_conn = AsyncMock()
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn

        with patch.object(db_mod, "_get_pool", return_value=mock_pool):
            # 1. get_user_reminder not found -> default
            mock_conn.fetchrow.return_value = None
            res_def = await db_mod.get_user_reminder(12345)
            self.assertEqual(res_def["reminder_time"], "21:00")
            self.assertEqual(res_def["timezone"], "Europe/Moscow")
            self.assertTrue(res_def["reminder_enabled"])

            # 2. get_user_reminder found
            mock_conn.fetchrow.return_value = {
                "reminder_time": "19:30",
                "reminder_enabled": False,
                "timezone": "Asia/Yekaterinburg",
                "last_reminded_date": "2026-09-13"
            }
            res = await db_mod.get_user_reminder(12345)
            self.assertEqual(res["reminder_time"], "19:30")
            self.assertEqual(res["timezone"], "Asia/Yekaterinburg")
            self.assertFalse(res["reminder_enabled"])

            # 3. set_user_reminder
            mock_conn.execute.return_value = "UPDATE 1"
            upd = await db_mod.set_user_reminder(12345, reminder_time="20:00", timezone="Europe/Samara", enabled=True)
            self.assertTrue(upd)

            # 4. get_users_due_for_reminder
            mock_conn.fetch.return_value = [
                {"user_id": 111, "first_name": "Anna", "username": "anna", "reminder_time": "21:00", "timezone": "Europe/Moscow"}
            ]
            due = await db_mod.get_users_due_for_reminder("21:00", "2026-09-13")
            self.assertEqual(len(due), 1)
            self.assertEqual(due[0]["user_id"], 111)

            # 5. get_enabled_reminder_users
            mock_conn.fetch.return_value = [
                {"user_id": 111, "first_name": "Anna", "username": "anna", "reminder_time": "21:00", "timezone": "Europe/Moscow", "last_reminded_date": None}
            ]
            enabled_users = await db_mod.get_enabled_reminder_users()
            self.assertEqual(len(enabled_users), 1)

            # 6. mark_user_reminded
            mock_conn.execute.return_value = "UPDATE 1"
            marked = await db_mod.mark_user_reminded(111, "2026-09-13")
            self.assertTrue(marked)

    async def test_reminder_prompt_callbacks(self):
        # 1. Healthy response
        mock_cb = AsyncMock()
        mock_cb.message = AsyncMock()
        await process_daily_healthy(mock_cb)
        mock_cb.answer.assert_called_with("Здорово!")

        # 2. Headache response starts HeadacheLogSG.start_time
        mock_cb_h = AsyncMock()
        mock_cb_h.message = AsyncMock()
        mock_state = AsyncMock()
        await process_daily_headache(mock_cb_h, mock_state)
        mock_state.set_state.assert_called_with(HeadacheLogSG.start_time)
        mock_cb_h.answer.assert_called()

    async def test_reminder_scheduler_tick(self):
        import zoneinfo
        from datetime import datetime, timezone
        from services.reminder_service import reminder_scheduler
        mock_bot = AsyncMock()

        now_utc = datetime.now(timezone.utc)
        user_tz = zoneinfo.ZoneInfo("Europe/Moscow")
        user_local_time = now_utc.astimezone(user_tz).strftime("%H:%M")

        calls = 0
        async def fake_sleep(sec):
            nonlocal calls
            calls += 1
            if calls > 1:
                raise asyncio.CancelledError()

        with patch("services.reminder_service.get_enabled_reminder_users", new_callable=AsyncMock) as mock_get_users, \
             patch("services.reminder_service.mark_user_reminded", new_callable=AsyncMock) as mock_mark, \
             patch("asyncio.sleep", side_effect=fake_sleep):
            mock_get_users.return_value = [
                {
                    "user_id": 999,
                    "first_name": "TestUser",
                    "reminder_time": user_local_time,
                    "timezone": "Europe/Moscow",
                    "last_reminded_date": None,
                }
            ]
            await reminder_scheduler(mock_bot)
            mock_bot.send_message.assert_called_once()
            mock_mark.assert_called_once()

    def test_media_cache_functions(self):
        from pathlib import Path
        import services.media_cache as mc
        from aiogram.types import PhotoSize, FSInputFile

        # Backup existing cache
        orig_cache = dict(mc._FILE_ID_CACHE)
        try:
            with patch.object(mc, "save_media_cache"):
                test_path = Path("/tmp/test_img.png")
                mc.record_photo_file_id(test_path, "test_file_id_12345")

                self.assertEqual(mc.get_cached_file_id(test_path), "test_file_id_12345")
                self.assertEqual(mc.get_photo_source(test_path), "test_file_id_12345")

                input_media = mc.get_input_media(test_path, caption="test caption")
                self.assertEqual(input_media.media, "test_file_id_12345")
                self.assertEqual(input_media.caption, "test caption")

                # Test fallback for unknown file
                unknown_path = Path("/tmp/unknown_img.png")
                self.assertIsNone(mc.get_cached_file_id(unknown_path))
                self.assertIsInstance(mc.get_photo_source(unknown_path), FSInputFile)

                # Test hash invalidation and no-collision
                import tempfile
                with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tf:
                    tf.write(b"original_image_bytes")
                    temp_p = Path(tf.name)
                try:
                    mc.record_photo_file_id(temp_p, "file_id_version_1")
                    self.assertEqual(mc.get_cached_file_id(temp_p), "file_id_version_1")

                    # Modify the file content on disk
                    with open(temp_p, "wb") as f:
                        f.write(b"modified_new_design_image_bytes")

                    # Hash mismatch must invalidate cached file_id and return None
                    self.assertIsNone(mc.get_cached_file_id(temp_p))

                    # Test cross-locale collision prevention
                    ru_path = mc.ASSETS_DIR / "ru" / "steps" / "pain_scale.png"
                    en_path = mc.ASSETS_DIR / "en" / "steps" / "pain_scale.png"
                    mc.record_photo_file_id(ru_path, "ru_file_id_abc")
                    # en_path must not resolve to ru_file_id_abc
                    self.assertNotEqual(mc.get_cached_file_id(en_path), "ru_file_id_abc")
                finally:
                    if temp_p.exists():
                        temp_p.unlink()
        finally:
            mc._FILE_ID_CACHE = orig_cache

    def test_i18n_locales_and_mappings(self):
        from locales import (
            get_text,
            get_intensity_label,
            get_location_map,
            get_pain_type_map,
            get_symptoms_map,
            get_medication_map,
            SUPPORTED_LANGUAGES,
        )

        self.assertIn("ru", SUPPORTED_LANGUAGES)
        self.assertIn("en", SUPPORTED_LANGUAGES)
        self.assertIn("meme", SUPPORTED_LANGUAGES)
        self.assertIn("cyberpunk", SUPPORTED_LANGUAGES)

        # Test Russian strings
        self.assertIn("Migrebot", get_text("start_welcome", "ru"))
        self.assertEqual(get_intensity_label(2, "ru"), "Слабая")
        self.assertEqual(get_intensity_label(10, "ru"), "Невыносимая")

        # Test English strings
        self.assertIn("Migrebot", get_text("start_welcome", "en"))
        self.assertEqual(get_intensity_label(2, "en"), "Mild")
        self.assertEqual(get_intensity_label(10, "en"), "Unbearable")
        self.assertIn("Forehead", get_location_map("en")["forehead"])

        # Test Meme Russian strings (old and new Runet memes)
        meme_welcome = get_text("start_welcome", "meme")
        self.assertTrue("бо-бо" in meme_welcome or "сожрет" in meme_welcome or "суету" in meme_welcome)
        self.assertTrue("фиаско" in get_intensity_label(10, "meme") or "Press F" in get_intensity_label(10, "meme"))
        self.assertIn("facepalm", get_location_map("meme")["forehead"])
        self.assertIn("дедлайн", get_pain_type_map("meme")["pressing"])
        self.assertIn("кринж", get_symptoms_map("meme")["nausea"])
        self.assertIn("артиллерия", get_medication_map("meme")["triptan"])

        # Test Cyberpunk strings
        cp_welcome = get_text("start_welcome", "cyberpunk")
        self.assertTrue("чумба" in cp_welcome or "биомонитор" in cp_welcome or "нейрочип" in cp_welcome)
        self.assertTrue("киберпсихоз" in get_intensity_label(10, "cyberpunk") or "Травма Тим" in get_intensity_label(10, "cyberpunk"))
        self.assertIn("нейропорт", get_location_map("cyberpunk")["forehead"])
        self.assertIn("Черного льда", get_pain_type_map("cyberpunk")["stabbing"])
        self.assertIn("Kiroshi", get_symptoms_map("cyberpunk")["photophobia"])
        self.assertIn("нейроблокатор", get_medication_map("cyberpunk")["triptan"])

        # Test symptom and location coverage across all languages
        for l_code in SUPPORTED_LANGUAGES:
            s_map = get_symptoms_map(l_code)
            self.assertIn("vomiting", s_map, f"vomiting missing from {l_code}")
            self.assertIn("nausea", s_map, f"nausea missing from {l_code}")
            self.assertIn("odor", s_map, f"odor missing from {l_code}")
            self.assertIn("photophobia", s_map, f"photophobia missing from {l_code}")
            self.assertIn("phonophobia", s_map, f"phonophobia missing from {l_code}")
            self.assertIn("aura", s_map, f"aura missing from {l_code}")
            self.assertIn("dizziness", s_map, f"dizziness missing from {l_code}")

            l_map = get_location_map(l_code)
            self.assertIn("left", l_map, f"left missing from {l_code}")
            self.assertIn("right", l_map, f"right missing from {l_code}")
            self.assertIn("both", l_map, f"both missing from {l_code}")
            self.assertIn("forehead_temples", l_map, f"forehead_temples missing from {l_code}")
            self.assertIn("back_head", l_map, f"back_head missing from {l_code}")
            self.assertIn("diffuse", l_map, f"diffuse missing from {l_code}")

            p_map = get_pain_type_map(l_code)
            self.assertIn("throbbing", p_map, f"throbbing missing from {l_code}")
            self.assertIn("pressing", p_map, f"pressing missing from {l_code}")
            self.assertIn("stabbing", p_map, f"stabbing missing from {l_code}")
            self.assertIn("dull", p_map, f"dull missing from {l_code}")
            self.assertIn("bursting", p_map, f"bursting missing from {l_code}")

        # Test fallback to Russian
        self.assertIsNotNone(get_text("unknown_key_xyz", "en"))

    def test_format_episode_card_no_raw_vomiting(self):
        from handlers.startHandler import _format_episode_card
        ep = {
            "id": 6,
            "start_time": "2026-09-13 22:23",
            "end_time": "2026-09-13 22:36",
            "intensity": 10,
            "location": "diffuse",
            "pain_type": "dull",
            "symptoms": ["aura", "phonophobia", "vomiting", "nausea", "photophobia", "dizziness"],
            "medication": "none",
            "status": "completed"
        }
        # Verify Russian
        card_ru = _format_episode_card(ep, lang="ru")
        self.assertNotIn("vomiting", card_ru)
        self.assertIn("Рвота", card_ru)
        self.assertIn("Тошнота", card_ru)

        # Verify English
        card_en = _format_episode_card(ep, lang="en")
        self.assertNotIn("vomiting", card_en)
        self.assertIn("Vomiting", card_en)
        self.assertIn("Nausea", card_en)

        # Verify Meme
        card_meme = _format_episode_card(ep, lang="meme")
        self.assertNotIn("vomiting", card_meme)
        self.assertIn("Рвота (полный тотал)", card_meme)

        # Verify Cyberpunk
        card_cp = _format_episode_card(ep, lang="cyberpunk")
        self.assertNotIn("vomiting", card_cp)
        self.assertIn("Выброс биомассы", card_cp)

    async def test_language_handler_and_switching(self):
        from handlers.languageHandler import cmd_select_language, process_language_choice
        from keyboards.headache_kb import LanguageCallback

        # 1. Test /language command
        mock_msg = AsyncMock()
        mock_msg.from_user = MagicMock()
        mock_msg.from_user.id = 12345
        mock_msg.from_user.username = "testuser"
        mock_msg.from_user.first_name = "Test"

        with patch("handlers.languageHandler.upsert_user", new=AsyncMock()), \
             patch("handlers.languageHandler.get_user_language", new=AsyncMock(return_value="ru")):
            await cmd_select_language(mock_msg)
            mock_msg.answer.assert_called_once()
            args, kwargs = mock_msg.answer.call_args
            self.assertIn("Выбор языка", kwargs["text"])

        # 2. Test language selection callback
        mock_cb = AsyncMock()
        mock_cb.from_user = mock_msg.from_user
        mock_cb.message = AsyncMock()
        cb_data = LanguageCallback(code="meme")

        with patch("handlers.languageHandler.upsert_user", new=AsyncMock()), \
             patch("handlers.languageHandler.set_user_language", new=AsyncMock(return_value=True)):
            await process_language_choice(mock_cb, cb_data)
            mock_cb.answer.assert_called_with("Language: MEME")

    async def test_followup_flow_and_medication_relief(self):
        from handlers.followupHandler import (
            cmd_check_pain_status,
            process_pain_passed,
            process_pain_not_passed,
            process_set_when,
            process_medication_relief,
        )
        from keyboards.headache_kb import FollowUpCallback

        # 1. Test /status or finish check
        mock_msg = AsyncMock()
        mock_msg.from_user = MagicMock()
        mock_msg.from_user.id = 12345
        mock_state = AsyncMock()

        with patch("handlers.followupHandler.get_active_episode", new=AsyncMock(return_value={"id": 42, "user_id": 12345})):
            await cmd_check_pain_status(mock_msg, mock_state)
            mock_msg.answer.assert_called_once()
            args, kwargs = mock_msg.answer.call_args
            self.assertIn("Прошла ли", kwargs["text"])

        # 2. Pain passed -> asks when
        mock_cb = AsyncMock()
        mock_cb.from_user = mock_msg.from_user
        mock_cb.message = AsyncMock()
        cb_passed = FollowUpCallback(action="pain_passed", episode_id=42)
        await process_pain_passed(mock_cb, cb_passed)
        mock_cb.message.edit_text.assert_called_once()
        args, kwargs = mock_cb.message.edit_text.call_args
        self.assertIn("Когда прошла", kwargs["text"])

        # 3. Time selected -> resolves pain & asks medication if taken
        cb_when = FollowUpCallback(action="set_when", episode_id=42, value="-30m")
        mock_ep = {
            "id": 42,
            "user_id": 12345,
            "medication": "Суматриптан 50мг",
            "medication_relief": None,
        }
        with patch("handlers.followupHandler.resolve_episode_pain", new=AsyncMock(return_value=True)) as mock_resolve, \
             patch("handlers.followupHandler.get_episode_by_id", new=AsyncMock(return_value=mock_ep)):
            await process_set_when(mock_cb, cb_when)
            mock_resolve.assert_called_with(42, pain_passed=True, end_time=unittest.mock.ANY)
            args, kwargs = mock_cb.message.edit_text.call_args
            self.assertIn("Помог ли", kwargs["text"])

        # 4. Medication relief recorded -> stores in DB
        mock_cb_med = AsyncMock()
        mock_cb_med.from_user = mock_msg.from_user
        mock_cb_med.message = AsyncMock()
        cb_relief = FollowUpCallback(action="med_relief", episode_id=42, value="helped")
        with patch("handlers.followupHandler.update_medication_relief", new=AsyncMock(return_value=True)) as mock_up_med:
            await process_medication_relief(mock_cb_med, cb_relief)
            mock_up_med.assert_called_with(42, "helped")
            mock_cb_med.answer.assert_called_once()

        # 5. Pain NOT passed -> marks not resolved in DB
        cb_not_passed = FollowUpCallback(action="pain_not_passed", episode_id=42)
        with patch("handlers.followupHandler.resolve_episode_pain", new=AsyncMock(return_value=True)) as mock_resolve_no, \
             patch("handlers.followupHandler.get_episode_by_id", new=AsyncMock(return_value={"id": 42, "medication": "none"})):
            await process_pain_not_passed(mock_cb, cb_not_passed)
            mock_resolve_no.assert_called_with(42, pain_passed=False)

    async def test_followup_scheduler_worker(self):
        from services.followup_service import followup_scheduler
        mock_bot = AsyncMock()

        test_episodes = [
            {
                "id": 99,
                "user_id": 12345,
                "language": "meme",
                "medication": "Ибупрофен",
            }
        ]

        calls = 0
        async def fake_sleep(duration):
            nonlocal calls
            calls += 1
            if calls > 1:
                raise asyncio.CancelledError()

        with patch("services.followup_service.get_pending_followup_episodes", new=AsyncMock(return_value=test_episodes)), \
             patch("services.followup_service.mark_followup_sent", new=AsyncMock(return_value=True)) as mock_sent, \
             patch("asyncio.sleep", side_effect=fake_sleep):
            await followup_scheduler(mock_bot)
            mock_bot.send_message.assert_called_once()
            args, kwargs = mock_bot.send_message.call_args
            self.assertEqual(kwargs["chat_id"], 12345)
            self.assertTrue("отпустила" in kwargs["text"] or "суета" in kwargs["text"])
            mock_sent.assert_called_with(99)

    def test_localized_assets(self):
        from services.media_cache import get_localized_asset, ASSETS_DIR
        from PIL import Image

        required_assets = [
            "hero_banner.png",
            "architecture_diagram.png",
            "flow_diagram.png",
            "db_diagram.png",
            "history.png",
            "export.png",
            "steps/start_time.png",
            "steps/pain_scale.png",
            "steps/location.png",
            "steps/pain_type.png",
            "steps/symptoms.png",
            "steps/medication.png",
            "steps/confirm.png",
            "steps/saved.png",
        ]

        for loc in ["ru", "en"]:
            for asset in required_assets:
                p = ASSETS_DIR / loc / asset
                self.assertTrue(p.is_file(), f"Asset {p} does not exist!")
                self.assertGreater(p.stat().st_size, 1000, f"Asset {p} is empty!")
                with Image.open(p) as img:
                    self.assertEqual(img.size, (1376, 768), f"Asset {p} dimensions != (1376, 768)")

        # Verify get_localized_asset helper
        ru_step = get_localized_asset("steps/pain_scale.png", "ru")
        self.assertEqual(ru_step, ASSETS_DIR / "ru" / "steps" / "pain_scale.png")

        en_step = get_localized_asset("steps/pain_scale.png", "en")
        self.assertEqual(en_step, ASSETS_DIR / "en" / "steps" / "pain_scale.png")

        # Fallback for meme / cyberpunk
        meme_step = get_localized_asset("steps/pain_scale.png", "meme")
        self.assertEqual(meme_step, ASSETS_DIR / "ru" / "steps" / "pain_scale.png")

    async def test_medication_relief_flow_branching(self):
        # 1. When medication is skipped ("none") -> advances directly to HeadacheLogSG.confirm
        state_dict_none = {"lang": "ru"}
        mock_state_none = AsyncMock()
        mock_state_none.get_data.side_effect = lambda: state_dict_none
        async def fake_update_none(**kwargs):
            state_dict_none.update(kwargs)
        mock_state_none.update_data.side_effect = fake_update_none

        mock_cb_none = AsyncMock()
        mock_cb_none.from_user = MagicMock()
        mock_cb_none.from_user.id = 12345
        mock_cb_none.message = AsyncMock()

        cb_none = MedicationCallback(value="none")
        await process_medication_skip(mock_cb_none, cb_none, mock_state_none)

        self.assertEqual(state_dict_none.get("medication"), "none")
        self.assertIsNone(state_dict_none.get("medication_relief"))
        mock_state_none.set_state.assert_called_with(HeadacheLogSG.confirm)

        # 2. When medication is entered as text -> advances to HeadacheLogSG.medication_relief
        state_dict_med = {"lang": "ru"}
        mock_state_med = AsyncMock()
        mock_state_med.get_data.side_effect = lambda: state_dict_med
        async def fake_update_med(**kwargs):
            state_dict_med.update(kwargs)
        mock_state_med.update_data.side_effect = fake_update_med

        mock_msg = AsyncMock()
        mock_msg.from_user = MagicMock()
        mock_msg.from_user.id = 12345
        mock_msg.text = "Суматриптан 50мг"

        await process_medication_input(mock_msg, mock_state_med)

        self.assertEqual(state_dict_med.get("medication"), "Суматриптан 50мг")
        mock_state_med.set_state.assert_called_with(HeadacheLogSG.medication_relief)

        # 3. When medication relief option is selected -> saves relief and advances to HeadacheLogSG.confirm
        mock_cb_relief = AsyncMock()
        mock_cb_relief.from_user = mock_msg.from_user
        mock_cb_relief.message = AsyncMock()

        cb_relief = MedicationReliefCallback(value="helped")
        await process_medication_relief(mock_cb_relief, cb_relief, mock_state_med)

        self.assertEqual(state_dict_med.get("medication_relief"), "helped")
        mock_state_med.set_state.assert_called_with(HeadacheLogSG.confirm)

        # 4. Summary format check with medication relief
        summary = format_summary(state_dict_med, "ru")
        self.assertIn("Суматриптан 50мг", summary)
        self.assertIn("Помогло", summary)


if __name__ == "__main__":
    unittest.main()
