import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from cards_app.config.settings import settings
from cards_app.config.logging import setup_logging

from cards_app.routers import auth, users, cards

setup_logging(settings.LOG_LEVEL)

app = FastAPI(debug=True)

app.mount(settings.STATIC_URL,
          StaticFiles(directory=str(settings.STATIC_DIR)),
          name='static')

app.mount(settings.MEDIA_URL,
          StaticFiles(directory=str(settings.MEDIA_DIR)),
          name='media')

app.include_router(cards.router)
app.include_router(auth.router)
app.include_router(users.router)


@app.get('/')
async def root():
    return {'message': '/class-cards /users/1'}


if __name__ == '__main__':
    uvicorn.run('main:app', reload=True)
