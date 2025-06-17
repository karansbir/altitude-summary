#!/usr/bin/env python3
"""
Dashboard Query Functions
Provides analytics and dashboard data from the activities database
"""

from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional

try:
    from .database_client import DatabaseClient
except ImportError:
    from database_client import DatabaseClient

class DashboardQueries:
    """Advanced query functions for dashboard and analytics"""
    
    def __init__(self):
        self.db_client = DatabaseClient()
    
    def get_weekly_trends(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """Get weekly activity trends"""
        activities = self.db_client.get_activities_by_date_range(start_date, end_date)
        
        # Group by date
        daily_stats = {}
        for activity in activities:
            activity_date = activity['date']
            if activity_date not in daily_stats:
                daily_stats[activity_date] = {
                    'toileting': 0,
                    'diaper': 0,
                    'nap_sessions': 0,
                    'meals_eaten': 0,
                    'other_activities': 0
                }
            
            activity_type = activity['activity_type']
            if activity_type == 'toileting':
                daily_stats[activity_date]['toileting'] += 1
            elif activity_type == 'diaper':
                daily_stats[activity_date]['diaper'] += 1
            elif activity_type == 'nap':
                if activity.get('activity_subtype') == 'start':
                    daily_stats[activity_date]['nap_sessions'] += 1
            elif activity_type == 'meal':
                if activity.get('activity_subtype') in ['all', 'some']:
                    daily_stats[activity_date]['meals_eaten'] += 1
            elif activity_type == 'other':
                daily_stats[activity_date]['other_activities'] += 1
        
        return {
            'start_date': start_date,
            'end_date': end_date,
            'daily_stats': daily_stats,
            'averages': self._calculate_weekly_averages(daily_stats)
        }
    
    def _calculate_weekly_averages(self, daily_stats: Dict) -> Dict[str, float]:
        """Calculate weekly averages"""
        if not daily_stats:
            return {}
        
        totals = {
            'toileting': 0,
            'diaper': 0,
            'nap_sessions': 0,
            'meals_eaten': 0,
            'other_activities': 0
        }
        
        num_days = len(daily_stats)
        for day_stats in daily_stats.values():
            for key in totals:
                totals[key] += day_stats.get(key, 0)
        
        return {key: round(total / num_days, 1) for key, total in totals.items()}
    
    def get_nap_analysis(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """Analyze nap patterns"""
        activities = self.db_client.get_activities_by_date_range(start_date, end_date)
        nap_activities = [a for a in activities if a['activity_type'] == 'nap']
        
        # Group naps by date
        daily_naps = {}
        for activity in nap_activities:
            activity_date = activity['date']
            if activity_date not in daily_naps:
                daily_naps[activity_date] = {'starts': [], 'stops': []}
            
            if activity.get('activity_subtype') == 'start':
                daily_naps[activity_date]['starts'].append(activity['parsed_time'])
            elif activity.get('activity_subtype') == 'stop':
                daily_naps[activity_date]['stops'].append(activity['parsed_time'])
        
        # Calculate nap durations
        nap_durations = []
        nap_start_times = []
        
        for date_naps in daily_naps.values():
            starts = date_naps['starts']
            stops = date_naps['stops']
            
            for i in range(min(len(starts), len(stops))):
                duration = self._parse_time_duration(starts[i], stops[i])
                if duration > 0:
                    nap_durations.append(duration)
                    nap_start_times.append(starts[i])
        
        return {
            'total_naps': len(nap_durations),
            'average_duration_minutes': sum(nap_durations) / len(nap_durations) if nap_durations else 0,
            'longest_nap_minutes': max(nap_durations) if nap_durations else 0,
            'shortest_nap_minutes': min(nap_durations) if nap_durations else 0,
            'nap_durations': nap_durations,
            'common_nap_start_times': self._get_common_times(nap_start_times)
        }
    
    def get_meal_analysis(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """Analyze meal eating patterns"""
        activities = self.db_client.get_activities_by_date_range(start_date, end_date)
        meal_activities = [a for a in activities if a['activity_type'] == 'meal']
        
        meal_stats = {
            'am_snack': {'all': 0, 'some': 0, 'none': 0},
            'lunch': {'all': 0, 'some': 0, 'none': 0},
            'pm_snack': {'all': 0, 'some': 0, 'none': 0}
        }
        
        for activity in meal_activities:
            activity_name = activity.get('activity_name', '').lower()
            subtype = activity.get('activity_subtype', '').lower()
            
            if 'am snack' in activity_name and subtype in meal_stats['am_snack']:
                meal_stats['am_snack'][subtype] += 1
            elif 'lunch' in activity_name and subtype in meal_stats['lunch']:
                meal_stats['lunch'][subtype] += 1
            elif 'pm snack' in activity_name and subtype in meal_stats['pm_snack']:
                meal_stats['pm_snack'][subtype] += 1
        
        # Calculate percentages
        meal_percentages = {}
        for meal, counts in meal_stats.items():
            total = sum(counts.values())
            if total > 0:
                meal_percentages[meal] = {
                    status: round((count / total) * 100, 1)
                    for status, count in counts.items()
                }
            else:
                meal_percentages[meal] = {'all': 0, 'some': 0, 'none': 0}
        
        return {
            'meal_counts': meal_stats,
            'meal_percentages': meal_percentages,
            'total_meals_tracked': sum(sum(counts.values()) for counts in meal_stats.values())
        }
    
    def get_activity_timeline(self, target_date: str) -> List[Dict[str, Any]]:
        """Get chronological timeline of activities for a specific date"""
        activities = self.db_client.get_daily_activities(target_date)
        
        # Convert to timeline format
        timeline = []
        for activity in activities:
            timeline.append({
                'time': activity.get('parsed_time', 'Unknown'),
                'activity': activity.get('activity_name', ''),
                'type': activity.get('activity_subtype', ''),
                'category': activity.get('activity_type', ''),
                'timestamp': activity.get('timestamp', '')
            })
        
        # Sort by parsed time
        timeline.sort(key=lambda x: self._time_to_minutes(x['time']) if x['time'] != 'Unknown' else 0)
        
        return timeline
    
    def get_monthly_summary(self, year: int, month: int) -> Dict[str, Any]:
        """Get monthly summary statistics"""
        start_date = f"{year:04d}-{month:02d}-01"
        
        # Calculate end date (last day of month)
        if month == 12:
            end_date = f"{year+1:04d}-01-01"
        else:
            end_date = f"{year:04d}-{month+1:02d}-01"
        
        # Get date range (subtract 1 day from end_date for inclusive range)
        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d') - timedelta(days=1)
        end_date = end_date_obj.strftime('%Y-%m-%d')
        
        activities = self.db_client.get_activities_by_date_range(start_date, end_date)
        
        # Group by activity type
        type_counts = {}
        daily_activity_counts = {}
        
        for activity in activities:
            activity_type = activity['activity_type']
            activity_date = activity['date']
            
            # Count by type
            type_counts[activity_type] = type_counts.get(activity_type, 0) + 1
            
            # Count by date
            if activity_date not in daily_activity_counts:
                daily_activity_counts[activity_date] = 0
            daily_activity_counts[activity_date] += 1
        
        return {
            'year': year,
            'month': month,
            'total_activities': len(activities),
            'activity_type_counts': type_counts,
            'daily_activity_counts': daily_activity_counts,
            'busiest_day': max(daily_activity_counts.items(), key=lambda x: x[1]) if daily_activity_counts else None,
            'average_daily_activities': sum(daily_activity_counts.values()) / len(daily_activity_counts) if daily_activity_counts else 0
        }
    
    def search_activities(self, query: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[Dict]:
        """Search activities by text content"""
        if start_date and end_date:
            activities = self.db_client.get_activities_by_date_range(start_date, end_date)
        else:
            # Get recent activities if no date range specified
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            activities = self.db_client.get_activities_by_date_range(start_date, end_date)
        
        # Filter by query
        query_lower = query.lower()
        matching_activities = []
        
        for activity in activities:
            # Search in activity name, type, subtype, and raw content
            searchable_text = ' '.join([
                activity.get('activity_name', ''),
                activity.get('activity_type', ''),
                activity.get('activity_subtype', ''),
                activity.get('raw_content', '')
            ]).lower()
            
            if query_lower in searchable_text:
                matching_activities.append(activity)
        
        return matching_activities
    
    def _get_common_times(self, times: List[str]) -> List[str]:
        """Get most common times from a list"""
        time_counts = {}
        for time_str in times:
            time_counts[time_str] = time_counts.get(time_str, 0) + 1
        
        # Return top 3 most common times
        sorted_times = sorted(time_counts.items(), key=lambda x: x[1], reverse=True)
        return [time for time, count in sorted_times[:3]]
    
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