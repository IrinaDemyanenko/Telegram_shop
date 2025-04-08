from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

cancel_router = Router()  # или добавь его в свой admin_router, если удобно

@cancel_router.message(F.text == "/cancel")
async def cancel_handler(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Действие отменено. Вы вернулись в главное меню.")
