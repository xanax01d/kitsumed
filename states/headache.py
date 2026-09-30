from aiogram.fsm.state import State, StatesGroup

class HeadacheLogSG(StatesGroup):
    start_time = State()         # When the headache started (presets or manual)
    custom_start_time = State()  # Text input for custom start time
    intensity = State()          # 1-10 pain score
    location = State()           # Side / area of head
    pain_type = State()          # Character of pain (throbbing, pressing, etc.)
    symptoms = State()           # Multi-select symptoms (nausea, aura, etc.)
    medication = State()         # Medication choice
    custom_medication = State()  # Text input for custom medication
    medication_time = State()    # When medication was taken after start of pain
    medication_relief = State()  # Did medication help or not (helped, partially, not_helped)
    relief_time = State()        # How long after medication did pain stop
    confirm = State()            # Final summary confirmation
