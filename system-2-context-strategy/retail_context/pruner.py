"""Select the small set of order fields needed for return decisions."""

from __future__ import annotations

KEPT_FIELDS = (
    "order_id",
    "order_date",
    "order_total_usd",
    "fulfillment_status",
    "return_eligible_until",
)


class PrunerMissingFieldError(KeyError):
    """Raised when an order lookup does not contain a required decision field."""


def prune_lookup_order(raw: dict) -> dict:
    missing = [name for name in KEPT_FIELDS if name not in raw]
    if missing:
        raise PrunerMissingFieldError(
            f"lookup_order response is missing required kept fields: {missing}"
        )
    return {name: raw[name] for name in KEPT_FIELDS}
