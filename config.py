import os

from dotenv import load_dotenv
from revolt import Client, Server, Role, Server, VoiceChannel

load_dotenv()

ROLES = {}
CLIENT : Client
SERVER : Server
CHANNELS = {}

BOT_IDS = [
    os.getenv("BOT_ID_1"),
    os.getenv("BOT_ID_2"),
    os.getenv("BOT_ID_3")
]

ROLE_IDS = {
    "Artist": os.getenv("ROLE_ID_ARTIST"),
    "Member": os.getenv("ROLE_ID_MEMBER"),
    "Unverified": os.getenv("ROLE_ID_UNVERIFIED"),
    "Hidden": os.getenv("ROLE_ID_HIDDEN")
}

AMOUNT_OF_ROLES = {
    "Artist": 0,
    "Member": 0,
    "Unverified": 0
}

CHANNEL_IDS = {
    "Artist": os.getenv("CHANNEL_ID_ARTIST"),
    "Member": os.getenv("CHANNEL_ID_MEMBER"),
    "Unverified": os.getenv("CHANNEL_ID_UNVERIFIED"),
    "Verification": os.getenv("CHANNEL_ID_VERIFICATION"),
    "Verification_check": os.getenv("CHANNEL_ID_VERIFICATION_CHECK"),
    "Welcome": os.getenv("CHANNEL_ID_WELCOME")
}

class ServerData:
    def __init__(self, client: Client):
        global CLIENT
        CLIENT = client

    async def initialize(self):
        global AMOUNT_OF_ROLES, ROLES, CHANNELS, SERVER

        SERVER = await CLIENT.fetch_server(os.getenv("SERVER"))

        for name, id in CHANNEL_IDS.items():
            try:
                channel = await CLIENT.fetch_channel(id)

                CHANNELS[name] = channel
            except ValueError as e:
                print(e)

        for name in AMOUNT_OF_ROLES:
            channel: VoiceChannel  = CHANNELS[name]
            channel_name = channel.name
            number = int(channel_name.split(" ")[3])

            AMOUNT_OF_ROLES[name] = number

        for name, id in ROLE_IDS.items():
            try:
                role = SERVER.get_role(id)

                ROLES[name] = role
            except ValueError as e:
                print(e)

        print("Config initialization done.")