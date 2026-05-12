import sys
import smtplib

from dotenv import load_dotenv

from config import Config
from services.email_service import EmailConfigurationError
from services.email_service import send_email


DEFAULT_RECIPIENT = "silaralph@gmail.com"


def main() -> int:
    load_dotenv()

    if len(sys.argv) > 2:
        print("Usage: python test-smtp.py [recipient@example.com]")
        return 2

    recipient = sys.argv[1].strip() if len(sys.argv) == 2 else DEFAULT_RECIPIENT
    if not recipient:
        print("Recipient email is required")
        return 2

    print("SMTP configuration:")
    print(f"  host={Config.SMTP_HOST or '<missing>'}")
    print(f"  port={Config.SMTP_PORT}")
    print(f"  username={Config.SMTP_USERNAME or '<missing>'}")
    print(f"  from_email={Config.SMTP_FROM_EMAIL or '<missing>'}")
    print(f"  use_tls={Config.SMTP_USE_TLS}")
    print(f"  use_ssl={Config.SMTP_USE_SSL}")
    print(f"  recipient={recipient}")

    try:
        send_email(
            recipient,
            "Test SMTP CEKA",
            "Bonjour,\n\nVotre configuration SMTP CEKA fonctionne.\n",
        )
    except EmailConfigurationError as exc:
        print(f"SMTP configuration error: {exc}")
        return 1
    except smtplib.SMTPAuthenticationError as exc:
        print("SMTP authentication failed.")
        print(f"Server response: {exc.smtp_code} {exc.smtp_error.decode(errors='ignore')}")
        print("Check SMTP_USERNAME and SMTP_PASSWORD in .env.")
        print("If you use Gmail, use an App Password, not your normal account password.")
        return 1
    except smtplib.SMTPException as exc:
        print(f"SMTP error: {exc}")
        return 1

    print(f"SMTP test email sent to {recipient}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
