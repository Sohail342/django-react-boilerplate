from decimal import Decimal

DEFAULT_CURRENCY = "USD"
AMOUNT_STEP = Decimal("0.01")


def _money(amount: Decimal) -> str:
    return f"{amount.quantize(AMOUNT_STEP)}"


def _person(user) -> dict | None:
    if user is None:
        return None
    name = user.get_full_name().strip() or user.get_username()
    return {"id": user.pk, "username": user.get_username(), "name": name}
