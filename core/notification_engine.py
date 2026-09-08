import smtplib
import asyncio
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────────────
#  CONFIG — Loaded from .env (never hardcode!)
# ─────────────────────────────────────────────
EMAIL_SENDER     = os.getenv("EMAIL_SENDER", "")
EMAIL_PASSWORD   = os.getenv("EMAIL_PASSWORD", "")
EMAIL_RECEIVER   = os.getenv("EMAIL_RECEIVER", "")

TWILIO_ENABLED        = os.getenv("TWILIO_ENABLED", "False").lower() == "true"
TWILIO_ACCOUNT_SID    = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN     = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_FROM_NUMBER    = os.getenv("TWILIO_FROM_NUMBER", "")
TWILIO_TO_NUMBER      = os.getenv("TWILIO_TO_NUMBER", "")
# ─────────────────────────────────────────────


class NotificationEngine:
    def __init__(self):
        self.last_email_time = 0
        self.last_call_time  = 0
        self.email_cooldown  = 60   # Send email at most once every 60 seconds
        self.call_cooldown   = 120  # Make call at most once every 2 minutes

    # ── EMAIL ────────────────────────────────
    async def send_email_alert(self, threat_level: str, reasons: list, img_path: str = None):
        """Send email with snapshot attached."""
        import time
        now = time.time()
        if now - self.last_email_time < self.email_cooldown:
            return
        self.last_email_time = now

        await asyncio.to_thread(self._send_email_sync, threat_level, reasons, img_path)

    def _send_email_sync(self, threat_level: str, reasons: list, img_path: str = None):
        try:
            timestamp = datetime.now().strftime("%d/%m/%Y %I:%M:%S %p")
            reason_html = "".join(f"<li>{r}</li>" for r in reasons)

            # ── HTML body ──
            html_body = f"""
            <html><body style="font-family:Arial,sans-serif;background:#0f172a;color:#e2e8f0;padding:20px;">
              <div style="max-width:560px;margin:auto;background:#1e293b;border-radius:12px;overflow:hidden;">
                <div style="background:{'#dc2626' if threat_level=='Critical' else '#d97706'};padding:16px 24px;">
                  <h2 style="margin:0;color:#fff;">🚨 SurveilX — {threat_level} Alert!</h2>
                  <p style="margin:4px 0 0;color:#fecaca;font-size:13px;">{timestamp}</p>
                </div>
                <div style="padding:20px 24px;">
                  <p style="color:#94a3b8;font-size:13px;">The following threats were detected:</p>
                  <ul style="color:#f87171;font-size:14px;line-height:2;">{reason_html}</ul>
                  {'<p style="color:#94a3b8;font-size:12px;">📸 Snapshot attached below.</p>' if img_path else ''}
                </div>
                <div style="background:#0f172a;padding:12px 24px;text-align:center;">
                  <p style="color:#475569;font-size:11px;margin:0;">SurveilX Automated Security System</p>
                </div>
              </div>
            </body></html>
            """

            msg = MIMEMultipart("related")
            msg["Subject"] = f"🚨 [{threat_level}] SurveilX Security Alert — {timestamp}"
            msg["From"]    = EMAIL_SENDER
            msg["To"]      = EMAIL_RECEIVER

            msg.attach(MIMEText(html_body, "html"))

            # Attach snapshot if available
            if img_path and os.path.exists(img_path):
                with open(img_path, "rb") as f:
                    img = MIMEImage(f.read(), name=os.path.basename(img_path))
                    img.add_header("Content-Disposition", "attachment",
                                   filename=os.path.basename(img_path))
                    msg.attach(img)

            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(EMAIL_SENDER, EMAIL_PASSWORD)
                server.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, msg.as_string())

            print(f"[NotificationEngine] ✅ Email sent to {EMAIL_RECEIVER}")

        except Exception as e:
            print(f"[NotificationEngine] ❌ Email failed: {e}")

    # ── PHONE CALL (Twilio) ──────────────────
    async def make_phone_call(self, threat_level: str):
        """Make automated phone call via Twilio."""
        if not TWILIO_ENABLED:
            print("[NotificationEngine] ℹ️  Twilio disabled. Set TWILIO_ENABLED=True to enable calls.")
            return

        import time
        now = time.time()
        if now - self.last_call_time < self.call_cooldown:
            return
        self.last_call_time = now

        await asyncio.to_thread(self._make_call_sync, threat_level)

    def _make_call_sync(self, threat_level: str):
        try:
            from twilio.rest import Client
            client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

            # TwiML voice message spoken on the call
            twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Say voice="alice" language="en-IN">
    Warning! SurveilX has detected a {threat_level} security threat.
    Immediate attention is required. Please check your security dashboard now.
    This is an automated alert from SurveilX.
  </Say>
  <Pause length="1"/>
  <Say voice="alice" language="en-IN">Repeating. {threat_level} threat detected. Please respond immediately.</Say>
</Response>"""

            call = client.calls.create(
                twiml=twiml,
                to=TWILIO_TO_NUMBER,
                from_=TWILIO_FROM_NUMBER
            )
            print(f"[NotificationEngine] 📞 Call initiated: SID={call.sid}")

        except ImportError:
            print("[NotificationEngine] ❌ Twilio not installed. Run: pip install twilio")
        except Exception as e:
            print(f"[NotificationEngine] ❌ Call failed: {e}")
