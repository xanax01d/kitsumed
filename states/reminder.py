from aiogram.fsm.state import State, StatesGroup


class ReminderSG(StatesGroup):
    custom_time = State()  # Awaiting manual HH:MM time entry from user
