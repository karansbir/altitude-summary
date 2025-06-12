from http.server import BaseHTTPRequestHandler
import json
import os

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Test environment variables"""
        env_vars = {
            'GMAIL_CREDENTIALS_JSON': 'exists' if os.getenv('GMAIL_CREDENTIALS_JSON') else 'missing',
            'GMAIL_TOKEN_JSON': 'exists' if os.getenv('GMAIL_TOKEN_JSON') else 'missing',
            'BREVO_API_KEY': 'exists' if os.getenv('BREVO_API_KEY') else 'missing',
            'RECIPIENT_EMAIL': os.getenv('RECIPIENT_EMAIL') or 'missing',
            'ALTITUDE_LABEL': os.getenv('ALTITUDE_LABEL') or 'missing',
        }
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(env_vars, indent=2).encode())