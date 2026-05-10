import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def send(subject: str, html_body: str, plain_body: str, to_email: str, from_email: str) -> None:
    """Send via Resend if RESEND_API_KEY is set, otherwise fall back to Gmail SMTP."""
    resend_key = os.environ.get("RESEND_API_KEY")
    if resend_key:
        _send_resend(subject, html_body, plain_body, to_email, from_email, resend_key)
    else:
        _send_smtp(subject, html_body, plain_body, to_email, from_email)


def _send_resend(
    subject: str,
    html_body: str,
    plain_body: str,
    to_email: str,
    from_email: str,
    api_key: str,
) -> None:
    import resend

    resend.api_key = api_key
    params: resend.Emails.SendParams = {
        "from": from_email,
        "to": [to_email],
        "subject": subject,
        "html": html_body,
        "text": plain_body,
    }
    response = resend.Emails.send(params)
    print(f"[mailer] Resend sent: id={response.id}")


def _send_smtp(
    subject: str,
    html_body: str,
    plain_body: str,
    to_email: str,
    from_email: str,
) -> None:
    smtp_user = os.environ.get("GMAIL_USER") or from_email
    smtp_pass = os.environ.get("GMAIL_APP_PASSWORD")
    if not smtp_pass:
        raise RuntimeError("No RESEND_API_KEY or GMAIL_APP_PASSWORD found in environment.")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = smtp_user
    msg["To"] = to_email
    msg.attach(MIMEText(plain_body, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.sendmail(smtp_user, [to_email], msg.as_string())

    print(f"[mailer] Gmail SMTP sent to {to_email}")
