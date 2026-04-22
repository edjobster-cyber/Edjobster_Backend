import imaplib
import email
import os
import logging
from email.header import decode_header
from pathlib import Path
import sys

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmailFetcher:
    """
    A standalone class to fetch email attachments from an IMAP server.
    """
    
    def __init__(self, email_account, email_password, imap_server="imap.gmail.com", download_dir="email_attachments"):
        """
        Initialize the EmailFetcher with email credentials and configuration.
        
        Args:
            email_account (str): Email address to log in with
            email_password (str): App password or account password
            imap_server (str): IMAP server address (default: Gmail)
            download_dir (str): Directory to save attachments (default: email_attachments/)
        """
        self.IMAP_SERVER = imap_server
        self.EMAIL_ACCOUNT = email_account
        self.EMAIL_PASSWORD = email_password
        
        # Set up download directory
        self.DOWNLOAD_DIR = Path(download_dir).resolve()
        self.DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    
    @staticmethod
    def clean(text):
        """Clean text to create safe filenames."""
        return "".join(c if c.isalnum() else "_" for c in str(text))
    
    def fetch_emails_with_attachments(self, search_criteria="ALL", limit=5):
        """
        Fetch emails with attachments from the IMAP server.
        
        Args:
            search_criteria (str): IMAP search criteria (e.g., 'UNSEEN', 'FROM "someone@domain.com"')
            limit (int): Maximum number of emails to process
            
        Returns:
            list: List of dictionaries containing attachment information
        """
        try:
            # Connect to the server
            mail = imaplib.IMAP4_SSL(self.IMAP_SERVER)
            
            # Login
            mail.login(self.EMAIL_ACCOUNT, self.EMAIL_PASSWORD)
            
            # Select mailbox (INBOX)
            mail.select("inbox")
            
            # Search for emails
            status, messages = mail.search(None, search_criteria)
            
            if status != "OK":
                print("No messages found!")
                return []
            
            email_ids = messages[0].split()
            print(f"Found {len(email_ids)} emails")
            
            all_attachments = []
            processed_count = 0
            
            for num in reversed(email_ids):  # Process newest emails first
                if processed_count >= limit:
                    break
                    
                try:
                    status, msg_data = mail.fetch(num, "(RFC822)")
                    if status != "OK":
                        print(f"Failed to fetch email {num}")
                        continue
                    
                    msg = email.message_from_bytes(msg_data[0][1])
                    
                    # Decode subject and from
                    subject = self._get_email_header(msg, "Subject")
                    from_ = self._get_email_header(msg, "From")
                    
                    print(f"\nProcessing: {subject} from {from_}")
                    
                    # Process email parts for attachments
                    attachments = self._process_email_parts(msg, subject, from_)
                    all_attachments.extend(attachments)
                    
                    processed_count += 1
                    
                except Exception as e:
                    print(f"Error processing email {num}: {str(e)}")
                    continue
                    
            mail.logout()
            return all_attachments
            
        except Exception as e:
            print(f"Error in fetch_emails_with_attachments: {str(e)}")
            if 'mail' in locals():
                try:
                    mail.logout()
                except:
                    pass
            return []
    
    def _get_email_header(self, msg, header_name):
        """Extract and decode email header."""
        header_value = msg.get(header_name, "")
        if not header_value:
            return ""
            
        try:
            decoded_header = decode_header(header_value)[0]
            if isinstance(decoded_header[0], bytes):
                return decoded_header[0].decode(decoded_header[1] or "utf-8", errors="ignore")
            return str(decoded_header[0])
        except Exception as e:
            print(f"Error decoding header {header_name}: {str(e)}")
            return str(header_value)

    def _process_email_parts(self, msg, subject, from_):
        """Process email parts to extract attachments."""
        attachments = []
        
        for part in msg.walk():
            content_disposition = str(part.get("Content-Disposition", "")).lower()
            
            if "attachment" in content_disposition:
                filename = part.get_filename()
                if not filename:
                    continue
                    
                try:
                    # Decode filename
                    decoded_name = self._get_email_header(part, "filename")
                    if not decoded_name:
                        decoded_name = filename
                    
                    # Clean and create safe filename
                    safe_filename = self.clean(decoded_name)
                    filepath = self.DOWNLOAD_DIR / safe_filename
                    
                    # Get file content
                    file_content = part.get_payload(decode=True)
                    
                    # Save attachment
                    with open(filepath, "wb") as f:
                        f.write(file_content)
                    
                    print(f"Saved attachment: {filepath}")
                    
                    attachment_info = {
                        "subject": subject,
                        "from": from_,
                        "filename": safe_filename,
                        "path": str(filepath),
                        "size": os.path.getsize(filepath)
                    }
                    
                    attachments.append(attachment_info)
                    
                except Exception as e:
                    print(f"Error processing attachment {filename}: {str(e)}")
                    continue
        
        return attachments

def load_environment(env_path=".env"):
    """Load environment variables from .env file if it exists."""
    try:
        env_path = Path(env_path).resolve()
        if env_path.exists():
            print(f"Loading environment variables from {env_path}")
            with open(env_path) as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        if (value.startswith('"') and value.endswith('"')) or \
                           (value.startswith("'") and value.endswith("'")):
                            value = value[1:-1]
                        os.environ[key] = value
        else:
            print("Warning: .env file not found. Using system environment variables.")
    except Exception as e:
        print(f"Warning: Could not load .env file: {str(e)}")

def main():
    # Load environment variables
    load_environment(Path(__file__).parent.parent / '.env')
    
    # Get email settings
    email_account = os.getenv('EMAIL_HOST_USER')
    email_password = os.getenv('EMAIL_HOST_PASSWORD')
    
    if not email_account or not email_password:
        print("Error: Email credentials not found.")
        print("Please set EMAIL_HOST_USER and EMAIL_HOST_PASSWORD in your .env file or environment variables.")
        print("Example:")
        print("EMAIL_HOST_USER=your-email@gmail.com")
        print("EMAIL_HOST_PASSWORD=your-app-password")
        return
    
    # Initialize fetcher
    fetcher = EmailFetcher(
        email_account=email_account,
        email_password=email_password,
        imap_server=os.getenv('EMAIL_IMAP_SERVER', 'imap.gmail.com')
    )
    
    try:
        # Fetch emails with attachments (limit to 5 most recent)
        print("Connecting to email server...")
        attachments = fetcher.fetch_emails_with_attachments(search_criteria="UNSEEN", limit=5)
        
        if not attachments:
            print("\nNo new email attachments found.")
            return
            
        print(f"\nProcessing complete. Found {len(attachments)} attachments:")
        for i, attachment in enumerate(attachments, 1):
            print(f"{i}. {attachment['filename']} ({attachment['size']} bytes) from {attachment['from']}")
            
    except Exception as e:
        print(f"\nError: {str(e)}")
        print("Please check your email settings and try again.")

if __name__ == "__main__":
    main()
