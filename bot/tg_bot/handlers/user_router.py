import sys
import json
import asyncio
from dataclasses import dataclass
from asgiref.sync import sync_to_async

import django
from django.conf import settings
from django.apps import apps

from starlette.background import BackgroundTask

from aiogram import Router, F
from aiogram.filters import CommandStart, Command, CommandObject
from aiogram.types import User, Message, ReplyKeyboardRemove, ContentType

# from sqlmodel import  Session

from bot.tg_bot.keyboards import kbs
from bot.tg_bot.utils.utils import greet_user, get_about_us_text, make_random_password
from bot.zulip_client import ZulipClient, ZulipException
#from app.models import User, UserBase #, TgUserMessageBase
#from app.bot.utils.rabbit_publisher import RabbitPublisher
# from app.config import settings
# from app.db import DB
from bot.logger import create_logger

import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "conf.settings")
django.setup()
from django.conf import settings
from django.db.utils import IntegrityError
from django.core.exceptions import ValidationError

from profiles.models import Profile, Company
from communications.models import Message

#apps.populate(settings.INSTALLED_APPS)


logger = create_logger(logger_name=__name__)
user_router = Router()

try:
    zulip_client = ZulipClient()
except ZulipException:
    msg = "Фатальная ошибка при попытке коннекта к Zulip-серверу! Бот не запущен!"
    logger.critical(msg)
    sys.exit(msg)


def send_bot_event_msg_to_zulip(text:str, topic='info'):
    zulip_client.send_msg_to_channel(
        channel_name="bot_events",
        topic=topic,
        msg=text
    )


async def get_or_create_user_django(tg_user: User, company: Company) -> (User, bool):
    created = False
    try:
        user = await Profile.objects.aget(tg_id=tg_user.id)
    except Profile.DoesNotExist:
        user = None

    if user:
        return (user, created)

    user = Profile(
        username=f"{tg_user.first_name}_{tg_user.id}",  # тут телефона нету, поэтому id, потом запишем телефон
        first_name=tg_user.first_name,
        last_name=tg_user.last_name or "",
        tg_id=tg_user.id,
        company=company
    )
    password = make_random_password()
    user.set_password(password)

    try:
        await sync_to_async(user.full_clean)()
        await user.asave()
        created = True
    except (IntegrityError, ValidationError) as e:
        logger.error(f"Ошибка при сохранении нового пользователя. Поле не уникально: {e}")
        user = None
    return (user, created)


async def handle_start_command(tg_user: User, company_name: str=""):
    if not company_name:
        company_name = settings.NONAME_CHANNEL_NAME

    msg_text = f"Команда /start от {tg_user.first_name} с ID {tg_user.id}. Компания: {company_name}."
    logger.info(msg_text)
    send_bot_event_msg_to_zulip(f"{msg_text}")  # todo добавить в фоновые задачи (fastapi.BackgroundTask, aiojobs)

    # ищем или создаем компанию в Джанго
    company, created = await Company.objects.aget_or_create(
        channel_name=company_name,
        defaults={'name': company_name}
    )
    if created:
        logger.info(f"Создана компания в Джанго: {company_name}.")

    # проверяем, есть ли канал компании в Zulip
    if not company.channel_id:
        # канал в Zulip еще не создан. Создаем
        channel_id = zulip_client.get_or_create_channel(company_name, settings.ZULIP_STAFF_IDS)
        company.channel_id = channel_id
        await company.asave()

    #если в Джанго нет пользователя с таким tg_id, то создаем
    user, created = await get_or_create_user_django(tg_user, company)
    if not user:
        msg_text = f"Ошибка при создании в Джанго пользователя по данныи из ТГ {tg_user}."
        logger.error(msg_text)
        send_bot_event_msg_to_zulip(msg_text)
        return

    if created:
        msg_text = f"Создан пользователь в Джанго: {user}."
        logger.info(msg_text)
        send_bot_event_msg_to_zulip(msg_text)


# Обработчик команды "/start с доп параметром", напр: https://t.me/kik_help_bot?start=ArtLife
# должен быть определен раньше "простого" ообработчика команды /start
@user_router.message(CommandStart(deep_link=True))
async def cmd_start(message: Message, command: CommandObject):
    from_user = message.from_user
    company_name = command.args

    if not command.args:
        company_name = settings.NONAME_CHANNEL_NAME

    await handle_start_command(from_user, company_name)

    await message.answer(get_about_us_text(), reply_markup=kbs.contact_keyboard())


# Этот обработчик должен быть вторым
@user_router.message(CommandStart())
async def cmd_start_no_param(message: Message) -> None:
    from_user = message.from_user
    company_name = settings.NONAME_CHANNEL_NAME

    await handle_start_command(from_user, company_name)
    await message.answer(get_about_us_text(), reply_markup=kbs.contact_keyboard())


@user_router.message(F.contact)
async def get_contact(message: Message):
    contact = message.contact
    """
    The Contact object has the following structure and attributes:
    phone_number	str	Contact's phone number.
    first_name	str	Contact's first name.
    last_name	str	Optional. Contact's last name.
    user_id	int	Optional. Contact's user identifier in Telegram.
    vcard	str	Optional. Additional data about the contact in the form of a vCard."""

    logger.info(f"Получены контакты: {contact}")

    # клиент мог повторно отправить контакты, поэтому сначала ищем его в БД
    try:
        user = await Profile.objects.select_related('company').aget(tg_id=contact.user_id)
    except Profile.DoesNotExist:
        user = None

    if user:
        if not user.phone:
            # первый раз поделился контактом
            user.phone = contact.phone_number
            await user.asave()

        # отправим "тестовое" сообщение в Zulip
        channel_id = user.company.channel_id
        topic_name = user.get_zulip_topic_name()
        message_text = "Я новый пользователь"
        zulip_client.send_msg_to_channel(channel_id, topic_name, message_text)
    else:
        msg_text = f"Получены контакты, но пользователя нет в Джанго: {contact}"  # todo  может записать в Noname ?
        logger.error(msg_text)
        send_bot_event_msg_to_zulip(msg_text)

    await message.answer(
        f"Спасибо! Теперь вы можете написать нам о своей проблеме.",
        reply_markup=ReplyKeyboardRemove()
    )

@dataclass
class ZulipMessage:
    channel_id: int
    topik_name: str
    text: str


@user_router.message(F.text)
async def user_message(message: Message) -> None:
    tg_user_id = message.from_user.id
    try:
        user = await Profile.objects.select_related('company').aget(tg_id=tg_user_id)
    except Profile.DoesNotExist:
        user = None

    if not user:
        await message.answer(
            "Вы еще не отправили ваш номер телефона.\n"
            "Нажмите на кнопку ОТПРАВИТЬ ниже.",
            reply_markup=kbs.contact_keyboard()
        )
        return

    logger.info(f"Получено сообщение от пользователя бота {user}: {message.text}")

    topic_name = user.get_zulip_topic_name()
    message_text = message.text
    channel_id = user.company.channel_id

    chat_type = message.chat.type
    if 'group' in chat_type:  # сообщение отправлено из группы
        topic_name = f"Группа_{message.chat.id}"
        message_text = f"{user.get_full_name()}: {message_text}"

    # отправим сообщение в Zulip
    zulip_client.send_msg_to_channel(channel_id, topic_name, message_text)

    # сохраним сообщение в Джанго
    dj_message = Message(
        sender=user,
        content=message_text,
    )
    await dj_message.asave()

    await asyncio.sleep(0)


@user_router.message(F.photo)
async def get_photo(message: Message):
    # todo ниже большой кусок дублируетс
    tg_user_id = message.from_user.id
    try:
        user = await Profile.objects.select_related('company').aget(tg_id=tg_user_id)
    except Profile.DoesNotExist:
        user = None

    if not user:
        await message.answer(
            "Вы еще не отправили ваш номер телефона.\n"
            "Нажмите на кнопку ОТПРАВИТЬ ниже.",
            reply_markup=kbs.contact_keyboard()
        )
        return

    logger.info(f"Получено фото от пользователя {user}")

    topic_name = user.get_zulip_topic_name()
    channel_id = user.company.channel_id

    chat_type = message.chat.type
    if 'group' in chat_type:  # сообщение отправлено из группы
        topic_name = f"Группа_{message.chat.id}"

    largest_photo = message.photo[-1]
    max_size = settings.MAX_FILE_SIZE * 1024 * 1024
    if largest_photo.file_size > max_size:
        await message.answer(
            f"Очень большой размер фото.\n"
            f"Макс допустимый размер - {max_size}Б."
        )
        return

    # фото сначала сохраняем на сервере ТГ
    destination = f"/tmp/{largest_photo.file_id}.jpg"
    await message.bot.download(file=largest_photo.file_id, destination=destination)

    #затем отправляем на сервер zulip
    try:
        with open(destination, "rb") as f:
            uploaded_file_url = zulip_client.upload_file(f)
            if uploaded_file_url:
                message_text = f"{message.caption}\n[Фото]({uploaded_file_url})"
            else:
                message_text = "Тут должна быть ссылка на файл, но файл не удалось получить."
    except Exception as e:
        message_text = f"Тут должна быть ссылка на файл, но файл не удалось получить: {e}"

    #и отправим сообщение в Zulip с ссылкой на файл
    zulip_client.send_msg_to_channel(channel_id, topic_name, message_text)

    await asyncio.sleep(0)


# @user_router.message((F.from_user.id == settings.ADMIN_TG_ID) & F.text.startswith('//'))
# async def admin_command(message: Message) -> None:
#     """
#     админская команда
#
#     todo сделать проверки try...except..
#     """
#     cmd = message.text
#     logger.info(f'Получена команда {cmd}')
#
#     if '/list' in cmd:
#         parts = cmd.split()
#         try:
#             from_id = int(parts[1])
#         except IndexError:
#             from_id = 0
#
#         user_list = db.get_40_users_from_id(from_id, session)
#         list_json = ''
#
#         for user in user_list:
#             list_json += user.model_dump_json()
#             list_json += '\n'
#
#         zulip_client.send_msg_to_channel(
#             channel_name="bot_events",
#             topic="ответы на команды",
#             msg=list_json,
#         )
#         await message.answer('Команда /list обработана')
#         logger.info('Команда /list обработана')
#
#     elif '/upd' in cmd:
#         parts = cmd.split()
#         user_id = int(parts[1])
#         update_data = json.loads(parts[2])
#         db.update_user_from_dict(user_id, update_data, session)
#
#         await message.answer(f"Запись пользователя {user_id} изменена")
#
#     elif '/del' in cmd:
#         parts = cmd.split()
#         user_id = int(parts[1])
#         user_str = db.delete_user(user_id, session)
#         if user_str:
#             await message.answer(f"{user_str} удален")
#         else:
#             await message.answer(f"Пользователь с id={user_id} не найден.")
#
#     else:
#         await message.answer(f"Неопознанная команда: {cmd}")
#




"""
Message(
    message_id=743, date=datetime.datetime(2026, 1, 18, 15, 7, 19, tzinfo=TzInfo(0)), 
    chat=Chat(id=542393918, type='private', title=None, username=None, first_name='Александр', last_name=None, is_forum=None, 
        is_direct_messages=None, accent_color_id=None, active_usernames=None, available_reactions=None, background_custom_emoji_id=None, 
        bio=None, birthdate=None, business_intro=None, business_location=None, business_opening_hours=None, can_set_sticker_set=None, 
        custom_emoji_sticker_set_name=None, description=None, emoji_status_custom_emoji_id=None, emoji_status_expiration_date=None, 
        has_aggressive_anti_spam_enabled=None, has_hidden_members=None, has_private_forwards=None, has_protected_content=None, 
        has_restricted_voice_and_video_messages=None, has_visible_history=None, invite_link=None, join_by_request=None, 
        join_to_send_messages=None, linked_chat_id=None, location=None, message_auto_delete_time=None, permissions=None, 
        personal_chat=None, photo=None, pinned_message=None, profile_accent_color_id=None, profile_background_custom_emoji_id=None, 
        slow_mode_delay=None, sticker_set_name=None, unrestrict_boost_count=None), 
    message_thread_id=None, 
    direct_messages_topic=None, 
    from_user=User(id=542393918, is_bot=False, first_name='Александр', last_name=None, username=None, language_code='ru', 
        is_premium=None, added_to_attachment_menu=None, can_join_groups=None, can_read_all_group_messages=None, 
        supports_inline_queries=None, can_connect_to_business=None, has_main_web_app=None, has_topics_enabled=None), 
    sender_chat=None, sender_boost_count=None, sender_business_bot=None, business_connection_id=None, forward_origin=None, 
    is_topic_message=None, is_automatic_forward=None, reply_to_message=None, external_reply=None, quote=None, reply_to_story=None, 
    reply_to_checklist_task_id=None, via_bot=None, edit_date=None, has_protected_content=None, is_from_offline=None, is_paid_post=None, 
    media_group_id=None, author_signature=None, paid_star_count=None, text='/start ArtLife', 
    entities=[MessageEntity(type='bot_command', offset=0, length=6, url=None, user=None, language=None, custom_emoji_id=None)], 
    link_preview_options=None, suggested_post_info=None, effect_id=None, animation=None, audio=None, document=None, paid_media=None, 
    photo=None, sticker=None, story=None, video=None, video_note=None, voice=None, caption=None, caption_entities=None, 
    show_caption_above_media=None, has_media_spoiler=None, checklist=None, contact=None, dice=None, game=None, poll=None, 
    venue=None, location=None, new_chat_members=None, left_chat_member=None, new_chat_title=None, new_chat_photo=None, 
    delete_chat_photo=None, group_chat_created=None, supergroup_chat_created=None, channel_chat_created=None, 
    message_auto_delete_timer_changed=None, migrate_to_chat_id=None, migrate_from_chat_id=None, pinned_message=None, invoice=None, 
    successful_payment=None, refunded_payment=None, users_shared=None, chat_shared=None, gift=None, unique_gift=None, 
    gift_upgrade_sent=None, connected_website=None, write_access_allowed=None, passport_data=None, proximity_alert_triggered=None, 
    boost_added=None, chat_background_set=None, checklist_tasks_done=None, checklist_tasks_added=None, direct_message_price_changed=None, 
    forum_topic_created=None, forum_topic_edited=None, forum_topic_closed=None, forum_topic_reopened=None, general_forum_topic_hidden=None, 
    general_forum_topic_unhidden=None, giveaway_created=None, giveaway=None, giveaway_winners=None, giveaway_completed=None, 
    paid_message_price_changed=None, suggested_post_approved=None, suggested_post_approval_failed=None, suggested_post_declined=None, 
    suggested_post_paid=None, suggested_post_refunded=None, video_chat_scheduled=None, video_chat_started=None, video_chat_ended=None, 
    video_chat_participants_invited=None, web_app_data=None, reply_markup=None, forward_date=None, forward_from=None, forward_from_chat=None, 
    forward_from_message_id=None, forward_sender_name=None, forward_signature=None, user_shared=None)"""