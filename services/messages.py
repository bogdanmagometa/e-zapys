"""
MessageService - Centralized message text construction.

This service is responsible for all user-facing message formatting.
It uses templates from the provided templates module for the actual text content.
"""

from types import ModuleType


class MessageService:
    """Service for constructing all bot message texts."""
    
    def __init__(self, templates: ModuleType):
        """
        Initialize MessageService with a templates module.
        
        Args:
            templates: A module containing template constants (e.g., templates_uk or templates_en)
        """
        self.T = templates
    
    def help(self) -> str:
        """Help command response."""
        return self.T.HELP
    
    def availability(self, availability_data: dict) -> str:
        """
        Format availability response for /availability command.
        
        Args:
            availability_data: Dict with keys:
                - available_centers: int
                - total_centers: int
                - last_updated: str
                - centers: list of center dicts with 'center' and 'address' keys
        """
        text = self.T.AVAILABILITY_HEADER.format(
            available_centers=availability_data['available_centers'],
            total_centers=availability_data['total_centers'],
            last_updated=availability_data['last_updated']
        )
        
        centers = availability_data.get('centers', [])
        if centers:
            text += self.T.AVAILABILITY_CENTERS_HEADER
            for i, center in enumerate(centers, 1):
                text += self.T.AVAILABILITY_CENTER_ITEM.format(
                    index=i,
                    center=center['center'],
                    address=center['address']
                )
        else:
            text += self.T.AVAILABILITY_NO_CENTERS
        
        return text
    
    def availability_changed(self, changes: dict) -> str:
        """
        Format availability change notification.
        
        Args:
            changes: Dict with keys:
                - added: list of centers that became available
                - removed: list of centers that became unavailable
                Each center has 'center' and 'address' keys
        """
        added_centers = changes.get('added', [])
        removed_centers = changes.get('removed', [])
        
        text = self.T.AVAILABILITY_CHANGED_HEADER
        
        if added_centers:
            text += self.T.AVAILABILITY_ADDED_HEADER.format(count=len(added_centers))
            for i, center in enumerate(added_centers, 1):
                text += self.T.AVAILABILITY_CENTER_ITEM.format(
                    index=i,
                    center=center['center'],
                    address=center['address']
                )
        
        if removed_centers:
            text += self.T.AVAILABILITY_REMOVED_HEADER.format(count=len(removed_centers))
            for i, center in enumerate(removed_centers, 1):
                text += self.T.AVAILABILITY_CENTER_ITEM.format(
                    index=i,
                    center=center['center'],
                    address=center['address']
                )
        
        return text
    
    def subscription_prompt(self, selected_count: int, total_count: int) -> str:
        """Prompt for subscription selection UI."""
        return self.T.SUBSCRIPTION_PROMPT.format(
            selected_count=selected_count,
            total_count=total_count
        )
    
    def subscription_saved(self, selected_centers: list) -> str:
        """Subscription saved confirmation."""
        if not selected_centers:
            return self.T.SUBSCRIPTION_SAVED_EMPTY
        
        text = self.T.SUBSCRIPTION_SAVED_HEADER.format(count=len(selected_centers))
        for center in selected_centers:
            text += f"\n• {center}"
        text += self.T.SUBSCRIPTION_SAVED_FOOTER
        
        return text
    
    def subscription_no_centers(self) -> str:
        """No centers available for subscription."""
        return self.T.SUBSCRIPTION_NO_CENTERS
    
    def subscription_session_expired(self) -> str:
        """Subscription session expired message."""
        return self.T.SUBSCRIPTION_SESSION_EXPIRED
    
    def status(self, user_data: dict) -> str:
        """
        Format user status response.
        
        Args:
            user_data: Dict with keys:
                - subscribed_centers: list of center names (optional)
                - first_seen: datetime or None
                - last_interaction: datetime or None
        """
        subscribed_centers = user_data.get('subscribed_centers', [])
        first_seen = user_data.get('first_seen')
        last_interaction = user_data.get('last_interaction')
        
        has_subscriptions = len(subscribed_centers) > 0
        status_emoji = "✅" if has_subscriptions else "❌"
        
        text = self.T.STATUS_HEADER.format(
            status_emoji=status_emoji,
            centers_count=len(subscribed_centers),
            first_seen=first_seen.strftime(self.T.DATE_FORMAT) if first_seen else self.T.DATE_UNKNOWN,
            last_interaction=last_interaction.strftime(self.T.DATE_FORMAT) if last_interaction else self.T.DATE_UNKNOWN
        )
        
        if has_subscriptions:
            text += self.T.STATUS_SUBSCRIBED_CENTERS_HEADER
            for center in subscribed_centers:
                text += f"• {center}\n"
        
        text += self.T.STATUS_FOOTER
        
        return text
    
    def user_not_found(self) -> str:
        """User profile not found error."""
        return self.T.ERROR_USER_NOT_FOUND
