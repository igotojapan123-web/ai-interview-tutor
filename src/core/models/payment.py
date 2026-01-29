"""
Payment and subscription domain models.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional, Dict, Any

from pydantic import Field

from src.core.models.base import Entity, BaseModel
from src.core.models.user import SubscriptionTier


class PaymentStatus(str, Enum):
    """Payment transaction status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"


class PaymentMethod(str, Enum):
    """Payment methods."""
    KAKAOPAY = "kakaopay"
    TOSS = "toss"
    CARD = "card"
    BANK_TRANSFER = "bank_transfer"
    VIRTUAL_ACCOUNT = "virtual_account"


class ProductType(str, Enum):
    """Product types."""
    SUBSCRIPTION = "subscription"
    ONE_TIME = "one_time"
    MENTOR_SESSION = "mentor_session"
    DOCUMENT_REVIEW = "document_review"


class BillingCycle(str, Enum):
    """Billing cycle for subscriptions."""
    MONTHLY = "monthly"
    YEARLY = "yearly"


class Product(BaseModel):
    """Product definition."""
    id: str
    name: str
    description: str
    product_type: ProductType
    tier: Optional[SubscriptionTier] = None
    billing_cycle: Optional[BillingCycle] = None

    # Pricing
    price: Decimal = Field(description="Price in KRW")
    original_price: Optional[Decimal] = Field(default=None, description="Original price before discount")
    currency: str = Field(default="KRW")

    # Features
    features: list[str] = Field(default_factory=list)

    # Status
    is_active: bool = Field(default=True)
    display_order: int = Field(default=0)

    @property
    def discount_percentage(self) -> Optional[int]:
        """Calculate discount percentage."""
        if self.original_price and self.original_price > 0:
            discount = ((self.original_price - self.price) / self.original_price) * 100
            return int(discount)
        return None


class Payment(Entity):
    """
    Payment transaction entity.

    Represents a single payment transaction.
    """

    # Reference
    user_id: str = Field(description="User who made the payment")
    product_id: str = Field(description="Product being purchased")
    order_id: str = Field(description="Unique order identifier")

    # Payment details
    amount: Decimal = Field(description="Payment amount")
    currency: str = Field(default="KRW")
    payment_method: PaymentMethod
    status: PaymentStatus = Field(default=PaymentStatus.PENDING)

    # Provider details
    provider_transaction_id: Optional[str] = Field(default=None, description="Payment provider's transaction ID")
    provider_response: Optional[Dict[str, Any]] = Field(default=None, description="Raw provider response")

    # Timestamps
    paid_at: Optional[datetime] = Field(default=None)
    cancelled_at: Optional[datetime] = Field(default=None)
    refunded_at: Optional[datetime] = Field(default=None)

    # Refund
    refund_amount: Optional[Decimal] = Field(default=None)
    refund_reason: Optional[str] = Field(default=None)

    # Receipt
    receipt_url: Optional[str] = Field(default=None)

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @property
    def is_successful(self) -> bool:
        """Check if payment was successful."""
        return self.status == PaymentStatus.COMPLETED

    @property
    def is_refundable(self) -> bool:
        """Check if payment can be refunded."""
        return self.status in [PaymentStatus.COMPLETED, PaymentStatus.PARTIALLY_REFUNDED]

    def complete(self, provider_transaction_id: str, receipt_url: Optional[str] = None) -> None:
        """Mark payment as completed."""
        self.status = PaymentStatus.COMPLETED
        self.provider_transaction_id = provider_transaction_id
        self.receipt_url = receipt_url
        self.paid_at = datetime.utcnow()
        self.touch()

    def fail(self, reason: str) -> None:
        """Mark payment as failed."""
        self.status = PaymentStatus.FAILED
        self.metadata["failure_reason"] = reason
        self.touch()

    def cancel(self) -> None:
        """Cancel the payment."""
        self.status = PaymentStatus.CANCELLED
        self.cancelled_at = datetime.utcnow()
        self.touch()

    def refund(self, amount: Decimal, reason: str) -> None:
        """Process refund."""
        if amount >= self.amount:
            self.status = PaymentStatus.REFUNDED
        else:
            self.status = PaymentStatus.PARTIALLY_REFUNDED

        self.refund_amount = (self.refund_amount or Decimal(0)) + amount
        self.refund_reason = reason
        self.refunded_at = datetime.utcnow()
        self.touch()


class Subscription(Entity):
    """
    User subscription entity.

    Manages user subscription lifecycle.
    """

    user_id: str
    product_id: str
    tier: SubscriptionTier
    billing_cycle: BillingCycle

    # Status
    is_active: bool = Field(default=True)
    auto_renew: bool = Field(default=True)

    # Dates
    starts_at: datetime
    expires_at: datetime
    cancelled_at: Optional[datetime] = Field(default=None)

    # Payment
    last_payment_id: Optional[str] = Field(default=None)
    next_billing_date: Optional[datetime] = Field(default=None)

    # Trial
    is_trial: bool = Field(default=False)
    trial_ends_at: Optional[datetime] = Field(default=None)

    @property
    def is_expired(self) -> bool:
        """Check if subscription is expired."""
        return datetime.utcnow() > self.expires_at

    @property
    def days_remaining(self) -> int:
        """Get days remaining in subscription."""
        if self.is_expired:
            return 0
        delta = self.expires_at - datetime.utcnow()
        return max(0, delta.days)

    def cancel(self) -> None:
        """Cancel subscription (will expire at end of period)."""
        self.auto_renew = False
        self.cancelled_at = datetime.utcnow()
        self.touch()

    def renew(self, new_expires_at: datetime, payment_id: str) -> None:
        """Renew subscription."""
        self.expires_at = new_expires_at
        self.last_payment_id = payment_id
        self.is_active = True
        self.touch()


class PaymentCreate(BaseModel):
    """DTO for creating a payment."""
    user_id: str
    product_id: str
    payment_method: PaymentMethod
    return_url: Optional[str] = None
    cancel_url: Optional[str] = None


class PaymentCallback(BaseModel):
    """DTO for payment callback."""
    order_id: str
    provider_transaction_id: str
    status: str
    amount: Decimal
    paid_at: Optional[datetime] = None
    receipt_url: Optional[str] = None
    raw_data: Optional[Dict[str, Any]] = None
