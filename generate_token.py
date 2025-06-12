#!/usr/bin/env python3
"""Generate OAuth token for Gmail API"""

import os
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def main():
    creds = None
    
    # Load credentials from environment variable
    credentials_json = os.getenv('GMAIL_CREDENTIALS_JSON')
    if not credentials_json:
        print("Error: GMAIL_CREDENTIALS_JSON environment variable not set")
        return
    
    # Parse credentials
    credentials_data = json.loads(credentials_json)
    
    # Create flow
    flow = InstalledAppFlow.from_client_config(
        credentials_data, SCOPES
    )
    
    print("Starting OAuth flow...")
    print("Please visit the URL and authorize the application")
    
    # Run the local server
    creds = flow.run_local_server(port=8080)
    
    # Save the credentials
    token_data = {
        'token': creds.token,
        'refresh_token': creds.refresh_token,
        'token_uri': creds.token_uri,
        'client_id': creds.client_id,
        'client_secret': creds.client_secret,
        'scopes': creds.scopes,
        'expiry': creds.expiry.isoformat() if creds.expiry else None
    }
    
    with open('token.json', 'w') as token:
        json.dump(token_data, token, indent=2)
    
    print("Token saved to token.json")
    print(f"Token will expire at: {creds.expiry}")
    
    # Also update .env file
    env_token_json = json.dumps(token_data)
    print(f"\nUpdate your .env file with:")
    print(f"GMAIL_TOKEN_JSON={env_token_json}")

if __name__ == '__main__':
    # Load .env file
    from dotenv import load_dotenv
    load_dotenv()
    
    main()