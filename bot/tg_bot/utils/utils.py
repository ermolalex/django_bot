import secrets
from aiogram.types import Message
from bot.tg_bot.keyboards.kbs import main_keyboard


def get_about_us_text() -> str:
    return """
🌟 ТЕХНИЧЕСКАЯ ПОДДЕРЖКА КИК-СОФТ 🌟

Добро пожаловать!

Для продолжения работы вам нужно нажать кнопку (внизу) "Отправить" и "Поделиться контактом" с нашим ботом поддержки.
Это безопасно. 
"""


#async def greet_user(message: Message, is_new_user: bool) -> None:
async def greet_user(message: Message, is_new_user: bool = True) -> None:

    """
    Приветствует пользователя и отправляет соответствующее сообщение.
    """
    greeting = "Добро пожаловать" if is_new_user else "С возвращением"
    status = "Вы успешно зарегистрированы!" if is_new_user else "Рады видеть вас снова!"
    await message.answer(
        f"{greeting}, <b>Sasa</b>! {status}\n"
        "Чем я могу помочь вам сегодня?",
        # reply_markup=main_keyboard(user_id=message.from_user.id, first_name=message.from_user.first_name)
    )
    # await message.answer(
    #     f"{greeting}, <b>{message.from_user.full_name}</b>! {status}\n"
    #     "Чем я могу помочь вам сегодня?",
    #     reply_markup=main_keyboard(user_id=message.from_user.id, first_name=message.from_user.first_name)
    # )


def make_random_password(length=10, allowed_chars=None):
    if not allowed_chars:
        allowed_chars = 'abcdefghjkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789@#$%&?*(){}[]<>'
    return ''.join(secrets.choice(allowed_chars) for i in range(length))