#!/usr/bin/env python3
"""
Notification Service using Brevo (Email) and Twilio (SMS)
Handles email and SMS notifications for daily summaries
"""

import os
import json
import requests
from typing import Dict, Any, Optional
from datetime import datetime

class NotificationService:
    """Service for sending email via Brevo and SMS via Twilio"""
    
    def __init__(self):
        # Brevo configuration (for email)
        self.brevo_api_key = os.getenv('BREVO_API_KEY')
        self.from_email = os.getenv('FROM_EMAIL', 'noreply@altitude-summary.com')
        self.from_name = os.getenv('FROM_NAME', 'Altitude Summary')
        
        # Twilio configuration (for SMS/WhatsApp)
        self.twilio_account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.twilio_auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.twilio_phone_number = os.getenv('TWILIO_PHONE_NUMBER')
        self.twilio_whatsapp_number = os.getenv('TWILIO_WHATSAPP_NUMBER', 'whatsapp:+14155238886')
        
        # Recipients
        self.recipient_email = os.getenv('RECIPIENT_EMAIL')
        self.recipient_phone = os.getenv('RECIPIENT_PHONE')
        
        # Brevo setup
        self.brevo_base_url = 'https://api.brevo.com/v3'
        self.brevo_headers = {
            'accept': 'application/json',
            'api-key': self.brevo_api_key,
            'content-type': 'application/json'
        }
        
        # Initialize Twilio client if configured
        self.twilio_client = None
        if self.twilio_account_sid and self.twilio_auth_token:
            try:
                from twilio.rest import Client
                self.twilio_client = Client(self.twilio_account_sid, self.twilio_auth_token)
            except ImportError:
                print("Warning: Twilio library not installed. Run: pip install twilio")
        
        # Validate configuration
        if not self.brevo_api_key:
            print("Warning: BREVO_API_KEY not set")
        if not self.recipient_email:
            print("Warning: RECIPIENT_EMAIL not set")
        if not self.twilio_account_sid:
            print("Warning: TWILIO_ACCOUNT_SID not set (SMS disabled)")
            
    def test_connection(self) -> Dict[str, Any]:
        """Test Brevo API and Twilio connections"""
        results = {
            'status': 'failed',
            'brevo': None,
            'twilio': None
        }
        
        # Test Brevo
        if self.brevo_api_key:
            results['brevo'] = self._test_brevo_connection()
        else:
            results['brevo'] = {'status': 'failed', 'error': 'BREVO_API_KEY not configured'}
            
        # Test Twilio
        if self.twilio_client:
            results['twilio'] = self._test_twilio_connection()
        else:
            results['twilio'] = {'status': 'failed', 'error': 'Twilio not configured'}
        
        # Overall status
        if results['brevo'].get('status') == 'success' or results['twilio'].get('status') == 'success':
            results['status'] = 'partial' if results['brevo'].get('status') != results['twilio'].get('status') else 'success'
        
        return results
    
    def _test_brevo_connection(self) -> Dict[str, Any]:
        """Test Brevo API connection and sender validation"""
        try:
            # Test API connection
            response = requests.get(
                f"{self.brevo_base_url}/account",
                headers=self.brevo_headers
            )
            
            if response.status_code != 200:
                return {
                    'status': 'failed',
                    'error': f"API returned status {response.status_code}: {response.text}"
                }
            
            account_info = response.json()
            
            # Check senders
            senders_response = requests.get(
                f"{self.brevo_base_url}/senders",
                headers=self.brevo_headers
            )
            
            sender_warning = None
            if senders_response.status_code == 200:
                senders = senders_response.json().get('senders', [])
                sender_emails = [s.get('email') for s in senders if s.get('active')]
                
                if self.from_email not in sender_emails:
                    sender_warning = f"Warning: {self.from_email} is not in your verified senders list. You may need to verify it in Brevo."
            
            result = {
                'status': 'success',
                'message': 'Brevo API connected successfully',
                'account_info': {
                    'email': account_info.get('email'),
                    'company': account_info.get('companyName'),
                    'plan': account_info.get('plan', [{}])[0].get('type')
                }
            }
            
            if sender_warning:
                result['warning'] = sender_warning
                
            return result
                
        except Exception as e:
            return {
                'status': 'failed',
                'error': str(e)
            }
    
    def _test_twilio_connection(self) -> Dict[str, Any]:
        """Test Twilio connection"""
        try:
            # Get account info
            account = self.twilio_client.api.accounts(self.twilio_account_sid).fetch()
            
            # Check if phone number is valid
            phone_numbers = self.twilio_client.incoming_phone_numbers.list(
                phone_number=self.twilio_phone_number,
                limit=1
            )
            
            if not phone_numbers:
                return {
                    'status': 'failed',
                    'error': f"Phone number {self.twilio_phone_number} not found in your Twilio account"
                }
            
            return {
                'status': 'success',
                'message': 'Twilio connected successfully',
                'account_info': {
                    'friendly_name': account.friendly_name,
                    'status': account.status,
                    'phone_number': self.twilio_phone_number
                }
            }
        except Exception as e:
            return {
                'status': 'failed',
                'error': str(e)
            }
    
    def send_summary(self, summary_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send daily summary via email and SMS"""
        results = {
            'status': 'failed',
            'email_sent': False,
            'sms_sent': False
        }
        
        try:
            # Format the summary text
            from src.altitude_parser import AltitudeParser
            parser = AltitudeParser()
            full_text = parser.format_summary_text(summary_data)
            
            # Send email via Brevo
            if self.recipient_email and self.brevo_api_key:
                email_result = self._send_email_brevo(summary_data, full_text)
                results['email_sent'] = email_result.get('success', False)
                if not email_result.get('success'):
                    results['email_error'] = email_result.get('error')
            
            # Send SMS/WhatsApp via Twilio
            if self.recipient_phone and self.twilio_client:
                # Try WhatsApp first (no A2P restrictions), then SMS
                sms_result = self._send_whatsapp_twilio(summary_data)
                if not sms_result.get('success'):
                    # Fallback to SMS if WhatsApp fails
                    sms_result = self._send_sms_twilio(summary_data)
                
                results['sms_sent'] = sms_result.get('success', False)
                if not sms_result.get('success'):
                    results['sms_error'] = sms_result.get('error')
            
            # Determine overall status
            if results['email_sent'] and results['sms_sent']:
                results['status'] = 'success'
            elif results['email_sent'] or results['sms_sent']:
                results['status'] = 'partial'
                results['error'] = 'Some notifications failed to send'
            else:
                results['status'] = 'failed'
                results['error'] = 'All notifications failed'
                
        except Exception as e:
            results['status'] = 'failed'
            results['error'] = str(e)
            
        return results
    
    def _send_email_brevo(self, summary_data: Dict[str, Any], full_text: str) -> Dict[str, Any]:
        """Send email via Brevo API"""
        try:
            html_content = self._format_html_email(summary_data, full_text)
            
            payload = {
                "sender": {
                    "name": self.from_name,
                    "email": self.from_email
                },
                "to": [
                    {
                        "email": self.recipient_email
                    }
                ],
                "subject": f"📊 Altitude Summary - {summary_data['formatted_date']}",
                "htmlContent": html_content,
                "textContent": full_text
            }
            
            response = requests.post(
                f"{self.brevo_base_url}/smtp/email",
                json=payload,
                headers=self.brevo_headers
            )
            
            if response.status_code in [200, 201]:
                return {'success': True, 'message_id': response.json().get('messageId')}
            else:
                return {'success': False, 'error': f"Email API error: {response.text}"}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _send_whatsapp_twilio(self, summary_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send WhatsApp message via Twilio"""
        try:
            sms_text = self._format_sms_content(summary_data)
            
            # Format recipient phone for WhatsApp
            whatsapp_to = f"whatsapp:{self.recipient_phone}"
            
            message = self.twilio_client.messages.create(
                body=sms_text,
                from_=self.twilio_whatsapp_number,
                to=whatsapp_to
            )
            
            return {
                'success': True,
                'message_sid': message.sid,
                'status': message.status,
                'method': 'whatsapp'
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _send_sms_twilio(self, summary_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send SMS via Twilio"""
        try:
            sms_text = self._format_sms_content(summary_data)
            
            message = self.twilio_client.messages.create(
                body=sms_text,
                from_=self.twilio_phone_number,
                to=self.recipient_phone
            )
            
            return {
                'success': True,
                'message_sid': message.sid,
                'status': message.status,
                'method': 'sms'
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _format_html_email(self, summary_data: Dict[str, Any], text_content: str) -> str:
        """Format HTML email with modern design"""
        summary = summary_data['summary']
        
        # Format nap duration
        nap_mins = summary['nap_duration_minutes']
        nap_hours = nap_mins // 60
        nap_remaining = nap_mins % 60
        nap_display = f"{nap_hours}h {nap_remaining}m" if nap_hours > 0 else f"{nap_mins}m"
        
        # Format activities
        activities_html = ""
        if summary['other_activities']:
            activities_html = "<ul style='margin: 5px 0; padding-left: 20px;'>"
            for activity in summary['other_activities']:
                activities_html += f"<li style='margin: 3px 0;'>{activity}</li>"
            activities_html += "</ul>"
        else:
            activities_html = "<p style='margin: 5px 0; color: #666;'>No additional activities</p>"
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #f5f5f5;">
            <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f5f5f5; padding: 20px 0;">
                <tr>
                    <td align="center">
                        <table width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                            <!-- Header -->
                            <tr>
                                <td style="background-color: #4A90E2; color: #ffffff; padding: 20px; text-align: center; border-radius: 8px 8px 0 0;">
                                    <h1 style="margin: 0; font-size: 22px; font-weight: 600;">📊 Daily Altitude Summary</h1>
                                    <p style="margin: 8px 0 0 0; font-size: 15px; opacity: 0.9;">{summary_data['formatted_date']}</p>
                                </td>
                            </tr>
                            
                            <!-- Content -->
                            <tr>
                                <td style="padding: 20px;">
                                    <!-- Row 1: Toileting & Diapers -->
                                    <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom: 15px;">
                                        <tr>
                                            <td width="48%" style="vertical-align: top;">
                                                <div style="padding: 15px; background-color: #f8f9fa; border-radius: 6px; height: 100%;">
                                                    <h2 style="margin: 0 0 12px 0; font-size: 16px; color: #333;">
                                                        🚽 Toileting
                                                    </h2>
                                                    <table width="100%">
                                                        <tr>
                                                            <td style="text-align: center; padding: 0 10px;">
                                                                <div style="font-size: 22px; font-weight: 600; color: #4A90E2;">{summary['toiletings']['wet']}</div>
                                                                <div style="font-size: 13px; color: #666; margin-top: 2px;">Wet</div>
                                                            </td>
                                                            <td style="text-align: center; padding: 0 10px;">
                                                                <div style="font-size: 22px; font-weight: 600; color: #4A90E2;">{summary['toiletings']['dry']}</div>
                                                                <div style="font-size: 13px; color: #666; margin-top: 2px;">Dry</div>
                                                            </td>
                                                            <td style="text-align: center; padding: 0 10px;">
                                                                <div style="font-size: 22px; font-weight: 600; color: #4A90E2;">{summary['toiletings']['bm']}</div>
                                                                <div style="font-size: 13px; color: #666; margin-top: 2px;">BM</div>
                                                            </td>
                                                        </tr>
                                                    </table>
                                                </div>
                                            </td>
                                            <td width="4%"></td>
                                            <td width="48%" style="vertical-align: top;">
                                                <div style="padding: 15px; background-color: #f8f9fa; border-radius: 6px; height: 100%;">
                                                    <h2 style="margin: 0 0 12px 0; font-size: 16px; color: #333;">
                                                        👶 Diapers
                                                    </h2>
                                                    <table width="100%">
                                                        <tr>
                                                            <td style="text-align: center; padding: 0 10px;">
                                                                <div style="font-size: 22px; font-weight: 600; color: #4A90E2;">{summary['diapers']['wet']}</div>
                                                                <div style="font-size: 13px; color: #666; margin-top: 2px;">Wet</div>
                                                            </td>
                                                            <td style="text-align: center; padding: 0 10px;">
                                                                <div style="font-size: 22px; font-weight: 600; color: #4A90E2;">{summary['diapers']['dry']}</div>
                                                                <div style="font-size: 13px; color: #666; margin-top: 2px;">Dry</div>
                                                            </td>
                                                            <td style="text-align: center; padding: 0 10px;">
                                                                <div style="font-size: 22px; font-weight: 600; color: #4A90E2;">{summary['diapers']['bm']}</div>
                                                                <div style="font-size: 13px; color: #666; margin-top: 2px;">BM</div>
                                                            </td>
                                                        </tr>
                                                    </table>
                                                </div>
                                            </td>
                                        </tr>
                                    </table>
                                    
                                    <!-- Row 2: Nap Duration & Activities -->
                                    <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom: 15px;">
                                        <tr>
                                            <td width="48%" style="vertical-align: top;">
                                                <div style="padding: 15px; background-color: #f8f9fa; border-radius: 6px; height: 100%;">
                                                    <h2 style="margin: 0 0 8px 0; font-size: 16px; color: #333;">
                                                        😴 Nap Duration
                                                    </h2>
                                                    <div style="font-size: 26px; font-weight: 600; color: #4A90E2; text-align: center; padding: 10px 0;">
                                                        {nap_display}
                                                    </div>
                                                </div>
                                            </td>
                                            <td width="4%"></td>
                                            <td width="48%" style="vertical-align: top;">
                                                <div style="padding: 15px; background-color: #f8f9fa; border-radius: 6px; height: 100%;">
                                                    <h2 style="margin: 0 0 8px 0; font-size: 16px; color: #333;">
                                                        🎨 Activities
                                                    </h2>
                                                    {activities_html}
                                                </div>
                                            </td>
                                        </tr>
                                    </table>
                                    
                                    <!-- Row 3: Meals (full width) -->
                                    <div style="padding: 15px; background-color: #f8f9fa; border-radius: 6px;">
                                        <h2 style="margin: 0 0 12px 0; font-size: 16px; color: #333;">
                                            🍽️ Meals
                                        </h2>
                                        <table width="100%">
                                            <tr>
                                                <td style="text-align: center; padding: 0 15px;">
                                                    <div style="font-size: 13px; color: #666;">AM Snack</div>
                                                    <div style="font-size: 18px; font-weight: 600; color: #4A90E2; margin-top: 3px;">{summary['meals']['am_snack']}</div>
                                                </td>
                                                <td style="text-align: center; padding: 0 15px; border-left: 1px solid #e0e0e0; border-right: 1px solid #e0e0e0;">
                                                    <div style="font-size: 13px; color: #666;">Lunch</div>
                                                    <div style="font-size: 18px; font-weight: 600; color: #4A90E2; margin-top: 3px;">{summary['meals']['lunch']}</div>
                                                </td>
                                                <td style="text-align: center; padding: 0 15px;">
                                                    <div style="font-size: 13px; color: #666;">PM Snack</div>
                                                    <div style="font-size: 18px; font-weight: 600; color: #4A90E2; margin-top: 3px;">{summary['meals']['pm_snack']}</div>
                                                </td>
                                            </tr>
                                        </table>
                                    </div>
                                </td>
                            </tr>
                            
                            <!-- Footer -->
                            <tr>
                                <td style="padding: 15px; text-align: center; border-top: 1px solid #eee; color: #666; font-size: 13px;">
                                    <p style="margin: 0;">Generated at {datetime.now().strftime('%I:%M %p')}</p>
                                    <p style="margin: 5px 0 0 0; font-size: 11px;">Altitude Summary - Auto-generated from daily updates</p>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """
    
    def _format_sms_content(self, summary_data: Dict[str, Any]) -> str:
        """Format compact SMS content (160 char consideration)"""
        s = summary_data['summary']
        
        # Format nap time
        nap_mins = s['nap_duration_minutes']
        nap_h = nap_mins // 60
        nap_m = nap_mins % 60
        nap_str = f"{nap_h}h{nap_m}m" if nap_h > 0 else f"{nap_mins}m"
        
        # Shorten meal values
        meals = s['meals']
        meal_str = f"A:{meals['am_snack'][0]} L:{meals['lunch'][0]} P:{meals['pm_snack'][0]}"
        
        # Format activities (first 2 only for space)
        activities = s['other_activities'][:2] if s['other_activities'] else []
        act_str = ', '.join([a.split(':')[0] for a in activities]) if activities else 'None'
        
        # Build SMS (keeping under 160 chars)
        sms = f"""📊 Altitude Summary - {summary_data['formatted_date']}

🚽 Toileting: W:{s['toiletings']['wet']} D:{s['toiletings']['dry']} BM:{s['toiletings']['bm']}
👶 Diapers: W:{s['diapers']['wet']} D:{s['diapers']['dry']} BM:{s['diapers']['bm']}
😴 Nap: {nap_str}
🍽️ Meals: {meal_str}
🎨 Activities: {act_str}"""
        
        return sms