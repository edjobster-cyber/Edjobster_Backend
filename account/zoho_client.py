import requests
from django.conf import settings
from django.core.cache import cache
from django.core.mail import send_mail
import traceback
import logging


class ZohoCRMClient:
    TOKEN_CACHE_KEY = "zoho_access_token"
    TOKEN_TTL = 50 * 60  # seconds
    NOTIFICATION_EMAIL = "aakash.dubey.50159@gmail.com"

    def __init__(self):
        self.base_domain = settings.ZOHO_BASE_DOMAIN.rstrip("/")
        self.accounts_url = settings.ZOHO_ACCOUNTS_URL.rstrip("/")
        self.client_id = settings.ZOHO_CLIENT_ID
        self.client_secret = settings.ZOHO_CLIENT_SECRET
        self.refresh_token = settings.ZOHO_REFRESH_TOKEN
        self.logger = logging.getLogger(__name__)

    def _send_notification_email(self, subject: str, message: str, is_error: bool = False):
        """Send email notification for Zoho CRM operations"""
        try:
            email_subject = f"Zoho CRM {'Error' if is_error else 'Success'}: {subject}"
            from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', None) or getattr(settings, 'EMAIL_HOST_USER', None)
            
            send_mail(
                subject=email_subject,
                message=message,
                from_email=from_email,
                recipient_list=[self.NOTIFICATION_EMAIL],
                fail_silently=False
            )
            self.logger.info(f"Notification email sent to {self.NOTIFICATION_EMAIL}")
        except Exception as e:
            self.logger.error(f"Failed to send notification email: {str(e)}")

    def _refresh_access_token(self) -> str:
        token_url = f"{self.accounts_url}/oauth/v2/token"
        params = {
            "refresh_token": self.refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "refresh_token",
        }
        try:
            resp = requests.post(token_url, params=params, timeout=20)
            resp.raise_for_status()
            data = resp.json()
            access_token = data.get("access_token")
            print("Access Token:", access_token)
            if not access_token:
                error_msg = f"Zoho token refresh failed: {data}"
                self._send_notification_email("Token Refresh Failed", error_msg, is_error=True)
                raise Exception(error_msg)
            cache.set(self.TOKEN_CACHE_KEY, access_token, self.TOKEN_TTL)
            print("Access Token Cached:", cache.get(self.TOKEN_CACHE_KEY))
            self._send_notification_email("Token Refresh Success", f"Access token refreshed successfully. Expires in {self.TOKEN_TTL} seconds.")
            return access_token
        except Exception as e:
            error_msg = f"Zoho token refresh error: {str(e)}\n\nTraceback:\n{traceback.format_exc()}"
            self._send_notification_email("Token Refresh Error", error_msg, is_error=True)
            raise

    def _get_access_token(self) -> str:
        token = cache.get(self.TOKEN_CACHE_KEY)
        if token:
            return token
        return self._refresh_access_token()

    def _headers(self) -> dict:
        token = self._get_access_token()
        return {
            "Authorization": f"Zoho-oauthtoken {token}",
            "Content-Type": "application/json",
        }

    def call(self, method: str, path: str, params=None, json=None):
        url = f"{self.base_domain}/crm/v2{path}"
        headers = self._headers()
        
        try:
            resp = requests.request(method, url, headers=headers, params=params, json=json, timeout=30)

            if resp.status_code == 401:
                self._refresh_access_token()
                headers = self._headers()
                resp = requests.request(method, url, headers=headers, params=params, json=json, timeout=30)

            resp.raise_for_status()
            response_data = resp.json()
            
            # Send success notification
            success_msg = f"Zoho CRM API call successful.\n\nMethod: {method}\nPath: {path}\nStatus Code: {resp.status_code}\nResponse: {response_data}"
            self._send_notification_email(f"API Success: {method} {path}", success_msg)
            
            return response_data
            
        except requests.exceptions.HTTPError as e:
            error_msg = f"Zoho CRM API HTTP error.\n\nMethod: {method}\nPath: {path}\nStatus Code: {resp.status_code}\nResponse: {resp.text}\n\nError: {str(e)}\n\nTraceback:\n{traceback.format_exc()}"
            self._send_notification_email(f"HTTP Error: {method} {path}", error_msg, is_error=True)
            raise
        except requests.exceptions.RequestException as e:
            error_msg = f"Zoho CRM API request error.\n\nMethod: {method}\nPath: {path}\n\nError: {str(e)}\n\nTraceback:\n{traceback.format_exc()}"
            self._send_notification_email(f"Request Error: {method} {path}", error_msg, is_error=True)
            raise
        except Exception as e:
            error_msg = f"Zoho CRM API unexpected error.\n\nMethod: {method}\nPath: {path}\n\nError: {str(e)}\n\nTraceback:\n{traceback.format_exc()}"
            self._send_notification_email(f"Unexpected Error: {method} {path}", error_msg, is_error=True)
            raise

    def bulk_create(self, module: str, records: list[dict]):
        try:
            result = self.call("POST", f"/{module}", json={"data": records})
            success_msg = f"Bulk create successful for module: {module}\n\nRecords count: {len(records)}\nResponse: {result}"
            self._send_notification_email(f"Bulk Create Success: {module}", success_msg)
            return result
        except Exception as e:
            error_msg = f"Bulk create failed for module: {module}\n\nRecords count: {len(records)}\nError: {str(e)}"
            self._send_notification_email(f"Bulk Create Error: {module}", error_msg, is_error=True)
            raise
        
    def create_lead(self, lead_data: dict):
        """
        Create a new lead in Zoho CRM
        
        Args:
            lead_data (dict): Dictionary containing lead information with the following keys:
                - First_Name (str): First name of the lead
                - Last_Name (str): Last name of the lead
                - Email (str): Email address
                - Phone (str): Phone number
                - Company (str, optional): Company name
                - Lead_Source (str, optional): Source of the lead (default: 'Website')
                - Lead_Type (str, optional): Type of lead (e.g., 'Contact Us')
                - Description (str, optional): Additional notes
                - State (str, optional): State/Region
                - School_Institution_Name (str, optional): School/Institution name
                - Designation (str, optional): Job title/position
                - Any other valid Zoho CRM lead fields
                
        Returns:
            dict: Response from Zoho CRM API
        """
        # Set default values if not provided
        # lead_data.setdefault('Lead_Source', 'Website')
        print("lead_data..................", lead_data)
        # Prepare the data in the format expected by Zoho
        data = {
            "data": [lead_data],
            "trigger": ["approval", "workflow", "blueprint"]
        }
        
        # print("data..................", data)
        try:
            result = self.call("POST", "/Leads", json=data)
            success_msg = f"Lead created successfully.\n\nLead Data: {lead_data}\nResponse: {result}"
            self._send_notification_email("Lead Created Successfully", success_msg)
            return result
        except Exception as e:
            error_msg = f"Lead creation failed.\n\nLead Data: {lead_data}\nError: {str(e)}"
            self._send_notification_email("Lead Creation Failed", error_msg, is_error=True)
            raise
        
    def update_lead(self, lead_id: str, lead_data: dict):
        """
        Update an existing lead in Zoho CRM
        
        Args:
            lead_id (str): The Zoho CRM ID of the lead to update
            lead_data (dict): Dictionary containing lead fields to update
                
        Returns:
            dict: Response from Zoho CRM API
        """
        # Add the ID to the lead data
        lead_data_with_id = lead_data.copy()
        lead_data_with_id['id'] = lead_id
        # print("lead_data_with_id..................", lead_data_with_id)
        # Prepare the data in the format expected by Zoho
        data = {
            "data": [lead_data_with_id],
            "trigger": ["approval", "workflow", "blueprint"]
        }
        try:
            result = self.call("PUT", "/Leads", json=data)
            success_msg = f"Lead updated successfully.\n\nLead ID: {lead_id}\nUpdate Data: {lead_data}\nResponse: {result}"
            self._send_notification_email("Lead Updated Successfully", success_msg)
            return result
        except Exception as e:
            error_msg = f"Lead update failed.\n\nLead ID: {lead_id}\nUpdate Data: {lead_data}\nError: {str(e)}"
            self._send_notification_email("Lead Update Failed", error_msg, is_error=True)
            raise