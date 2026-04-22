import imaplib
import email
from email.header import decode_header

ZOHO_IMAP = "imap.zoho.in"
EMAIL = "ayush@edjobster.com"       # your domain email
PASSWORD = "your_app_password"          # Zoho app password

def fetch_emails():
    mail = imaplib.IMAP4_SSL(ZOHO_IMAP)
    mail.login(EMAIL, PASSWORD)

    mail.select("inbox")  # or "INBOX"

    status, messages = mail.search(None, "ALL")
    
    email_ids = messages[0].split()

    all_mails = []

    for eid in email_ids[-10:]:  # last 10 mails
        status, data = mail.fetch(eid, "(RFC822)")
        msg = email.message_from_bytes(data[0][1])

        subject, encoding = decode_header(msg["Subject"])[0]
        if isinstance(subject, bytes):
            subject = subject.decode(encoding or "utf-8")

        from_email = msg.get("From")

        # read email body
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_payload(decode=True).decode()
        else:
            body = msg.get_payload(decode=True).decode()

        all_mails.append({
            "from": from_email,
            "subject": subject,
            "body": body
        })

    mail.logout()
    return all_mails
