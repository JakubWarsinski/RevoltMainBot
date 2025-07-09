import os
import revolt
import asyncio
import config
import webserver

from dotenv import load_dotenv
from revolt.utils import client_session
from events.on_member_update import on_member_update
from events.on_member_leave import on_member_leave
from utils.change_user_role import change_user_role
from utils.update_server_counter import update_server_counter
from events.on_message import on_message
from events.on_raw_reaction_add import on_raw_reaction_add

load_dotenv()

TOKEN = os.getenv("TOKEN")

class Client(revolt.Client):
    async def on_ready(self):
        cfg = config.ServerData(self)
        await cfg.initialize()

        asyncio.create_task(update_server_counter())

        print("Bot is ready.")

    async def on_message(self, message):
        await on_message(message)

    async def on_raw_reaction_add(self, payload):
        await on_raw_reaction_add(payload)
    
    async def on_member_update(self, before, after):
        on_member_update(before, after)

    async def on_member_join(self, member):
        await change_user_role(member, ["Unverified"])

    async def on_member_leave(self, member):
        on_member_leave(member)

async def main():
    await asyncio.gather(webserver.start_web(), run_bot())

async def run_bot():
    async with client_session() as session:
        client = Client(session, TOKEN)
        await client.start()

asyncio.run(main())