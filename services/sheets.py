"""
NeuroFlow AI Bot - Google Sheets Order Logger
Tracks all orders in the client tracker spreadsheet
"""

import os
import json
import urllib.request
import ssl
from datetime import datetime
from config import GOOGLE_SHEET_ID, GOOGLE_TOKEN_FILE


def _get_access_token() -> str:
    """Get a fresh Google access token from the stored credentials."""
    if not os.path.exists(GOOGLE_TOKEN_FILE):
        return ""

    with open(GOOGLE_TOKEN_FILE, "r") as f:
        creds = json.load(f)

    # creds might be the full OAuth response or just the token
    if "access_token" in creds:
        return creds["access_token"]
    if "token" in creds:
        return creds["token"]

    # Need to refresh
    if "refresh_token" in creds:
        return _refresh_token(creds["refresh_token"])

    return ""


def _refresh_token(refresh_token: str) -> str:
    """Refresh the access token."""
    try:
        data = urllib.parse.urlencode({
            "client_id": creds.get("client_id", "") if "creds" in dir() else "",
            "client_secret": creds.get("client_secret", "") if "creds" in dir() else "",
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }).encode()

        req = urllib.request.Request(
            "https://oauth2.googleapis.com/token",
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        ctx = ssl.create_default_context()
        resp = urllib.request.urlopen(req, context=ctx)
        result = json.loads(resp.read())
        return result.get("access_token", "")
    except Exception:
        return ""


async def log_order(user_id: str, username: str, service: str,
                    amount: float, order_id: str, status: str = "pending") -> bool:
    """
    Log an order to Google Sheets (Clients tab).
    Returns True if successful.
    """
    token = _get_access_token()
    if not token:
        print("[sheets] No Google token available, logging locally only")
        return False

    try:
        row_data = [
            datetime.now().strftime("%Y-%m-%d %H:%M"),
            user_id,
            username,
            "Telegram Bot",
            service,
            str(amount),
            status,
            order_id,
        ]

        # Append to sheet
        url = (
            f"https://sheets.googleapis.com/v4/spreadsheets/{GOOGLE_SHEET_ID}"
            f"/values/Clients!A:H:append"
            f"?valueInputOption=USER_ENTERED&insertDataOption=INSERT_ROWS"
        )

        body = json.dumps({"values": [row_data]}).encode()

        req = urllib.request.Request(
            url,
            data=body,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        ctx = ssl.create_default_context()
        resp = urllib.request.urlopen(req, context=ctx)
        result = json.loads(resp.read())

        return "updates" in result and result["updates"].get("updatedRows", 0) > 0

    except Exception as e:
        print(f"[sheets] Error logging order: {e}")
        return False
