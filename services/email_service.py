import smtplib
from email.message import EmailMessage
from email.utils import formataddr

from config import Config


class EmailConfigurationError(RuntimeError):
    pass


def _sender() -> str:
    if not Config.SMTP_FROM_EMAIL:
        raise EmailConfigurationError("smtp_from_email_required")
    return formataddr((Config.SMTP_FROM_NAME, Config.SMTP_FROM_EMAIL))


def send_email(to_email: str, subject: str, body: str) -> None:
    if not Config.SMTP_HOST:
        raise EmailConfigurationError("smtp_host_required")

    message = EmailMessage()
    message["From"] = _sender()
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(body)

    smtp_class = smtplib.SMTP_SSL if Config.SMTP_USE_SSL else smtplib.SMTP
    with smtp_class(
        Config.SMTP_HOST,
        Config.SMTP_PORT,
        timeout=Config.SMTP_TIMEOUT_SECONDS,
    ) as smtp:
        if Config.SMTP_USE_TLS and not Config.SMTP_USE_SSL:
            smtp.starttls()
        if Config.SMTP_USERNAME or Config.SMTP_PASSWORD:
            smtp.login(Config.SMTP_USERNAME, Config.SMTP_PASSWORD)
        smtp.send_message(message)


def send_password_reset_code(to_email: str, code: str) -> None:
    body = (
        "Bonjour,\n\n"
        f"Votre code de recuperation CEKA est: {code}\n\n"
        f"Ce code expire dans {Config.PASSWORD_RESET_CODE_EXPIRATION_MINUTES} minutes.\n"
        "Si vous n'avez pas demande ce code, ignorez cet email.\n"
    )
    send_email(to_email, "Code de recuperation CEKA", body)
