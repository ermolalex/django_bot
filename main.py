import os
import logging
import asyncio
from contextlib import asynccontextmanager

from django.conf import settings
from django.apps import apps
from django.core.asgi import get_asgi_application

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware

from aiogram.types import Update

import uvicorn

from bot.tg_bot.handlers.user_router import user_router
from bot.tg_bot.create_bot import bot, dp, stop_bot, start_bot

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "conf.settings")
apps.populate(settings.INSTALLED_APPS)


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.info("Starting bot setup...")
    dp.include_router(user_router)
    # dp.include_router(admin_router)
    await start_bot()
    webhook_url = settings.TG_WEBHOOK
    await bot.set_webhook(url=webhook_url,
                          allowed_updates=dp.resolve_used_update_types(),
                          drop_pending_updates=True)
    logging.info(f"Webhook set to {webhook_url}")
    yield
    logging.info("Shutting down bot...")
    await bot.delete_webhook()
    await stop_bot()
    logging.info("Webhook deleted")

app = FastAPI(lifespan=lifespan, title="Aeroplane", debug=settings.DEBUG)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# app.include_router(router, prefix="/api")
app.mount("/dj", get_asgi_application())


@app.post("/webhook")
async def webhook(request: Request) -> None:
    await request.body()
    request_json = await request.json()
    logging.info(f"Received webhook request: {request_json}")
    update = Update.model_validate(request_json, context={"bot": bot})
    await dp.feed_update(bot, update)
    #await say_after(0, update)
    logging.info("Update processed")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=80)
