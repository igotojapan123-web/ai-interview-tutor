"""
Payment service.

Business logic for payments and subscriptions.
"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional, Dict, Any
import logging
import secrets

from src.core.models.payment import (
    Payment, PaymentStatus, PaymentMethod, PaymentCreate, PaymentCallback,
    Product, ProductType, BillingCycle, Subscription
)
from src.core.models.user import SubscriptionTier
from src.core.exceptions import (
    NotFoundError, PaymentError, PaymentProcessingError, RefundError,
    ValidationError
)
from src.repositories.payment_repository import PaymentRepository, SubscriptionRepository
from src.services.user_service import UserService

logger = logging.getLogger(__name__)


# Product catalog
PRODUCTS = {
    "standard_monthly": Product(
        id="standard_monthly",
        name="STANDARD 월간",
        description="본격적인 면접 준비를 위한 추천 플랜",
        product_type=ProductType.SUBSCRIPTION,
        tier=SubscriptionTier.STANDARD,
        billing_cycle=BillingCycle.MONTHLY,
        price=Decimal("19900"),
        features=["AI 모의면접 일 50회", "자소서 AI 첨삭 월 10회", "개인화 추천", "채용 알림"]
    ),
    "standard_yearly": Product(
        id="standard_yearly",
        name="STANDARD 연간",
        description="연간 결제로 37% 할인",
        product_type=ProductType.SUBSCRIPTION,
        tier=SubscriptionTier.STANDARD,
        billing_cycle=BillingCycle.YEARLY,
        price=Decimal("149000"),
        original_price=Decimal("238800"),
        features=["AI 모의면접 일 50회", "자소서 AI 첨삭 월 10회", "개인화 추천", "채용 알림"]
    ),
    "premium_monthly": Product(
        id="premium_monthly",
        name="PREMIUM 월간",
        description="합격을 위한 올인원 프리미엄 플랜",
        product_type=ProductType.SUBSCRIPTION,
        tier=SubscriptionTier.PREMIUM,
        billing_cycle=BillingCycle.MONTHLY,
        price=Decimal("39900"),
        features=["AI 모의면접 무제한", "자소서 AI 첨삭 무제한", "1:1 멘토 상담 월 2회", "우선 고객 지원"]
    ),
    "premium_yearly": Product(
        id="premium_yearly",
        name="PREMIUM 연간",
        description="연간 결제로 38% 할인",
        product_type=ProductType.SUBSCRIPTION,
        tier=SubscriptionTier.PREMIUM,
        billing_cycle=BillingCycle.YEARLY,
        price=Decimal("299000"),
        original_price=Decimal("478800"),
        features=["AI 모의면접 무제한", "자소서 AI 첨삭 무제한", "1:1 멘토 상담 월 2회", "우선 고객 지원"]
    ),
}


class PaymentService:
    """Payment processing service."""

    def __init__(
        self,
        payment_repository: Optional[PaymentRepository] = None,
        subscription_repository: Optional[SubscriptionRepository] = None,
        user_service: Optional[UserService] = None
    ):
        self.payment_repo = payment_repository or PaymentRepository()
        self.subscription_repo = subscription_repository or SubscriptionRepository()
        self.user_service = user_service or UserService()

    def get_products(self) -> Dict[str, Product]:
        """Get all available products."""
        return PRODUCTS

    def get_product(self, product_id: str) -> Product:
        """Get product by ID."""
        product = PRODUCTS.get(product_id)
        if not product:
            raise NotFoundError("Product", product_id)
        return product

    def generate_order_id(self) -> str:
        """Generate unique order ID."""
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        random_part = secrets.token_hex(4).upper()
        return f"ORD-{timestamp}-{random_part}"

    def initiate_payment(self, payment_data: PaymentCreate) -> Dict[str, Any]:
        """
        Initiate a payment.

        Returns:
            Dict with payment_id, order_id, redirect_url
        """
        # Validate product
        product = self.get_product(payment_data.product_id)

        # Create payment record
        payment = Payment(
            user_id=payment_data.user_id,
            product_id=payment_data.product_id,
            order_id=self.generate_order_id(),
            amount=product.price,
            payment_method=payment_data.payment_method,
            status=PaymentStatus.PENDING
        )

        self.payment_repo.create(payment)
        logger.info(f"Payment initiated: {payment.order_id}")

        # Generate redirect URL based on payment method
        redirect_url = self._get_payment_redirect_url(payment, payment_data)

        return {
            "payment_id": payment.id,
            "order_id": payment.order_id,
            "amount": float(payment.amount),
            "redirect_url": redirect_url,
            "success": True
        }

    def _get_payment_redirect_url(self, payment: Payment, payment_data: PaymentCreate) -> str:
        """Generate payment gateway redirect URL."""
        from src.config.settings import get_settings
        settings = get_settings()

        if payment.payment_method == PaymentMethod.KAKAOPAY:
            # In production, call KakaoPay API to get redirect URL
            return f"https://mockpay.flyreadylab.com/kakaopay?order_id={payment.order_id}"
        elif payment.payment_method == PaymentMethod.TOSS:
            return f"https://mockpay.flyreadylab.com/toss?order_id={payment.order_id}"

        return f"https://mockpay.flyreadylab.com/generic?order_id={payment.order_id}"

    def process_callback(self, callback_data: PaymentCallback) -> Payment:
        """
        Process payment callback from gateway.

        Returns:
            Updated payment object
        """
        payment = self.payment_repo.get_by_order_id(callback_data.order_id)
        if not payment:
            raise NotFoundError("Payment", callback_data.order_id)

        if callback_data.status == "success":
            payment.complete(
                provider_transaction_id=callback_data.provider_transaction_id,
                receipt_url=callback_data.receipt_url
            )
            payment.provider_response = callback_data.raw_data

            # Activate subscription if applicable
            product = self.get_product(payment.product_id)
            if product.product_type == ProductType.SUBSCRIPTION:
                self._activate_subscription(payment, product)

            logger.info(f"Payment completed: {payment.order_id}")
        else:
            payment.fail(callback_data.status)
            logger.warning(f"Payment failed: {payment.order_id}")

        return self.payment_repo.update(payment)

    def _activate_subscription(self, payment: Payment, product: Product) -> Subscription:
        """Activate subscription after successful payment."""
        # Calculate expiration
        now = datetime.utcnow()
        if product.billing_cycle == BillingCycle.MONTHLY:
            expires_at = now + timedelta(days=30)
        else:
            expires_at = now + timedelta(days=365)

        # Check for existing subscription
        existing = self.subscription_repo.get_active_subscription(payment.user_id)
        if existing:
            # Renew existing
            existing.renew(expires_at, payment.id)
            subscription = self.subscription_repo.update(existing)
        else:
            # Create new subscription
            subscription = Subscription(
                user_id=payment.user_id,
                product_id=product.id,
                tier=product.tier,
                billing_cycle=product.billing_cycle,
                starts_at=now,
                expires_at=expires_at,
                last_payment_id=payment.id,
                next_billing_date=expires_at - timedelta(days=3)
            )
            subscription = self.subscription_repo.create(subscription)

        # Update user tier
        self.user_service.upgrade_subscription(
            payment.user_id,
            product.tier,
            expires_at
        )

        logger.info(f"Subscription activated for user {payment.user_id}")
        return subscription

    def cancel_payment(self, payment_id: str) -> Payment:
        """Cancel a pending payment."""
        payment = self.payment_repo.get_by_id(payment_id)
        if not payment:
            raise NotFoundError("Payment", payment_id)

        if payment.status != PaymentStatus.PENDING:
            raise PaymentError("Can only cancel pending payments")

        payment.cancel()
        return self.payment_repo.update(payment)

    def refund_payment(
        self,
        payment_id: str,
        amount: Optional[Decimal] = None,
        reason: str = "Customer request"
    ) -> Payment:
        """
        Process refund.

        Args:
            payment_id: Payment to refund
            amount: Refund amount (None for full refund)
            reason: Refund reason

        Returns:
            Updated payment
        """
        payment = self.payment_repo.get_by_id(payment_id)
        if not payment:
            raise NotFoundError("Payment", payment_id)

        if not payment.is_refundable:
            raise RefundError(payment_id, "Payment is not refundable")

        refund_amount = amount or payment.amount

        # In production, call payment gateway refund API
        payment.refund(refund_amount, reason)

        # If full refund, cancel subscription
        if refund_amount >= payment.amount:
            self._cancel_subscription(payment.user_id)

        logger.info(f"Refund processed: {payment_id}, amount: {refund_amount}")
        return self.payment_repo.update(payment)

    def _cancel_subscription(self, user_id: str) -> None:
        """Cancel user subscription."""
        subscription = self.subscription_repo.get_active_subscription(user_id)
        if subscription:
            subscription.cancel()
            self.subscription_repo.update(subscription)
            self.user_service.downgrade_subscription(user_id)

    def cancel_subscription(self, user_id: str) -> Optional[Subscription]:
        """Cancel subscription (will expire at end of period)."""
        subscription = self.subscription_repo.get_active_subscription(user_id)
        if subscription:
            subscription.cancel()
            logger.info(f"Subscription cancelled for user {user_id}")
            return self.subscription_repo.update(subscription)
        return None

    def get_user_subscription(self, user_id: str) -> Optional[Subscription]:
        """Get user's active subscription."""
        return self.subscription_repo.get_active_subscription(user_id)

    def get_user_payments(self, user_id: str) -> list:
        """Get user's payment history."""
        return self.payment_repo.get_by_user(user_id)

    def get_payment(self, payment_id: str) -> Payment:
        """Get payment by ID."""
        payment = self.payment_repo.get_by_id(payment_id)
        if not payment:
            raise NotFoundError("Payment", payment_id)
        return payment

    def get_stats(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get payment statistics."""
        payment_stats = self.payment_repo.get_revenue_stats(start_date, end_date)
        subscription_stats = self.subscription_repo.get_subscription_stats()

        return {
            "payments": payment_stats,
            "subscriptions": subscription_stats
        }
