"""
Payment repository implementation.
"""

from datetime import datetime, timedelta
from typing import Optional, List
from decimal import Decimal

from src.repositories.base import JSONRepository
from src.core.models.payment import Payment, PaymentStatus, PaymentMethod, Subscription


class PaymentRepository(JSONRepository[Payment]):
    """Repository for Payment entities."""

    def __init__(self, data_dir: str = "data"):
        super().__init__(
            data_dir=data_dir,
            filename="payments.json",
            entity_class=Payment
        )

    def get_by_order_id(self, order_id: str) -> Optional[Payment]:
        """Find payment by order ID."""
        return self.find_one(order_id=order_id)

    def get_by_user(self, user_id: str, status: Optional[PaymentStatus] = None) -> List[Payment]:
        """Get payments for a user."""
        criteria = {"user_id": user_id}
        if status:
            criteria["status"] = status.value
        return self.find(**criteria)

    def get_successful_payments(self, user_id: str) -> List[Payment]:
        """Get successful payments for a user."""
        return self.get_by_user(user_id, PaymentStatus.COMPLETED)

    def get_pending_payments(self, older_than_minutes: int = 30) -> List[Payment]:
        """Get pending payments older than specified minutes."""
        cutoff = datetime.utcnow() - timedelta(minutes=older_than_minutes)
        payments = self.find(status=PaymentStatus.PENDING.value)
        return [p for p in payments if p.created_at < cutoff]

    def get_refundable_payments(self, user_id: str) -> List[Payment]:
        """Get payments that can be refunded."""
        payments = self.get_by_user(user_id)
        return [p for p in payments if p.is_refundable]

    def get_revenue_stats(self, start_date: datetime, end_date: datetime) -> dict:
        """Get revenue statistics for a date range."""
        payments = self.find(status=PaymentStatus.COMPLETED.value)

        filtered = [
            p for p in payments
            if p.paid_at and start_date <= p.paid_at <= end_date
        ]

        total_revenue = sum(p.amount for p in filtered)
        total_refunded = sum(p.refund_amount or Decimal(0) for p in filtered)

        by_method = {}
        for p in filtered:
            method = p.payment_method.value if hasattr(p.payment_method, "value") else p.payment_method
            by_method[method] = by_method.get(method, Decimal(0)) + p.amount

        return {
            "total_revenue": total_revenue,
            "total_refunded": total_refunded,
            "net_revenue": total_revenue - total_refunded,
            "transaction_count": len(filtered),
            "by_method": by_method
        }


class SubscriptionRepository(JSONRepository[Subscription]):
    """Repository for Subscription entities."""

    def __init__(self, data_dir: str = "data"):
        super().__init__(
            data_dir=data_dir,
            filename="subscriptions.json",
            entity_class=Subscription
        )

    def get_active_subscription(self, user_id: str) -> Optional[Subscription]:
        """Get user's active subscription."""
        subscriptions = self.find(user_id=user_id, is_active=True)
        for sub in subscriptions:
            if not sub.is_expired:
                return sub
        return None

    def get_expiring_subscriptions(self, days: int = 7) -> List[Subscription]:
        """Get subscriptions expiring within given days."""
        cutoff = datetime.utcnow() + timedelta(days=days)
        subscriptions = self.find(is_active=True, auto_renew=True)
        return [s for s in subscriptions if s.expires_at <= cutoff and not s.is_expired]

    def get_cancelled_subscriptions(self) -> List[Subscription]:
        """Get subscriptions that were cancelled."""
        return self.find(auto_renew=False)

    def get_subscription_stats(self) -> dict:
        """Get subscription statistics."""
        subs = self.get_all()

        active = [s for s in subs if s.is_active and not s.is_expired]
        cancelled = [s for s in subs if s.cancelled_at is not None]
        trials = [s for s in subs if s.is_trial]

        by_tier = {}
        for s in active:
            tier = s.tier.value if hasattr(s.tier, "value") else s.tier
            by_tier[tier] = by_tier.get(tier, 0) + 1

        return {
            "total": len(subs),
            "active": len(active),
            "cancelled": len(cancelled),
            "trials": len(trials),
            "by_tier": by_tier
        }
