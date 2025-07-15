__author__ = "Kaarel-SOI"
__status__ = "Production"
__version__ = "1.3"
__created__ = "2025-07"

import os.path
import logging
import base64
import mimetypes
from email.message import EmailMessage

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Set up logger for the module
logger = logging.getLogger(__name__)

class gMailer():
    def __init__(self, token_file, client_secret_file, sender, recipient):      
        """
        Initializes the Mailer by passing credentials and settings directly.

        :param token_file: Path to the token.json file
        :param client_secret_file: Path to the client_secret.json file
        :param sender: Sender's email address
        :param recipient: Recipient's email address
        """
        self.token_file = token_file
        self.client_secret_file = client_secret_file
        self.sender = sender
        self.recipient = recipient
        self.service = None
        self.gmail_init()

    def gmail_init(self):
        """
        Initializes the Gmail service using OAuth 2.0 credentials.
        Code adapted from: https://developers.google.com/gmail/api/quickstart/python
        """
        SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

        creds = None
        if os.path.exists(self.token_file):
            creds = Credentials.from_authorized_user_file(self.token_file, SCOPES)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try: 
                    creds.refresh(Request())
                except Exception as e: 
                    logger.error(f"Refreshing token {self.token_file} failed.")
                    logger.error(e)
                    return
            else:
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.client_secret_file, SCOPES
                    )
                    creds = flow.run_local_server(port=0)
                except FileNotFoundError:
                    logger.error(f"Client secret file not found at {self.client_secret_file}")
                    return
            with open(self.token_file, "w") as token:
                token.write(creds.to_json())

        try:
            self.service = build("gmail", "v1", credentials=creds)            
            logger.info("Gmail service initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to build Gmail service: {e}")

    def send_email(self, subject, body, attachments=None):
        """
        Creates and sends an email with a subject, body, and optional attachments.

        :param subject: The subject line of the email.
        :param body: The plain text body of the email.
        :param attachments: A list of file paths to attach to the email.
        """
        if not self.service:
            logger.error("Email service not initialized. Cannot send email.")
            return

        message = EmailMessage()
        if isinstance(self.recipient, list):
            message["To"] = ", ".join(self.recipient)
        else:
            message["To"] = self.recipient
        message["From"] = self.sender
        message["Subject"] = subject
        message.set_content(body)

        if attachments:
            for file_path in attachments:
                if not os.path.exists(file_path):
                    logger.warning(f"Attachment file not found: {file_path}. Skipping.")
                    continue
                
                ctype, encoding = mimetypes.guess_type(file_path)
                if ctype is None or encoding is not None:
                    ctype = 'application/octet-stream'  # Default MIME type
                
                maintype, subtype = ctype.split('/', 1)

                with open(file_path, 'rb') as fp:
                    message.add_attachment(fp.read(),
                                           maintype=maintype,
                                           subtype=subtype,
                                           filename=os.path.basename(file_path))
                logger.info(f"Attached file: {file_path}")


        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        create_message = {"raw": encoded_message}

        try:
            send_request = self.service.users().messages().send(
                userId=self.sender, 
                body=create_message
            )
            sent_message = send_request.execute()
            logger.info(f"Message Sent. Message ID: {sent_message['id']}")
        except Exception as e:
            logger.error(f"Message Failed to send: {e}")

if __name__ == "__main__":
    # This script is intended to be used as a module
    # To use it import class
    # Example:
    #
    # import logging
    # from gmailer_oauth import Mailer
    #
    # logging.basicConfig(level=logging.INFO)
    #
    # mailer = gMailer(
    #     token_file='path/to/token.json',
    #     client_secret_file='path/to/client_secret.json',
    #     sender='your_email@gmail.com',
    #     recipient='recipient_email@example.com'
    # )
    # mailer.send_email("Test Subject", "Test Body", ["path/to/attachment.txt"])

    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger.info("This script is a module and is not meant to be run directly")
    logger.info("Import Mailer class to use.")