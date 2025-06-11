#!/usr/bin/env python3
"""
Altitude Email Parser
Processes Gmail messages to generate daily summaries
"""

import re
from datetime import datetime
from typing import List, Dict, Any

class AltitudeParser:
    """Parse Altitude emails and generate daily summaries"""
    
    def __init__(self):
        self.patterns = {
            'toileting': re.compile(r'Toileting:\s*(Wet|Dry|BM)', re.IGNORECASE),
            'diaper': re.compile(r'Diaper:\s*(Wet|Dry|BM|Wet \+ BM)', re.IGNORECASE),
            'nap': re.compile(r'Nap:\s*(Start|Stop)', re.IGNORECASE),
            'am_snack': re.compile(r'AM Snack:\s*(All|Some|None)', re.IGNORECASE),
            'lunch': re.compile(r'Lunch:\s*(All|Some|None)', re.IGNORECASE),
            'pm_snack': re.compile(r'PM Snack:\s*(All|Some|None)', re.IGNORECASE),
            'time_posted': re.compile(r'posted\s+(\d{1,2}:\d{2}\s+[AP]M)', re.IGNORECASE),
            'activity': re.compile(r'([A-Za-z\s]+?):\s*([A-Za-z\s]+?)\s+Kavitha', re.IGNORECASE)
        }
    
    def process_messages(self, messages: List[Dict], date_str: str) -> Dict[str, Any]:
        """Process Gmail messages and generate daily summary"""
        all_activities = []
        
        # Extract activities from each message
        for message in messages:
            activities = self.extract_activities_from_message(message)
            all_activities.extend(activities)
        
        # Sort activities by time
        all_activities.sort(key=lambda x: self.time_to_minutes(x.get('time', '00:00 AM')))
        
        # Generate summary
        summary = self.generate_daily_summary(all_activities, date_str)
        return summary
    
    def extract_activities_from_message(self, message: Dict) -> List[Dict]:
        """Extract activities from a single Gmail message"""
        activities = []
        
        # Get email content (snippet or body)
        content = message.get('snippet', '')
        if 'payload' in message and 'body' in message['payload']:
            body_data = message['payload']['body'].get('data', '')
            if body_data:
                import base64
                try:
                    content = base64.urlsafe_b64decode(body_data).decode('utf-8')
                except:
                    content = message.get('snippet', '')
        
        # Extract time posted
        time_match = self.patterns['time_posted'].search(content)
        posted_time = time_match.group(1) if time_match else "Unknown"
        
        # Extract all activity types
        activity_extractors = [
            ('Toileting', self.patterns['toileting']),
            ('Diaper', self.patterns['diaper']),
            ('Nap', self.patterns['nap']),
            ('AM Snack', self.patterns['am_snack']),
            ('Lunch', self.patterns['lunch']),
            ('PM Snack', self.patterns['pm_snack'])
        ]
        
        for activity_type, pattern in activity_extractors:
            matches = pattern.finditer(content)
            for match in matches:
                activities.append({
                    'time': posted_time,
                    'activity': activity_type,
                    'type': match.group(1),
                    'raw_content': match.group(0)
                })
        
        # Extract other activities
        other_matches = self.patterns['activity'].finditer(content)
        standard_activities = ['toileting', 'diaper', 'nap', 'snack', 'lunch']
        
        for match in other_matches:
            activity_name = match.group(1).strip()
            activity_type = match.group(2).strip()
            
            if not any(std in activity_name.lower() for std in standard_activities):
                activities.append({
                    'time': posted_time,
                    'activity': activity_name,
                    'type': activity_type,
                    'raw_content': match.group(0)
                })
        
        return activities
    
    def generate_daily_summary(self, activities: List[Dict], date_str: str) -> Dict[str, Any]:
        """Generate daily summary from activities"""
        
        # Count toileting and diaper activities
        toileting_counts = self.count_activities_by_type(activities, 'Toileting')
        diaper_counts = self.count_activities_by_type(activities, 'Diaper')
        
        # Calculate nap duration
        nap_duration = self.calculate_nap_duration(activities)
        
        # Get meal status
        meal_status = self.get_meal_status(activities)
        
        # Get other activities
        other_activities = self.get_other_activities(activities)
        
        # Format date
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        formatted_date = date_obj.strftime('%A, %B %d, %Y')
        
        return {
            'date': date_str,
            'formatted_date': formatted_date,
            'generated_at': datetime.now().isoformat(),
            'summary': {
                'toiletings': toileting_counts,
                'diapers': diaper_counts,
                'nap_duration_minutes': nap_duration,
                'meals': meal_status,
                'other_activities': other_activities
            },
            'raw_activities': activities
        }
    
    def count_activities_by_type(self, activities: List[Dict], activity_name: str) -> Dict[str, int]:
        """Count activities by type (wet, dry, bm)"""
        filtered = [a for a in activities if a['activity'] == activity_name]
        
        counts = {'wet': 0, 'dry': 0, 'bm': 0}
        
        for activity in filtered:
            activity_type = activity['type'].lower()
            if 'wet' in activity_type:
                counts['wet'] += 1
            if 'dry' in activity_type:
                counts['dry'] += 1
            if 'bm' in activity_type:
                counts['bm'] += 1
        
        return counts
    
    def calculate_nap_duration(self, activities: List[Dict]) -> int:
        """Calculate nap duration in minutes"""
        nap_start = None
        nap_end = None
        
        for activity in activities:
            if activity['activity'] == 'Nap':
                if activity['type'].lower() == 'start':
                    nap_start = activity['time']
                elif activity['type'].lower() == 'stop':
                    nap_end = activity['time']
        
        if nap_start and nap_end:
            return self.parse_time_duration(nap_start, nap_end)
        
        return 0
    
    def parse_time_duration(self, start_time: str, end_time: str) -> int:
        """Parse time duration between start and end times"""
        try:
            start_mins = self.time_to_minutes(start_time)
            end_mins = self.time_to_minutes(end_time)
            return max(0, end_mins - start_mins)
        except:
            return 0
    
    def time_to_minutes(self, time_str: str) -> int:
        """Convert time string to minutes since midnight"""
        try:
            time_str = time_str.strip()
            time_part, period = time_str.split()
            hours, minutes = map(int, time_part.split(':'))
            
            if period.upper() == 'PM' and hours != 12:
                hours += 12
            elif period.upper() == 'AM' and hours == 12:
                hours = 0
                
            return hours * 60 + minutes
        except:
            return 0
    
    def get_meal_status(self, activities: List[Dict]) -> Dict[str, str]:
        """Get status of all meals"""
        meals = {
            'am_snack': 'None',
            'lunch': 'None', 
            'pm_snack': 'None'
        }
        
        meal_mapping = {
            'AM Snack': 'am_snack',
            'Lunch': 'lunch',
            'PM Snack': 'pm_snack'
        }
        
        for activity in activities:
            if activity['activity'] in meal_mapping:
                meal_key = meal_mapping[activity['activity']]
                meals[meal_key] = activity['type']
        
        return meals
    
    def get_other_activities(self, activities: List[Dict]) -> List[str]:
        """Get non-standard activities"""
        standard_activities = ['Toileting', 'Diaper', 'Nap', 'AM Snack', 'Lunch', 'PM Snack']
        other_activities = []
        
        for activity in activities:
            if activity['activity'] not in standard_activities:
                activity_str = f"{activity['activity']}: {activity['type']}"
                if activity_str not in other_activities:
                    other_activities.append(activity_str)
        
        return other_activities
    
    def format_summary_text(self, summary_data: Dict[str, Any]) -> str:
        """Format summary as readable text"""
        data = summary_data['summary']
        
        # Format nap duration
        nap_mins = data['nap_duration_minutes']
        nap_hours = nap_mins // 60
        nap_remaining_mins = nap_mins % 60
        nap_formatted = f"{nap_mins} mins"
        if nap_hours > 0:
            nap_formatted += f" ({nap_hours}h {nap_remaining_mins}m)"
        
        # Format other activities
        other_activities_str = ", ".join(data['other_activities']) if data['other_activities'] else "None"
        
        summary_text = f"""
=== DAILY SUMMARY FOR {summary_data['formatted_date'].upper()} ===
Generated at {datetime.fromisoformat(summary_data['generated_at']).strftime('%I:%M %p')}

1. # of Toiletings - Wet: {data['toiletings']['wet']}, Dry: {data['toiletings']['dry']}, BM: {data['toiletings']['bm']}

2. # of Diapers - Wet: {data['diapers']['wet']}, Dry: {data['diapers']['dry']}, BM: {data['diapers']['bm']}

3. Length of Nap: {nap_formatted}

4. Meals Status - AM Snack: {data['meals']['am_snack']}, Lunch: {data['meals']['lunch']}, PM Snack: {data['meals']['pm_snack']}

5. Other Activities: {other_activities_str}

---
Summary auto-generated from Altitude updates
        """.strip()
        
        return summary_text
