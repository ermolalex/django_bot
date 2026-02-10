import re
import sys
import requests
import zulip
import django

import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "conf.settings")
django.setup()
from django.conf import settings

# from app.config import settings
from bot.logger import create_logger

logger = create_logger(logger_name=__name__)

class ZulipException(Exception):
    pass

class ZulipClient():
    def __init__(self):
        self.is_active = False
        self._create_client()

    def _create_client(self):
        try:
            self.client = zulip.Client(
                api_key=settings.ZULIP_API_KEY,
                email=settings.ZULIP_EMAIL,
                site=settings.ZULIP_SITE,
                insecure=settings.ZULIP_ALLOW_INSECURE
            )
            self.is_active = True
            logger.info("ZulipClient настроен.")

        except Exception as e:
            self.is_active = False
            logger.fatal(e)
            # raise ZulipException(e)

    def send_msg_to_channel(self, channel_name: str, topic: str, msg: str) -> str:
        request = {
            "type": "channel",
            "to": channel_name,
            "topic": topic,
            "content": msg,
        }
        result = self.client.send_message(request)

        # {'result': 'error', 'msg': "Channel with ID '79219376763' does not exist", 'stream_id': 79219376763,
        # 'code': 'STREAM_DOES_NOT_EXIST'}

        if result["result"] == "success":
            return
        else:
            err_msg = f"Ошибка при отправлении сообщения в канал'{channel_name}' - {result.get('msg', '')}"
            logger.warning(err_msg)
            #raise ZulipException(err_msg)

    def get_channel_id(self, channel_name: str) -> int:
        # по названию канала возвращает его ID, или 0, если канала нет
        #
        # {'result': 'error', 'msg': "Invalid channel name 'tg_bot'", 'code': 'BAD_REQUEST'}
        # {'result': 'success', 'msg': '', 'stream_id': 6}

        # if not channel_name:
        #     raise ValueError("Не указано название канала.")

        result = self.client.get_stream_id(channel_name)

        if result["result"] == 'success':
            return result["stream_id"]
        elif (result["result"] == 'error' and "Invalid channel name" in result["msg"]):  # todo
            return 0
        else:
            err_msg = f"Ошибка при обращении к каналу (get_channel_id) '{channel_name}' - {result.get('msg', '')}"
            logger.warning(err_msg)
            # raise ZulipException(err_msg)

    def get_or_create_channel(self, channel_name: str, zulip_staff_ids: [int]=[]) -> int:
        # по названию канала возвращает его ID, если канала нет, то сначала его создает
        #
        # {'result': 'error', 'msg': "Invalid channel name 'tg_bot'", 'code': 'BAD_REQUEST'}
        # {'result': 'success', 'msg': '', 'stream_id': 6}

        assert channel_name, "Не указано название канала."

        if not self.is_channel_exists(channel_name):
            # если в Zulip еще нет канала , то
            # - создаем канал, и подписываем на него всех сотрудников
            # - получаем его ID
            self.subscribe_to_channel(channel_name, zulip_staff_ids)

        channel_id = self.get_channel_id(channel_name)
        return channel_id

    def is_channel_exists(self, channel_name: str) -> bool:
        channel_id = self.get_channel_id(channel_name)
        return channel_id > 0

    def subscribe_to_channel(self, channel_name: str, principals: [int]=[]) -> int:
        # Create and subscribe to channel.
        # в параметр principals можно передать список [user_id] , которые будут подписаны на канал
        # {'result': 'success', 'msg': '', 'subscribed': {'8': ['канал про все']}, 'already_subscribed': {}} - если канал создали
        # {'result': 'success', 'msg': '', 'subscribed': {}, 'already_subscribed': {'8': ['Zulip']}} - если канал уже был
        # if not channel_name:
        #     raise ValueError("Не указано название канала.")

        result = self.client.add_subscriptions(
            streams=[
                {
                    "name": channel_name,
                    "description": f"Канал для клиента {channel_name}",
                },

            ],
            principals=principals,
        )

        if result["result"] == "success":
            if not principals:
                logger.info(f"Создан канал в Zulip '{channel_name}'")
            else:
                logger.info(f"Создан канал в Zulip '{channel_name}'. Пользователи {principals} подписаны на канал.")

            return channel_name
        else:
            err_msg = f"Ошибка при подписании на канал '{channel_name}' - {result.get('msg', '')}"
            logger.warning(err_msg)
            # raise ZulipException(err_msg)  # todo

    def get_group_members(self, group_id: int):
        # возвращает массив [user_ids]
        try:
            group_id = int(group_id)
        except ValueError:
            logger.warning(f"Неправильный номер группы Zulip - {group_id}")
            return []

        params = {
            'direct_member_only': 'false',
        }

        response = requests.get(
            f'{settings.ZULIP_SITE}/api/v1/user_groups/{group_id}/members',
            params=params,
            auth=(settings.ZULIP_EMAIL, settings.ZULIP_API_KEY),
        )

        response = response.json()
        if response["result"] == "success":
            return response["members"]

        return []

    def upload_file(self, file) -> str:
        if not file:
            return ''

        try:
            result = self.client.upload_file(file)
            if result['result'] == 'success':
                return result['url']
        except Exception as e:
            logger.error("Файл из ТГ не удалось загрузить в Zulip.")

        return ''

if __name__ == '__main__':
    try:
        client = ZulipClient()
    except ZulipException:
        sys.exit("Фатальная ошибка! Выполнение программы прекращено!")
