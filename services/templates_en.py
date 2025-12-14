"""
Message templates for the bot (English).

This module contains all user-facing text constants in English.
"""

# =============================================================================
# HELP
# =============================================================================

HELP = """
📋 Available commands:

/help - Show this help message
/availability - Check current availability
/change_subscription - Configure center subscriptions
/status - Check your subscription status

💡 Tip: Subscribe to centers to receive instant updates when availability changes!
"""

# =============================================================================
# AVAILABILITY
# =============================================================================

AVAILABILITY_HEADER = """
📊 Current availability:

Available centers: {available_centers} / {total_centers}
Last updated: {last_updated}
"""

AVAILABILITY_CENTERS_HEADER = "\n🏢 Centers with availability:\n"
AVAILABILITY_CENTER_ITEM = "\n{index}. {center}\n   📍 {address}"
AVAILABILITY_NO_CENTERS = "\n❌ No centers are currently available."

# =============================================================================
# AVAILABILITY CHANGED (Notifications)
# =============================================================================

AVAILABILITY_CHANGED_HEADER = "🔔 Availability update!\n"
AVAILABILITY_ADDED_HEADER = "\n✅ Now available ({count}):\n"
AVAILABILITY_REMOVED_HEADER = "\n\n❌ No longer available ({count}):\n"

# =============================================================================
# SUBSCRIPTION
# =============================================================================

SUBSCRIPTION_PROMPT = """
🔔 Subscription settings

Select centers you want to receive notifications about.
Selected: {selected_count} of {total_count}

Tap a center to select/deselect.
"""

SUBSCRIPTION_SAVED_EMPTY = """
✅ Subscription saved!

You are not subscribed to any centers.
Use /change_subscription to select centers.
"""

SUBSCRIPTION_SAVED_HEADER = """
✅ Subscription saved!

You are subscribed to {count} center(s):
"""

SUBSCRIPTION_SAVED_FOOTER = "\n\nUse /change_subscription to change settings."

SUBSCRIPTION_NO_CENTERS = """
⚠️ No centers available for subscription.

Try again later when center data is loaded.
"""

SUBSCRIPTION_SESSION_EXPIRED = "⚠️ Session expired. Use /change_subscription again."

# =============================================================================
# STATUS
# =============================================================================

STATUS_HEADER = """
📊 Your status:

Subscription: {status_emoji} {centers_count} center(s)
First interaction: {first_seen}
Last interaction: {last_interaction}
"""

STATUS_SUBSCRIBED_CENTERS_HEADER = "\n🏢 Subscribed centers:\n"
STATUS_FOOTER = "\nUse /change_subscription to change subscription."

# =============================================================================
# ERRORS
# =============================================================================

ERROR_USER_NOT_FOUND = "⚠️ Error: Could not find your profile. Try using any command first."

# =============================================================================
# FORMATTING HELPERS
# =============================================================================

DATE_FORMAT = "%Y-%m-%d %H:%M UTC"
DATE_UNKNOWN = "Unknown"

