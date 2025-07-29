__author__ = "Kaarel-SOI"
__status__ = "Production"
__version__ = "1.3"
__created__ = "2025-07"

import base64
import logging
import mimetypes
import os
from email.message import EmailMessage

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


class GMailer:
    def __init__(self, token_file, client_secret_file, sender, recipient):
        """
        Initializes the Gmail client with credentials and settings.

        :param token_file: Path to the token.json file
        :param client_secret_file: Path to the client_secret.json file
        :param sender: Sender's email address
        :param recipient: Recipient's email address (string or list)
        """
        self.token_file = token_file
        self.client_secret_file = client_secret_file
        self.sender = sender
        self.recipient = recipient
        self.service = None
        self.gmail_init()

    def gmail_init(self):
        """
        Initializes the Gmail API client using OAuth 2.0 credentials.
        """
        SCOPES = ["https://www.googleapis.com/auth/gmail.send"]
        creds = None

        if os.path.exists(self.token_file):
            creds = Credentials.from_authorized_user_file(self.token_file,
                                                          SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception:
                    logger.exception("Failed to refresh token: "
                                     f"{self.token_file}")
                    return
            else:
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.client_secret_file, SCOPES
                    )
                    creds = flow.run_local_server(port=0)
                except FileNotFoundError:
                    logger.exception("Client secret file not found: "
                                     f"{self.client_secret_file}")
                    return

            with open(self.token_file, "w") as token:
                token.write(creds.to_json())

        try:
            self.service = build("gmail", "v1", credentials=creds)
            logger.info("Gmail service initialized.")
        except Exception:
            logger.exception("Failed to initialize Gmail service.")

    def send_email(self, subject, body, attachments=None, cc=None, bcc=None):
        """
        Sends an email with subject, body, attachments, and optional cc/bcc.

        :param subject: Email subject line
        :param body: Plain text body content
        :param attachments: List of file paths to attach
        :param cc: Optional CC recipient(s) (string or list)
        :param bcc: Optional BCC recipient(s) (string or list)
        """
        if not self.service:
            logger.error("Gmail service is not initialized.")
            return

        def format_addr(field):
            if not field:
                return None
            return ", ".join(field) if isinstance(field, list) else field

        message = EmailMessage()
        message["From"] = self.sender
        message["To"] = format_addr(self.recipient)
        if cc:
            message["Cc"] = format_addr(cc)
        if bcc:
            message["Bcc"] = format_addr(bcc)
        message["Subject"] = subject
        message.set_content(body)

        if attachments:
            for file_path in attachments:
                if not os.path.exists(file_path):
                    logger.warning(
                        f"Attachment not found: {file_path}. Skipping.")
                    continue

                ctype, encoding = mimetypes.guess_type(file_path)
                if ctype is None or encoding is not None:
                    ctype = "application/octet-stream"

                maintype, subtype = ctype.split("/", 1)
                with open(file_path, "rb") as fp:
                    message.add_attachment(
                        fp.read(),
                        maintype=maintype,
                        subtype=subtype,
                        filename=os.path.basename(file_path),
                    )
                logger.info(f"Attached file: {file_path}")

        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        create_message = {"raw": raw_message}

        try:
            response = self.service.users().messages().send(
                userId="me", body=create_message
            ).execute()
            logger.info(f"Email sent. Message ID: {response['id']}")
        except Exception:
            logger.exception("Failed to send email.")


if __name__ == "__main__":
    # This script is intended to be used as a module
    # To use it import class
    # Example:
    #
    # import logging
    # from gmailer_oauth import GMailer
    #
    # logging.basicConfig(level=logging.INFO)
    #
    # mailer = GMailer(
    #                  "token.json",
    #                  "client_secret.json",
    #                  "me@example.com",
    #                  "you@example.com"
    #                  )
    #
    # mailer.send_email(
    #   subject="Daily Report",
    #   body="See attached logs.",
    #   attachments=["report.txt"],
    #   cc=["team@example.com"],
    #   bcc="secret@example.com"
    # )

    logger.info("This script is a module and is not meant to be run directly")
    logger.info("Import Mailer class to use.")
