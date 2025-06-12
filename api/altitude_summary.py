#!/usr/bin/env python3
"""
Vercel Serverless Function for Altitude Daily Summaries
Last updated: 2025-06-11 20:47 ET
"""

from http.server import BaseHTTPRequestHandler
import json
import os
import sys
from datetime import datetime
import pytz

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from altitude_parser import AltitudeParser
from gmail_client import GmailClient
from notification_service import NotificationService

class handler(BaseHTTPRequestHandler):
    def _check_cron_auth(self):
        """Check if request is from Vercel cron system"""
        # Vercel cron jobs always send this specific user agent
        user_agent = self.headers.get('User-Agent', '')
        if 'vercel-cron/1.0' in user_agent:
            return True
            
        # Alternative: check for cron secret if set (for manual testing)
        cron_secret = os.getenv('CRON_SECRET')
        if cron_secret:
            cron_token = self.headers.get('X-Cron-Token') or self.headers.get('x-cron-token')
            return cron_token == cron_secret
            
        return False
    
    def do_GET(self):
        """Handle GET request for manual trigger"""
        try:
            # Check cron authentication first
            if not self._check_cron_auth():
                self.send_response(401)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'Unauthorized - Invalid or missing cron token'}).encode())
                return
            # Parse query parameters
            query = self.path.split('?')[1] if '?' in self.path else ''
            params = dict(param.split('=') for param in query.split('&') if '=' in param)
            
            # Use ET timezone for date default
            et_tz = pytz.timezone('US/Eastern')
            et_now = datetime.now(et_tz)
            date = params.get('date', et_now.strftime('%Y-%m-%d'))
            force = params.get('force', 'false').lower() == 'true'
            
            result = process_daily_summary(date, force)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(result, indent=2).encode())
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode())
    
    def do_POST(self):
        """Handle POST request with JSON payload"""
        try:
            # Check cron authentication first
            if not self._check_cron_auth():
                self.send_response(401)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'Unauthorized - Invalid or missing cron token'}).encode())
                return
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            # Use ET timezone for date default
            et_tz = pytz.timezone('US/Eastern')
            et_now = datetime.now(et_tz)
            date = data.get('date', et_now.strftime('%Y-%m-%d'))
            force = data.get('force', False)
            
            result = process_daily_summary(date, force)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(result, indent=2).encode())
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode())

def process_daily_summary(date_str: str, force: bool = False) -> dict:
    """
    Main function to process daily summary
    """
    try:
        # Initialize services
        gmail = GmailClient()
        parser = AltitudeParser()
        notifier = NotificationService()
        
        # Fetch Gmail messages for the date
        messages = gmail.get_altitude_messages(date_str)
        
        if not messages:
            return {
                'status': 'no_data',
                'message': f'No Altitude messages found for {date_str}',
                'date': date_str
            }
        
        # Parse messages and generate summary
        daily_summary = parser.process_messages(messages, date_str)
        
        # Send notifications
        notification_result = notifier.send_summary(daily_summary)
        
        return {
            'status': 'success',
            'message': f'Daily summary generated and sent for {date_str}',
            'date': date_str,
            'summary': daily_summary,
            'notifications': notification_result
        }
        
    except Exception as e:
        return {
            'status': 'error',
            'message': str(e),
            'date': date_str
        }

# For local testing
if __name__ == "__main__":
    print("Testing Altitude Summary...")
    result = process_daily_summary('2025-06-10', True)
    print(json.dumps(result, indent=2))
