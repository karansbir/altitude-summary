#!/usr/bin/env python3
"""
Database Client for Altitude Summary
Handles database operations using Supabase
"""

import os
from datetime import datetime, date
from typing import List, Dict, Any, Optional
from supabase import create_client, Client
import json

class DatabaseClient:
    """Handle database operations for activity logging"""
    
    def __init__(self):
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_ANON_KEY')
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY environment variables are required")
        
        self.client: Client = create_client(self.supabase_url, self.supabase_key)
    
    def insert_activities(self, activities: List[Dict[str, Any]], source_message_id: str) -> List[Dict]:
        """Insert activities into the database"""
        db_activities = []
        
        for activity in activities:
            # Convert activity to database format
            db_activity = {
                'timestamp': datetime.now().isoformat(),
                'date': activity.get('date'),
                'activity_type': self._get_activity_type(activity['activity']),
                'activity_subtype': activity.get('type', '').lower() if activity.get('type') else None,
                'activity_name': activity['activity'],
                'raw_content': activity.get('raw_content', ''),
                'parsed_time': activity.get('time', ''),
                'source_message_id': source_message_id
            }
            db_activities.append(db_activity)
        
        # Insert into database
        result = self.client.table('activities').insert(db_activities).execute()
        return result.data
    
    def _get_activity_type(self, activity_name: str) -> str:
        """Map activity name to standardized type"""
        activity_lower = activity_name.lower()
        
        if 'toilet' in activity_lower:
            return 'toileting'
        elif 'diaper' in activity_lower:
            return 'diaper'
        elif 'nap' in activity_lower:
            return 'nap'
        elif 'snack' in activity_lower or 'lunch' in activity_lower:
            return 'meal'
        else:
            return 'other'
    
    def get_daily_activities(self, date_str: str) -> List[Dict]:
        """Get all activities for a specific date"""
        result = self.client.table('activities').select("*").eq('date', date_str).order('timestamp').execute()
        return result.data
    
    def get_activities_by_date_range(self, start_date: str, end_date: str) -> List[Dict]:
        """Get activities within a date range"""
        result = (self.client.table('activities')
                 .select("*")
                 .gte('date', start_date)
                 .lte('date', end_date)
                 .order('timestamp')
                 .execute())
        return result.data
    
    def get_all_activities(self) -> List[Dict]:
        """Get all activities from the database"""
        result = self.client.table('activities').select("*").order('timestamp').execute()
        return result.data
    
    def generate_daily_summary_from_db(self, date_str: str) -> Dict[str, Any]:
        """Generate daily summary from database activities"""
        activities = self.get_daily_activities(date_str)
        
        if not activities:
            return {
                'date': date_str,
                'formatted_date': self._format_date(date_str),
                'generated_at': datetime.now().isoformat(),
                'summary': {
                    'toiletings': {'wet': 0, 'dry': 0, 'bm': 0},
                    'diapers': {'wet': 0, 'dry': 0, 'bm': 0},
                    'nap_duration_minutes': 0,
                    'meals': {'am_snack': 'None', 'lunch': 'None', 'pm_snack': 'None'},
                    'other_activities': []
                },
                'raw_activities': []
            }
        
        # Count toileting and diaper activities
        toileting_counts = self._count_activities_by_type(activities, 'toileting')
        diaper_counts = self._count_activities_by_type(activities, 'diaper')
        
        # Calculate nap duration
        nap_duration = self._calculate_nap_duration(activities)
        
        # Get meal status
        meal_status = self._get_meal_status(activities)
        
        # Get other activities
        other_activities = self._get_other_activities(activities)
        
        return {
            'date': date_str,
            'formatted_date': self._format_date(date_str),
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
    
    def _format_date(self, date_str: str) -> str:
        """Format date string"""
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            return date_obj.strftime('%A, %B %d, %Y')
        except:
            return date_str
    
    def _count_activities_by_type(self, activities: List[Dict], activity_type: str) -> Dict[str, int]:
        """Count activities by subtype"""
        filtered = [a for a in activities if a.get('activity_type') == activity_type]
        
        counts = {'wet': 0, 'dry': 0, 'bm': 0}
        
        for activity in filtered:
            subtype = activity.get('activity_subtype', '').lower()
            if 'wet' in subtype:
                counts['wet'] += 1
            if 'dry' in subtype:
                counts['dry'] += 1
            if 'bm' in subtype:
                counts['bm'] += 1
        
        return counts
    
    def _calculate_nap_duration(self, activities: List[Dict]) -> int:
        """Calculate nap duration in minutes"""
        nap_activities = [a for a in activities if a.get('activity_type') == 'nap']
        
        nap_start = None
        nap_end = None
        
        for activity in nap_activities:
            subtype = activity.get('activity_subtype', '').lower()
            if subtype == 'start':
                nap_start = activity.get('parsed_time')
            elif subtype == 'stop':
                nap_end = activity.get('parsed_time')
        
        if nap_start and nap_end and nap_start != "Unknown" and nap_end != "Unknown":
            return self._parse_time_duration(nap_start, nap_end)
        
        return 0
    
    def _parse_time_duration(self, start_time: str, end_time: str) -> int:
        """Parse time duration between start and end times"""
        try:
            start_mins = self._time_to_minutes(start_time)
            end_mins = self._time_to_minutes(end_time)
            return max(0, end_mins - start_mins)
        except:
            return 0
    
    def _time_to_minutes(self, time_str: str) -> int:
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
    
    def _get_meal_status(self, activities: List[Dict]) -> Dict[str, str]:
        """Get status of all meals"""
        meals = {
            'am_snack': 'None',
            'lunch': 'None', 
            'pm_snack': 'None'
        }
        
        meal_activities = [a for a in activities if a.get('activity_type') == 'meal']
        
        for activity in activities:
            activity_name = activity.get('activity_name', '').lower()
            subtype = activity.get('activity_subtype', '')
            
            if 'am snack' in activity_name:
                meals['am_snack'] = subtype
            elif 'lunch' in activity_name:
                meals['lunch'] = subtype
            elif 'pm snack' in activity_name:
                meals['pm_snack'] = subtype
        
        return meals
    
    def _get_other_activities(self, activities: List[Dict]) -> List[str]:
        """Get non-standard activities"""
        other_activities = []
        
        for activity in activities:
            if activity.get('activity_type') == 'other':
                activity_name = activity.get('activity_name', '')
                activity_subtype = activity.get('activity_subtype', '')
                if activity_subtype:
                    activity_str = f"{activity_name}: {activity_subtype}"
                else:
                    activity_str = activity_name
                
                if activity_str not in other_activities:
                    other_activities.append(activity_str)
        
        return other_activities
    
    def get_weekly_summary(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """Generate weekly summary from database"""
        activities = self.get_activities_by_date_range(start_date, end_date)
        
        # Group activities by date
        daily_summaries = {}
        for activity in activities:
            activity_date = activity['date']
            if activity_date not in daily_summaries:
                daily_summaries[activity_date] = []
            daily_summaries[activity_date].append(activity)
        
        # Generate summary for each day
        weekly_data = {}
        for date_str, day_activities in daily_summaries.items():
            daily_summary = self.generate_daily_summary_from_db(date_str)
            weekly_data[date_str] = daily_summary['summary']
        
        return {
            'start_date': start_date,
            'end_date': end_date,
            'generated_at': datetime.now().isoformat(),
            'daily_summaries': weekly_data,
            'total_activities': len(activities)
        }
    
    def check_message_processed(self, message_id: str) -> bool:
        """Check if a message has already been processed"""
        result = self.client.table('activities').select("id").eq('source_message_id', message_id).limit(1).execute()
        return len(result.data) > 0