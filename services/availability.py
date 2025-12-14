import time
import logging
import threading
from datetime import datetime
from playwright.sync_api import sync_playwright

logger = logging.getLogger(__name__)


class AvailabilityService:
    def __init__(
        self, 
        db, 
        website_url: str,
        private_key_path: str,
        private_key_password: str,
        message_service,
        check_interval: int = 300,
        bot_service=None
    ):
        """
        Initialize AvailabilityService.
        
        Args:
            db: MongoDB database
            website_url: URL of the website to check
            private_key_path: Path to the private key file for authentication
            private_key_password: Password for the private key
            message_service: MessageService instance for formatting messages
            check_interval: Interval between availability checks in seconds (default: 300 = 5 minutes)
            bot_service: BotService instance for sending notifications
        """
        self.db = db
        self.availability_collection = self.db['availability']
        
        self.website_url = website_url
        self.private_key_path = private_key_path
        self.private_key_password = private_key_password
        self.message_service = message_service
        
        self.background_thread = None
        self.stop_event = threading.Event()
        self.check_interval = check_interval
        self.bot_service = bot_service
        
    def start(self):
        """Start the background availability checking job"""
        logger.info("Starting AvailabilityService...")
        logger.info(f"Check interval configured to: {self.check_interval} seconds ({self.check_interval/60:.1f} minutes)")
        
        # Start background thread
        self.background_thread = threading.Thread(
            target=self._background_loop,
            daemon=True
        )
        self.background_thread.start()
        
        logger.info("AvailabilityService started")
    
    def stop(self):
        """Stop the background job"""
        logger.info("Stopping AvailabilityService...")
        self.stop_event.set()
        if self.background_thread:
            self.background_thread.join(timeout=5)
        logger.info("AvailabilityService stopped")
    
    def _background_loop(self):
        """Background loop that periodically checks availability"""
        logger.info("Background loop started")
        
        # Run immediately on startup, then every interval
        while not self.stop_event.is_set():
            try:
                logger.info("Starting availability check...")
                availability_data = self._check_availability()
                
                if availability_data:
                    logger.info(f"Availability check complete. Found {len(availability_data)} centers")
                    
                    # Check if availability changed (compares with DB state)
                    has_changed, changes = self._has_availability_changed(availability_data)
                    
                    # Save to database (becomes the new previous state)
                    self._save_to_db(availability_data)
                    
                    # If changed and bot service is set, notify
                    if has_changed and self.bot_service and changes:
                        logger.info("Availability has changed! Notifying subscribers...")
                        try:
                            self.bot_service.broadcast_availability_changes(changes)
                        except Exception as e:
                            logger.error(f"Error sending availability notification: {e}", exc_info=True)
                    elif has_changed:
                        logger.info("Availability has changed but no bot service is registered")
                    else:
                        logger.info("Availability unchanged")
                else:
                    logger.warning("Availability check returned no data")
                    
            except Exception as e:
                logger.error(f"Error in background availability check: {e}", exc_info=True)
            
            # Wait for next interval (or until stop event is set)
            logger.info(f"Waiting {self.check_interval} seconds before next check...")
            self.stop_event.wait(self.check_interval)
        
        logger.info("Background loop stopped")
    
    def _has_availability_changed(self, new_availability_data):
        """
        Check if availability has changed compared to previous check.
        Reads previous state from MongoDB.
        
        Args:
            new_availability_data: List of center availability data
            
        Returns:
            tuple: (bool, dict) - (has_changed, changes_dict)
                   changes_dict contains 'added' and 'removed' lists of center info
        """
        # Read previous state from MongoDB
        previous_availability_cursor = self.availability_collection.find({})
        previous_availability = list(previous_availability_cursor)
        
        if not previous_availability:
            # First check, don't notify
            logger.info("First availability check (no previous data in DB), skipping notification")
            return False, None
        
        # Create dictionaries of centers by name for comparison
        previous_centers = {
            center['center']: center 
            for center in previous_availability
        }
        
        new_centers = {
            center['center']: center 
            for center in new_availability_data
        }
        
        # Find centers that changed availability status
        added = []  # Became available
        removed = []  # Became unavailable
        
        for center_name, center_data in new_centers.items():
            previous_data = previous_centers.get(center_name)
            
            # Check if this center became available
            if center_data.get('available', False):
                # Was not available before, or didn't exist before
                if not previous_data or not previous_data.get('available', False):
                    added.append(center_data)
        
        for center_name, center_data in previous_centers.items():
            new_data = new_centers.get(center_name)
            
            # Check if this center became unavailable
            if center_data.get('available', False):
                # Is no longer available, or doesn't exist anymore
                if not new_data or not new_data.get('available', False):
                    removed.append(center_data)
        
        # Check if there's a difference
        if added or removed:
            if added:
                logger.info(f"New available centers ({len(added)}): {[c['center'] for c in added]}")
            if removed:
                logger.info(f"No longer available centers ({len(removed)}): {[c['center'] for c in removed]}")
            
            return True, {'added': added, 'removed': removed}
        
        return False, None
    
    def _save_to_db(self, availability_data):
        """Save availability data to MongoDB"""
        try:
            # Clear old data and insert new data
            self.availability_collection.delete_many({})
            
            # Prepare documents with timestamp
            documents = []
            for center in availability_data:
                doc = {
                    'center': center['center'],
                    'address': center['address'],
                    'available': center['available'],
                    'checked_at': datetime.utcnow()
                }
                documents.append(doc)
            
            if documents:
                result = self.availability_collection.insert_many(documents)
                logger.info(f"Saved {len(result.inserted_ids)} centers to database")
            else:
                logger.warning("No documents to save to database")
                
        except Exception as e:
            logger.error(f"Error saving to database: {e}", exc_info=True)
    
    def _check_availability(self):
        """Check availability using Playwright (same logic as old_main.py)"""
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=False)
                page = browser.new_page()
                
                logger.info(f"Navigating to {self.website_url}...")
                page.goto(self.website_url)

                # Accept terms and click ID GOV UA
                page.locator(".css-j8yymo").set_checked(True)
                page.locator(".css-5lykd7").click()
                
                # Authenticate with private key file
                logger.info("Authenticating with private key...")
                page.locator("table").get_by_text("Файловий носій").click()
                page.locator("#CAsServersSelect").select_option('КНЕДП АЦСК АТ КБ "ПРИВАТБАНК"')
                page.locator("#PKeyFileInput").set_input_files(self.private_key_path)
                page.locator("#PKeyPassword").fill(self.private_key_password)
                page.get_by_text("Продовжити").click()
                page.get_by_text("Продовжити").click()

                # Go to availability page
                logger.info("Navigating to exam booking page...")
                page.get_by_text("Записатись у чергу").click()
                page.get_by_text("Практичний іспит").click()
                page.get_by_text("Практичний іспит на транспортному засобі Сервісного центру МВС").click()
                page.get_by_text("категорія В (механічна КПП)").click()
                
                # Wait for centers to load
                page.wait_for_selector('button.MuiButton-outlined.MuiButton-outlinedPrimary.MuiButton-fullWidth')
                time.sleep(1)
                
                availability = []
                
                # Process all centers - just check if available, don't extract dates
                logger.info("Processing centers...")
                center_buttons = page.locator('button.MuiButton-outlined.MuiButton-outlinedPrimary.MuiButton-fullWidth').all()
                logger.info(f"Found {len(center_buttons)} centers")
                
                for i, button in enumerate(center_buttons):
                    try:
                        is_disabled = button.get_attribute('disabled') is not None
                        
                        center_name_elem = button.locator('p.MuiTypography-body1').first
                        center_address_elem = button.locator('p.MuiTypography-body2').first
                        
                        center_name = center_name_elem.inner_text().strip()
                        center_address = center_address_elem.inner_text().strip()
                        
                        center_info = {
                            'center': center_name,
                            'address': center_address,
                            'available': not is_disabled
                        }
                        
                        availability.append(center_info)
                        
                        status = "✅ Available" if not is_disabled else "❌ Not available"
                        logger.info(f"  {i+1}. {center_name}: {status}")
                        
                    except Exception as e:
                        logger.error(f"Error processing center {i}: {e}")
                        continue
                
                browser.close()
                logger.info(f"Availability check complete. Found {len(availability)} centers")
                return availability
                
        except Exception as e:
            logger.error(f"Error checking availability: {e}", exc_info=True)
            return []
    
    def get_availability(self):
        """
        Get current availability data from database.
        Returns summary of available centers.
        """
        try:
            # Get all centers from database
            all_centers = list(self.availability_collection.find({}))
            
            if not all_centers:
                return {
                    'available_centers': 0,
                    'total_centers': 0,
                    'last_updated': 'Never',
                    'centers': []
                }
            
            # Calculate statistics
            available_centers = [c for c in all_centers if c['available']]
            total_centers = len(all_centers)
            available_count = len(available_centers)
            
            # Get last update time
            if all_centers and 'checked_at' in all_centers[0]:
                last_updated = all_centers[0]['checked_at'].strftime('%Y-%m-%d %H:%M UTC')
            else:
                last_updated = 'Unknown'
            
            return {
                'available_centers': available_count,
                'total_centers': total_centers,
                'last_updated': last_updated,
                'centers': available_centers
            }
            
        except Exception as e:
            logger.error(f"Error getting availability: {e}", exc_info=True)
            return {
                'available_centers': 0,
                'total_centers': 0,
                'last_updated': 'Error',
                'centers': []
            }
