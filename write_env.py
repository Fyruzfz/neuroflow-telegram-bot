#!/usr/bin/env python3
"""Write the .env file with bot token"""

import sys
import os

TOKEN = "8728330039:AAGmTtgfIwzCYpTLDF2EVinFSpr6lYUjW-k"
ENV_PATH = r"D:\neuroflow-code\telegram-bot\.env"

with open(ENV_PATH, "w") as f:
    f.write(f"NEUROFLOW_BOT_TOKEN={TOKEN}\n")
    f.write("ADMIN_CHAT_ID=\n")

print(f"Written to {ENV_PATH}")

# Verify
with open(ENV_PATH) as f:
    for line in f:
        if "TOKEN" in line:
            print(f"Token line: {line[:30]}... (len={len(line.split('=')[1].strip())})")
