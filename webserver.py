import os
from aiohttp import web

async def handle(request):
    return web.Response(text="Revolt Bot online")

async def start_web():
    app = web.Application()
    app.router.add_get("/", handle)
    
    runner = web.AppRunner(app)
    
    await runner.setup()
    
    site = web.TCPSite(runner, host="0.0.0.0", port=int(os.getenv("PORT", 10000)))
    
    await site.start()