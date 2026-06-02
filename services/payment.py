"""
NeuroFlow AI Bot - Payment Service
Generates payment info for manual verification
"""

from config import PAYMENT_METHODS


def generate_payment_link(order_id: str, amount: float, method: str = "binance") -> str:
    """
    Generate payment instructions for the user.
    Returns formatted text with payment details.
    """
    lines = [
        f"*Order #{order_id}*",
        f"Amount: *${amount:.2f} USD*",
        "",
        "*Payment Methods:*",
    ]

    for key, info in PAYMENT_METHODS.items():
        lines.append(f"")
        lines.append(f"*{info['name']}*")

        if key == "binance":
            lines.append(f"  Pay ID: `{info['id']}`")
            lines.append(f"  Amount: ${amount:.2f}")
            lines.append(f"  Reference: `{order_id}`")

        elif key == "payhere":
            lines.append(f"  Link: {info['url']}?ref={order_id}")

        elif key == "bank":
            lines.append(f"  {info['details']}")
            lines.append(f"  Reference: {order_id}")

    lines.append("")
    lines.append("After payment, send screenshot here.")
    lines.append("Your order will be completed within minutes.")

    return "\n".join(lines)
