import logging
from threading import Event
from contextlib import contextmanager
from dependencies import get_bot_service, get_availability_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

@contextmanager
def app_lifecycle():
    #######################
    # APPLICATION STARTUP #
    #######################
    
    logger.info("Starting app")
    
    # Initialize bot service first
    bot_service = get_bot_service()
    bot_service.start()
    logger.info("Bot service started")
    
    # Initialize availability service (starts background job)
    # The availability service already has a reference to bot_service
    availability_service = get_availability_service()
    availability_service.start()
    logger.info("Availability service started")
    
    logger.info("App started - Subscribers will receive notifications when availability changes")
    
    yield

    ########################
    # APPLICATION SHUTDOWN #
    ########################
    
    logger.info("Stopping app")
    availability_service.stop()
    bot_service.stop()
    logger.info("App stopped")

def main():
    with app_lifecycle():
        # Bot is running
        # Users can /subscribe to receive availability change notifications
        # Users can /unsubscribe to stop receiving them
        # Availability is being checked in the background
        # When availability changes, all subscribers are automatically notified
        logger.info("Application is running. Press Ctrl+C to stop.")
        Event().wait()


if __name__ == "__main__":
    main()
