from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from services.availability import AvailabilityService
from services.bot import BotService
from services.messages import MessageService
from config import settings

_availability_service = None
_bot_service = None
_message_service = None
_mongodb_client = None

def _get_templates_module():
    """Load the appropriate templates module based on LANGUAGE setting."""
    if settings.LANGUAGE == "en":
        from services import templates_en as templates
    else:
        from services import templates_uk as templates
    return templates

def get_message_service():
    global _message_service
    if _message_service is None:
        templates = _get_templates_module()
        _message_service = MessageService(templates)
    return _message_service

def get_bot_service():
    global _bot_service
    if _bot_service is None:
        db = get_db()
        message_service = get_message_service()
        _bot_service = BotService(
            bot_token=settings.BOT_TOKEN,
            db=db,
            message_service=message_service
        )
    return _bot_service

def get_availability_service():
    global _availability_service
    if _availability_service is None:
        db = get_db()
        message_service = get_message_service()
        bot_service = get_bot_service()
        _availability_service = AvailabilityService(
            db=db,
            website_url=settings.WEBSITE_URL,
            private_key_path=settings.PRIVATE_KEY_PATH,
            private_key_password=settings.PRIVATE_KEY_PASSWORD,
            message_service=message_service,
            check_interval=settings.AVAILABILITY_CHECK_INTERVAL,
            bot_service=bot_service
        )
    return _availability_service

def get_db():
    global _mongodb_client
    if _mongodb_client is None:
        _mongodb_client = MongoClient(settings.MONGODB_URI, server_api=ServerApi('1'))
        _mongodb_client.admin.command('ping')
        print("Successfully connected to MongoDB!")
    return _mongodb_client[settings.MONGODB_DB_NAME]
