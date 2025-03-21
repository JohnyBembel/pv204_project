from mailersend import emails
from dotenv import load_dotenv
import os

load_dotenv()

API_KEY = os.getenv("MAILERSEND_API_KEY")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")

# code of function is copied from mailersend documentation https://developers.mailersend.com/api/v1/email.html?_gl=1*1v9az2u*_gcl_aw*R0NMLjE3NDI0MTc4MTQuQ2owS0NRancxdW0tQmhEdEFSSXNBQmpVNXg2N3BPZXJCRmUtM2pYa1hzVXlIMmVsX3dpUUkxVEVCeFlUUWZ0bVlMMjhvQ2RnNkJOb3JpVWFBbFZuRUFMd193Y0I.*_gcl_au*MTczMzU5MzkwNS4xNzQyNDE1MDE2
def send_verification_email(recipient_email, code):
    mailer = emails.NewEmail(API_KEY)

    # define an empty dict to populate with mail values
    mail_body = {}

    mail_from = {
        "name": "MarketplaceNostr",
        "email": SENDER_EMAIL,
    }

    recipients = [
        {
            "email": recipient_email,
        }
    ]

    mailer.set_mail_from(mail_from, mail_body)
    mailer.set_mail_to(recipients, mail_body)
    mailer.set_subject("MarketplaceNostr Verification", mail_body)
    mailer.set_html_content(f"Code: {code}", mail_body)

    mailer.send(mail_body)