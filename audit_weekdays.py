#!/usr/bin/env python3
"""
Audit script to test the last 7 weekdays of data
Debug missing events and parsing issues
"""

import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from gmail_client import GmailClient
from altitude_parser import AltitudeParser

def get_last_weekdays(num_days=7):
    """Get the last N weekdays (Monday-Friday)"""
    weekdays = []
    current_date = datetime.now()
    
    while len(weekdays) < num_days:
        # Go back one day
        current_date -= timedelta(days=1)
        
        # Check if it's a weekday (Monday=0, Sunday=6)
        if current_date.weekday() < 5:  # Monday to Friday
            weekdays.append(current_date.strftime('%Y-%m-%d'))
    
    return sorted(weekdays)

def audit_day(date_str, gmail_client, parser):
    """Audit a single day's data"""
    print(f"\n{'='*60}")
    print(f"AUDITING DATE: {date_str}")
    print(f"{'='*60}")
    
    # Fetch messages
    messages = gmail_client.get_altitude_messages(date_str)
    print(f"Found {len(messages)} Gmail messages")
    
    if not messages:
        print("No messages found for this date")
        return
    
    # Debug: Show raw message content
    print(f"\n--- RAW MESSAGE CONTENT ---")
    for i, message in enumerate(messages):
        print(f"\nMessage {i+1}:")
        snippet = message.get('snippet', '')
        print(f"Snippet: {snippet}")
        
        # Try to get full body
        if 'payload' in message:
            body_data = message['payload'].get('body', {}).get('data', '')
            if body_data:
                import base64
                try:
                    full_content = base64.urlsafe_b64decode(body_data).decode('utf-8')
                    print(f"Full content: {full_content[:500]}...")
                except Exception as e:
                    print(f"Error decoding body: {e}")
    
    # Process with parser
    summary = parser.process_messages(messages, date_str)
    
    # Show results
    print(f"\n--- PARSED SUMMARY ---")
    print(f"Date: {summary['formatted_date']}")
    print(f"Toiletings: {summary['summary']['toiletings']}")
    print(f"Diapers: {summary['summary']['diapers']}")
    print(f"Nap duration: {summary['summary']['nap_duration_minutes']} minutes")
    print(f"Meals: {summary['summary']['meals']}")
    print(f"Other activities: {summary['summary']['other_activities']}")
    
    print(f"\n--- RAW ACTIVITIES FOUND ---")
    for activity in summary['raw_activities']:
        print(f"  {activity['time']} - {activity['activity']}: {activity['type']} ({activity['raw_content']})")
    
    return summary

def main():
    """Main audit function"""
    print("Starting audit of last 7 weekdays...")
    
    # Initialize clients
    try:
        gmail_client = GmailClient()
        parser = AltitudeParser()
    except Exception as e:
        print(f"Error initializing: {e}")
        return
    
    # Get weekdays to audit
    weekdays = get_last_weekdays(7)
    print(f"Auditing dates: {weekdays}")
    
    # Audit each day
    all_summaries = {}
    for date_str in weekdays:
        try:
            summary = audit_day(date_str, gmail_client, parser)
            if summary:
                all_summaries[date_str] = summary
        except Exception as e:
            print(f"Error auditing {date_str}: {e}")
    
    # Summary report
    print(f"\n{'='*60}")
    print("AUDIT SUMMARY")
    print(f"{'='*60}")
    
    for date_str, summary in all_summaries.items():
        s = summary['summary']
        total_toiletings = sum(s['toiletings'].values())
        total_diapers = sum(s['diapers'].values())
        
        print(f"{date_str}: {total_toiletings} toiletings, {total_diapers} diapers, "
              f"{s['nap_duration_minutes']}min nap, {len(s['other_activities'])} other activities")

if __name__ == "__main__":
    main()