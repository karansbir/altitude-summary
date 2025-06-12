#!/usr/bin/env python3
"""
Gmail API Client for Altitude Messages
"""

import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
except ImportError:
    print("Google API libraries not installed. Run: pip install -r requirements.txt")

class GmailClient:
    """Gmail API client for fetching Altitude messages"""
    
    SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
    
    def __init__(self):
        self.service = None
        self.authenticate()
    
    def authenticate(self):
        """Authenticate with Gmail API"""
        creds = None
        
        # Check for token in environment variable first (for serverless)
        token_json = os.getenv('GMAIL_TOKEN_JSON')
        if token_json:
            try:
                token_data = json.loads(token_json)
                creds = Credentials.from_authorized_user_info(token_data, self.SCOPES)
            except json.JSONDecodeError:
                raise ValueError("Invalid GMAIL_TOKEN_JSON format")
        # Check for existing token file
        elif os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', self.SCOPES)
        
        # If no valid credentials, authenticate
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                # Refresh the token
                creds.refresh(Request())
                
                # Save the refreshed token back to environment or file
                if os.getenv('VERCEL'):
                    # In Vercel, we can't save files, so we'll use the refresh token
                    # The refresh token doesn't expire unless revoked
                    print("Token refreshed in Vercel environment")
                elif not os.getenv('VERCEL') and os.path.exists('token.json'):
                    # Save refreshed token locally
                    with open('token.json', 'w') as token:
                        token.write(creds.to_json())
            else:
                # Use environment variables for credentials in production
                credentials_json = os.getenv('GMAIL_CREDENTIALS_JSON')
                if credentials_json:
                    try:
                        credentials_info = json.loads(credentials_json)
                        flow = InstalledAppFlow.from_client_config(credentials_info, self.SCOPES)
                    except json.JSONDecodeError:
                        raise ValueError("Invalid GMAIL_CREDENTIALS_JSON format")
                elif os.path.exists('credentials.json'):
                    flow = InstalledAppFlow.from_client_secrets_file('credentials.json', self.SCOPES)
                else:
                    raise FileNotFoundError("No Gmail credentials found. Set GMAIL_CREDENTIALS_JSON or add credentials.json")
                
                creds = flow.run_local_server(port=8080)
            
            # Save credentials for next run (not in serverless)
            if not (os.getenv('VERCEL') or os.getenv('AWS_LAMBDA_FUNCTION_NAME')):
                with open('token.json', 'w') as token:
                    token.write(creds.to_json())
        
        self.service = build('gmail', 'v1', credentials=creds)
    
    def get_altitude_messages(self, date_str: str) -> List[Dict]:
        """Get Altitude messages for a specific date"""
        try:
            label_name = os.getenv('ALTITUDE_LABEL', 'altitude')
            
            # Build search query
            query = f'label:{label_name} after:{date_str} before:{self._get_next_day(date_str)}'
            
            # Search for messages
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=100
            ).execute()
            
            messages = results.get('messages', [])
            
            # Fetch full message details
            full_messages = []
            for message in messages:
                msg = self.service.users().messages().get(
                    userId='me',
                    id=message['id'],
                    format='full'
                ).execute()
                full_messages.append(msg)
            
            return full_messages
            
        except Exception as e:
            print(f"Error fetching Gmail messages: {e}")
            return []
    
    def _get_next_day(self, date_str: str) -> str:
        """Get next day for date range query"""
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        next_day = date_obj + timedelta(days=1)
        return next_day.strftime('%Y-%m-%d')
