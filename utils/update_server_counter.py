import asyncio
import config as cfg

INTERVAL = 60

async def update_server_counter():
    while True:
        try:
            roles = cfg.AMOUNT_OF_ROLES 

            for name, amount in roles.items():
                channel = cfg.CHANNELS[name]
                await channel.edit(name=f"┇ {name}s : {amount}")
        except Exception as er:
            print(f"Could not rename channel: {er}")

        await asyncio.sleep(INTERVAL)