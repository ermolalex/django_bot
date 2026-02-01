import sys
import re
import json
import requests
import logging
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from profiles.models import Profile


class Command(BaseCommand):
    help = """Загрузить профили из JSON-файла, выгруженного из старой программы. 
    """
    """
    [{'zulip_channel_id': 7, 'user_type': 'client', 'id': 74, 'created_at': '2025-09-12T13:45:13.351599',
     'first_name': 'Ольга', 'last_name': None, 'tg_id': 5109290394, 'pin_code': None, 'activated': False,
     'phone_number': '79110299336'},
    {'zulip_channel_id': 78, 'user_type': 'client', 'id': 75, 'created_at': '2025-09-12T13:45:13.351599',
     'first_name': 'Главбух', 'last_name': None, 'tg_id': 8581693570, 'pin_code': None, 'activated': False,
     'phone_number': '+79500177915'}]
    """

    def add_arguments(self, parser):
        parser.add_argument('filename', type=str, help='The path to the file to be processed')


    def handle(self, *args, **options):
        filename = options["filename"]
        file_path = Path(filename)
        if not file_path.is_file():
            return

        with open(file_path, "r") as file:
            data = json.load(file)

        for item in data:
            print('*************', item)
            profile = Profile(
                username=f"{item["first_name"]}_{item["tg_id"]}",
                first_name=item["first_name"],
                last_name=item["last_name"] or item["first_name"],
                tg_id=item["tg_id"],
                phone=item["phone_number"],
                email=item["zulip_channel_id"]
            )
            profile.save()

