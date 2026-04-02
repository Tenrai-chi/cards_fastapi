from fastapi import APIRouter
from fastapi.templating import Jinja2Templates
from cards_app.config.settings import settings

router = APIRouter(prefix='/class-cards', tags=['class_cards'])

templates = Jinja2Templates(directory=str(settings.BASE_DIR / 'templates'))
