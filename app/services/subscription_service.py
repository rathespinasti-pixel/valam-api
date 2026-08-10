from app.models.subscription import Subscription
from app.extensions import db

class SubscriptionService:
    """Service layer for subscription related permission checks."""

    @staticmethod
    def get_subscription(user_id: int) -> Subscription:
        """Fetch the subscription record for a given user."""
        return Subscription.query.filter_by(user_id=user_id).first()

    @staticmethod
    def can_access_marketplace(user_id: int) -> bool:
        """Return True if the user's subscription level is PRO, granting marketplace access."""
        sub = SubscriptionService.get_subscription(user_id)
        if not sub:
            return False
        return sub.has_marketplace_access()

    # Placeholder for additional permission checks (e.g., can_view_full_lifecycle, can_create_forum_post)
