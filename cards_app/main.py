import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi_sqlalchemy_monitor import SQLAlchemyMonitor
from fastapi_sqlalchemy_monitor.action import WarnMaxTotalInvocation, PrintStatistics
from starlette.middleware.sessions import SessionMiddleware

from cards_app.config.settings import settings
from cards_app.config.logging import setup_logging
from cards_app.config.database import engine

from cards_app.routers import auth, users, cards, events, store, inventory

setup_logging(settings.LOG_LEVEL)

app = FastAPI(debug=True)

app.add_middleware(
    SQLAlchemyMonitor,
    engine=engine,
    actions=[
        WarnMaxTotalInvocation(max_invocations=10),
        PrintStatistics()
    ]
)

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SESSION_SECRET_KEY
)

app.mount(settings.STATIC_URL,
          StaticFiles(directory=str(settings.STATIC_DIR)),
          name='static')

app.mount(settings.MEDIA_URL,
          StaticFiles(directory=str(settings.MEDIA_DIR)),
          name='media')

app.include_router(cards.router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(events.router)
app.include_router(store.router)
app.include_router(inventory.router)

if __name__ == '__main__':
    uvicorn.run('main:app', reload=True)
