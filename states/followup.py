from aiogram.fsm.state import State, StatesGroup

class FollowUpSG(StatesGroup):
    custom_end_time = State()
