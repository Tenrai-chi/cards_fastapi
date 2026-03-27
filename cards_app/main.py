from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from cards_app.config.settings import settings
from cards_app.config.logging import setup_logging

from cards_app.routers.cards_routers import router

setup_logging(settings.LOG_LEVEL)

app = FastAPI(debug=True)

app.mount(settings.STATIC_URL,
          StaticFiles(directory=str(settings.STATIC_DIR)),
          name="static")

app.mount(settings.MEDIA_URL,
          StaticFiles(directory=str(settings.MEDIA_DIR)),
          name="media")

app.include_router(router)


@app.get("/")
async def root():
    return {"message": "Классы карт доступны по /class-cards"}

