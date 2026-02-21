#fire_email.py

import time
import smtplib
from email.message import EmailMessage

# ========================
# EMAIL CONFIG
# ========================
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

SENDER_EMAIL = "SENDER_EMAIL@gmail.com"
APP_PASSWORD = "GMAIL_APP_PASSWORD"
RECIPIENT_EMAIL = "RECEIVER_EMAIL@gmail.com"

EMAIL_COOLDOWN_SEC = 300  # 5 minutes cooldown
_last_email_time = 0


def send_fire_email(ts, temp, hum):
    global _last_email_time

    now = time.time()

    # cooldown protection
    if (now - _last_email_time) < EMAIL_COOLDOWN_SEC:
        print("Email cooldown active. Not sending again.")
        return

    msg = EmailMessage()
    msg["Subject"] = "[Smart Bakery] FIRE ALERT!"
    msg["From"] = SENDER_EMAIL
    msg["To"] = RECIPIENT_EMAIL

    msg.set_content(
        f"FIRE DETECTED!\n\n"
        f"Time: {ts}\n"
        f"Temperature: {round(temp,2)} degC\n"
        f"Humidity: {round(hum,2)} %\n\n"
        f"Please check the bakery immediately."
    )

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.login(SENDER_EMAIL, APP_PASSWORD)
            smtp.send_message(msg)

        _last_email_time = now
        print("Fire email sent successfully!")

    except Exception as e:
        print("Failed to send email:", e)
        
        