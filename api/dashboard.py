#!/usr/bin/env python3
"""
Dashboard API Endpoint
Provides dashboard and analytics data from the activities database
"""

from http.server import BaseHTTPRequestHandler
import json
import os
import sys
from datetime import datetime, timedelta
from urllib.parse import urlparse, parse_qs

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from dashboard_queries import DashboardQueries

class handler(BaseHTTPRequestHandler):
    def _check_auth(self):
        """Simple authentication check"""
        # For development, allow all requests
        # In production, you might want to add API key authentication
        return True
    
    def do_GET(self):
        """Handle GET requests for dashboard data"""
        try:
            if not self._check_auth():
                self.send_response(401)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'Unauthorized'}).encode())
                return
            
            # Parse URL and query parameters
            parsed_url = urlparse(self.path)
            query_params = parse_qs(parsed_url.query)
            
            # Get endpoint from path
            path_parts = parsed_url.path.strip('/').split('/')
            endpoint = path_parts[-1] if path_parts else 'dashboard'
            
            # Initialize dashboard queries
            dashboard = DashboardQueries()
            
            # Route to appropriate handler
            if endpoint == 'weekly-trends':
                result = self._handle_weekly_trends(dashboard, query_params)
            elif endpoint == 'nap-analysis':
                result = self._handle_nap_analysis(dashboard, query_params)
            elif endpoint == 'meal-analysis':
                result = self._handle_meal_analysis(dashboard, query_params)
            elif endpoint == 'timeline':
                result = self._handle_timeline(dashboard, query_params)
            elif endpoint == 'monthly-summary':
                result = self._handle_monthly_summary(dashboard, query_params)
            elif endpoint == 'search':
                result = self._handle_search(dashboard, query_params)
            else:
                result = self._handle_default_dashboard(dashboard, query_params)
            
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
    
    def _handle_weekly_trends(self, dashboard: DashboardQueries, params: dict) -> dict:
        """Handle weekly trends request"""
        end_date = self._get_param(params, 'end_date', datetime.now().strftime('%Y-%m-%d'))
        start_date = self._get_param(params, 'start_date', 
                                   (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d'))
        
        return dashboard.get_weekly_trends(start_date, end_date)
    
    def _handle_nap_analysis(self, dashboard: DashboardQueries, params: dict) -> dict:
        """Handle nap analysis request"""
        end_date = self._get_param(params, 'end_date', datetime.now().strftime('%Y-%m-%d'))
        start_date = self._get_param(params, 'start_date', 
                                   (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
        
        return dashboard.get_nap_analysis(start_date, end_date)
    
    def _handle_meal_analysis(self, dashboard: DashboardQueries, params: dict) -> dict:
        """Handle meal analysis request"""
        end_date = self._get_param(params, 'end_date', datetime.now().strftime('%Y-%m-%d'))
        start_date = self._get_param(params, 'start_date', 
                                   (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
        
        return dashboard.get_meal_analysis(start_date, end_date)
    
    def _handle_timeline(self, dashboard: DashboardQueries, params: dict) -> dict:
        """Handle activity timeline request"""
        target_date = self._get_param(params, 'date', datetime.now().strftime('%Y-%m-%d'))
        
        timeline = dashboard.get_activity_timeline(target_date)
        return {
            'date': target_date,
            'timeline': timeline,
            'total_activities': len(timeline)
        }
    
    def _handle_monthly_summary(self, dashboard: DashboardQueries, params: dict) -> dict:
        """Handle monthly summary request"""
        now = datetime.now()
        year = int(self._get_param(params, 'year', str(now.year)))
        month = int(self._get_param(params, 'month', str(now.month)))
        
        return dashboard.get_monthly_summary(year, month)
    
    def _handle_search(self, dashboard: DashboardQueries, params: dict) -> dict:
        """Handle activity search request"""
        query = self._get_param(params, 'q', '')
        start_date = self._get_param(params, 'start_date', None)
        end_date = self._get_param(params, 'end_date', None)
        
        if not query:
            return {'error': 'Query parameter "q" is required'}
        
        results = dashboard.search_activities(query, start_date, end_date)
        return {
            'query': query,
            'results': results,
            'total_matches': len(results)
        }
    
    def _handle_default_dashboard(self, dashboard: DashboardQueries, params: dict) -> dict:
        """Handle default dashboard request with summary data"""
        # Get recent data for overview
        end_date = datetime.now().strftime('%Y-%m-%d')
        week_start = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        month_start = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        # Get various summaries
        weekly_trends = dashboard.get_weekly_trends(week_start, end_date)
        nap_analysis = dashboard.get_nap_analysis(month_start, end_date)
        meal_analysis = dashboard.get_meal_analysis(month_start, end_date)
        today_timeline = dashboard.get_activity_timeline(end_date)
        
        now = datetime.now()
        monthly_summary = dashboard.get_monthly_summary(now.year, now.month)
        
        return {
            'generated_at': datetime.now().isoformat(),
            'overview': {
                'today_activities': len(today_timeline),
                'week_averages': weekly_trends.get('averages', {}),
                'month_total_activities': monthly_summary.get('total_activities', 0),
                'average_nap_duration': nap_analysis.get('average_duration_minutes', 0)
            },
            'weekly_trends': weekly_trends,
            'nap_analysis': nap_analysis,
            'meal_analysis': meal_analysis,
            'today_timeline': today_timeline[:10],  # Limit to 10 most recent
            'monthly_summary': monthly_summary
        }
    
    def _get_param(self, params: dict, key: str, default: str = None) -> str:
        """Get parameter value from query params"""
        if key in params and params[key]:
            return params[key][0]
        return default

# For local testing
if __name__ == "__main__":
    print("Testing Dashboard API...")
    dashboard = DashboardQueries()
    
    # Test weekly trends
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    
    try:
        result = dashboard.get_weekly_trends(start_date, end_date)
        print("Weekly trends:", json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error testing dashboard: {e}")