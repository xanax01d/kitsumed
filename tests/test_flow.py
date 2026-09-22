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
    get_confirm_keyboard,
    get_cancel_keyboard,
    get_export_keyboard,
    TimeCallback,
    IntensityCallback,
    LocationCallback,
    PainTypeCallback,
    SymptomCallback,
    MedicationCallback,
    ExportCallback,
    NavCallback,
)
from keyboards.main_menu import get_main_menu_keyboard
from states.headache import HeadacheLogSG
from handlers.headache import callback_back, callback_cancel, cmd_cancel
import db.database as db_mod
from main import get_redis_client, get_fsm_storage
from services import generate_csv, generate_pdf


class TestHeadacheFlow(unittest.IsolatedAsyncioTestCase):

    def test_keyboards_structure(self):
        menu = get_main_menu_keyboard()
        self.assertGreaterEqual(len(menu.keyboard), 2)

        self.assertIsNotNone(get_start_time_keyboard())
        self.assertIsNotNone(get_intensity_keyboard())
        self.assertIsNotNone(get_location_keyboard())
        self.assertIsNotNone(get_pain_type_keyboard())
        self.assertIsNotNone(get_confirm_keyboard())
        self.assertIsNotNone(get_export_keyboard())

        kb_empty = get_symptoms_keyboard(set())
        kb_with_sym = get_symptoms_keyboard({"nausea", "aura"})
        self.assertGreater(len(kb_empty.inline_keyboard), 0)
        self.assertGreater(len(kb_with_sym.inline_keyboard), 0)

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

        # 7. Confirmation has both back and cancel
        conf_actions = extract_nav_actions(get_confirm_keyboard())
        self.assertIn("back", conf_actions)
        self.assertIn("cancel", conf_actions)

        # 8. Cancel/text input keyboard has both back and cancel
        cancel_actions = extract_nav_actions(get_cancel_keyboard(show_back=True))
        self.assertIn("back", cancel_actions)
        self.assertIn("cancel", cancel_actions)

    async def test_navigation_back_fsm_transitions(self):
        # Test back button transitions through all FSM steps
        transitions = [
            (HeadacheLogSG.custom_start_time.state, HeadacheLogSG.start_time),
            (HeadacheLogSG.intensity.state, HeadacheLogSG.start_time),
            (HeadacheLogSG.location.state, HeadacheLogSG.intensity),
            (HeadacheLogSG.pain_type.state, HeadacheLogSG.location),
            (HeadacheLogSG.symptoms.state, HeadacheLogSG.pain_type),
            (HeadacheLogSG.medication.state, HeadacheLogSG.symptoms),
            (HeadacheLogSG.confirm.state, HeadacheLogSG.medication),
        ]

        for from_state, expected_to_state in transitions:
            mock_state = AsyncMock()
            mock_state.get_state.return_value = from_state
            mock_state.get_data.return_value = {
                "start_time": "2026-09-13 22:00",
                "intensity": 7,
                "location": "left",
                "pain_type": "throbbing",
                "symptoms": ["nausea"]
            }

            mock_cb = AsyncMock()
            mock_cb.message = AsyncMock()

            await callback_back(mock_cb, mock_state)
            mock_state.set_state.assert_called_with(expected_to_state)
            mock_cb.answer.assert_called()

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


if __name__ == "__main__":
    unittest.main()
