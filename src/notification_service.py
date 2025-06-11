#!/usr/bin/env python3
"""
Notification Service for Daily Summaries
Handles email and SMS notifications
"""

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any

class NotificationService:
    """Service for sending email and SMS notifications"""
    
    def __init__(self):
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_username = os.getenv('SMTP_USERNAME')
        self.smtp_password = os.getenv('SMTP_PASSWORD')
        self.recipient_email = os.getenv('RECIPIENT_EMAIL')
        
        # Validate required environment variables
        if not all([self.smtp_username, self.smtp_password, self.recipient_email]):
            print("Warning: Email configuration incomplete. Set SMTP_USERNAME, SMTP_PASSWORD, RECIPIENT_EMAIL")
        
    def send_summary(self, summary_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send daily summary via email"""
        try:
            from altitude_parser import AltitudeParser
            parser = AltitudeParser()
            summary_text = parser.format_summary_text(summary_data)
            
            # Send email if configured
            if all([self.smtp_username, self.smtp_password, self.recipient_email]):
                email_result = self.send_email(
                    subject=f"📊 Daily Altitude Summary - {summary_data['formatted_date']}",
                    body=summary_text
                )
            else:
                email_result = {'success': False, 'error': 'Email not configured'}
            
            return {
                'email': email_result,
                'status': 'success' if email_result.get('success') else 'failed'
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def send_email(self, subject: str, body: str) -> Dict[str, Any]:
        """Send email notification"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.smtp_username
            msg['To'] = self.recipient_email
            msg['Subject'] = subject
            
            # Add body with both plain text and HTML
            text_part = MIMEText(body, 'plain')
            msg.attach(text_part)
            
            # Create HTML version
            html_body = self._format_html_email(body)
            html_part = MIMEText(html_body, 'html')
            msg.attach(html_part)
            
            # Send email
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.smtp_username, self.smtp_password)
            
            text = msg.as_string()
            server.sendmail(self.smtp_username, self.recipient_email, text)
            server.quit()
            
            return {'success': True, 'message': 'Email sent successfully'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _format_html_email(self, text_body: str) -> str:
        """Convert plain text summary to HTML"""
        html = text_body.replace('\n', '<br>')
        html = html.replace('===', '<h2>').replace('===', '</h2>')
        html = html.replace('1. # of Toiletings', '<h3>🚽 Toiletings</h3>')
        html = html.replace('2. # of Diapers', '<h3>👶 Diapers</h3>')
        html = html.replace('3. Length of Nap', '<h3>😴 Nap Duration</h3>')
        html = html.replace('4. Meals Status', '<h3>🍽️ Meals</h3>')
        html = html.replace('5. Other Activities', '<h3>🎨 Activities</h3>')
        
        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background: #f8f9fa; padding: 20px; border-radius: 8px;">
        {html}
        </div>
        </body>
        </html>
        """
