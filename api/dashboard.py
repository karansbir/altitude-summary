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
        """Handle GET requests for dashboard data or UI"""
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
            
            # Check if HTML UI is requested
            accept_header = self.headers.get('Accept', '')
            wants_html = ('text/html' in accept_header or 
                         query_params.get('format', [''])[0] == 'html' or
                         parsed_url.path == '/api/dashboard' or
                         parsed_url.path == '/api/dashboard/')
            
            # Get endpoint from path
            path_parts = parsed_url.path.strip('/').split('/')
            endpoint = path_parts[-1] if path_parts else 'dashboard'
            
            # Initialize dashboard queries
            dashboard = DashboardQueries()
            
            # Serve HTML UI for main dashboard
            if wants_html and endpoint == 'dashboard':
                html_content = self._generate_dashboard_html(dashboard)
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(html_content.encode())
                return
            
            # Route to appropriate JSON API handler
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
            elif endpoint == 'available-dates':
                result = self._handle_available_dates(dashboard, query_params)
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
    
    def _handle_available_dates(self, dashboard: DashboardQueries, params: dict) -> dict:
        """Handle available dates request"""
        dates = dashboard.get_available_dates()
        return {
            'available_dates': dates,
            'total_dates': len(dates)
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
    
    def _generate_dashboard_html(self, dashboard: DashboardQueries) -> str:
        """Generate comprehensive HTML dashboard"""
        # Get URL parameters
        from urllib.parse import urlparse, parse_qs
        parsed_url = urlparse(self.path)
        query_params = parse_qs(parsed_url.query)
        
        # Get selected date from query parameter, default to today
        selected_date = self._get_param(query_params, 'date', datetime.now().strftime('%Y-%m-%d'))
        
        # Validate that the selected date has data
        available_dates = dashboard.get_available_dates()
        if selected_date not in available_dates and available_dates:
            selected_date = available_dates[0]  # Use most recent date with data
        
        week_start = (datetime.strptime(selected_date, '%Y-%m-%d') - timedelta(days=7)).strftime('%Y-%m-%d')
        
        # Get data for selected date
        today_timeline = dashboard.get_activity_timeline(selected_date)
        today_summary = dashboard.get_daily_summary(selected_date)
        
        # Get week data
        weekly_trends = dashboard.get_weekly_trends(week_start, selected_date)
        
        # Get lifetime data (all time)
        lifetime_summary = dashboard.get_lifetime_summary()
        
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Altitude Summary Dashboard</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        
        h1 {{
            color: white;
            text-align: center;
            margin-bottom: 10px;
            font-size: 2.5rem;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }}
        
        .date-picker-container {{
            text-align: center;
            margin-bottom: 30px;
        }}
        
        .date-picker {{
            background: white;
            border: 2px solid #667eea;
            border-radius: 8px;
            padding: 8px 12px;
            font-size: 1rem;
            color: #2c3e50;
            outline: none;
            transition: border-color 0.2s ease;
        }}
        
        .date-picker:focus {{
            border-color: #5a6fd8;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.2);
        }}
        
        .date-picker-label {{
            color: white;
            font-size: 1rem;
            margin-right: 10px;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
        }}
        
        .dashboard-section {{
            background: white;
            border-radius: 15px;
            padding: 25px;
            margin-bottom: 25px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.15);
            transition: transform 0.2s ease;
        }}
        
        .dashboard-section:hover {{
            transform: translateY(-2px);
        }}
        
        .section-title {{
            color: #2c3e50;
            font-size: 1.5rem;
            margin-bottom: 20px;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }}
        
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }}
        
        .metric-card {{
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            border-radius: 10px;
            padding: 20px;
            text-align: center;
            border-left: 4px solid #667eea;
        }}
        
        .metric-value {{
            font-size: 2rem;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 5px;
        }}
        
        .metric-label {{
            color: #6c757d;
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .activity-timeline {{
            max-height: 300px;
            overflow-y: auto;
            border: 1px solid #dee2e6;
            border-radius: 8px;
        }}
        
        .timeline-item {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 15px;
            border-bottom: 1px solid #f8f9fa;
        }}
        
        .timeline-item:last-child {{
            border-bottom: none;
        }}
        
        .timeline-time {{
            font-weight: 600;
            color: #667eea;
            min-width: 80px;
        }}
        
        .timeline-activity {{
            flex: 1;
            margin-left: 15px;
        }}
        
        .timeline-type {{
            color: #6c757d;
            font-size: 0.85rem;
        }}
        
        .meal-status {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 600;
            text-transform: uppercase;
        }}
        
        .meal-all {{ background: #d4edda; color: #155724; }}
        .meal-some {{ background: #fff3cd; color: #856404; }}
        .meal-none {{ background: #f8d7da; color: #721c24; }}
        
        .stats-row {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
            padding: 10px 0;
            border-bottom: 1px solid #f8f9fa;
        }}
        
        .stats-row:last-child {{
            border-bottom: none;
            margin-bottom: 0;
        }}
        
        .nap-duration {{
            font-size: 1.2rem;
            font-weight: 600;
            color: #667eea;
        }}
        
        .other-activities {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }}
        
        .other-activity {{
            background: #667eea;
            color: white;
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 0.8rem;
        }}
        
        .refresh-btn {{
            background: #667eea;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 25px;
            cursor: pointer;
            font-size: 0.9rem;
            margin-top: 20px;
            transition: background 0.2s ease;
        }}
        
        .refresh-btn:hover {{
            background: #5a6fd8;
        }}
        
        .last-updated {{
            text-align: center;
            color: #6c757d;
            font-size: 0.85rem;
            margin-top: 20px;
        }}
        
        @media (max-width: 768px) {{
            .metrics-grid {{
                grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            }}
            
            h1 {{
                font-size: 2rem;
            }}
            
            .dashboard-section {{
                padding: 20px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Altitude Summary Dashboard</h1>
        
        <!-- Date Picker -->
        <div class="date-picker-container">
            <label class="date-picker-label" for="datePicker">Select Date:</label>
            <select id="datePicker" class="date-picker" onchange="changeDate()">
                {self._generate_date_options(available_dates, selected_date)}
            </select>
        </div>
        
        <!-- Today's Summary -->
        <div class="dashboard-section">
            <h2 class="section-title">Summary for {datetime.strptime(selected_date, '%Y-%m-%d').strftime('%A, %B %d, %Y')}</h2>
            
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-value">{today_summary.get('toileting_counts', {}).get('wet', 0)}</div>
                    <div class="metric-label">Wet Toiletings</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{today_summary.get('toileting_counts', {}).get('dry', 0)}</div>
                    <div class="metric-label">Dry Toiletings</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{today_summary.get('toileting_counts', {}).get('bm', 0)}</div>
                    <div class="metric-label">BM Toiletings</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{today_summary.get('diaper_counts', {}).get('wet', 0)}</div>
                    <div class="metric-label">Wet Diapers</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{today_summary.get('diaper_counts', {}).get('dry', 0)}</div>
                    <div class="metric-label">Dry Diapers</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{today_summary.get('diaper_counts', {}).get('bm', 0)}</div>
                    <div class="metric-label">BM Diapers</div>
                </div>
            </div>
            
            <div class="stats-row">
                <span><strong>Nap Duration:</strong></span>
                <span class="nap-duration">{self._format_nap_duration(today_summary.get('nap_duration_minutes', 0))}</span>
            </div>
            
            <div class="stats-row">
                <span><strong>AM Snack:</strong></span>
                <span class="meal-status meal-{today_summary.get('meals', {}).get('am_snack', 'none').lower()}">{today_summary.get('meals', {}).get('am_snack', 'None')}</span>
            </div>
            
            <div class="stats-row">
                <span><strong>Lunch:</strong></span>
                <span class="meal-status meal-{today_summary.get('meals', {}).get('lunch', 'none').lower()}">{today_summary.get('meals', {}).get('lunch', 'None')}</span>
            </div>
            
            <div class="stats-row">
                <span><strong>PM Snack:</strong></span>
                <span class="meal-status meal-{today_summary.get('meals', {}).get('pm_snack', 'none').lower()}">{today_summary.get('meals', {}).get('pm_snack', 'None')}</span>
            </div>
            
            <div class="stats-row">
                <span><strong>Other Activities:</strong></span>
                <div class="other-activities">
                    {self._format_other_activities(today_summary.get('other_activities', []))}
                </div>
            </div>
            
            <h3 style="margin-top: 25px; color: #2c3e50;">Activity Timeline</h3>
            <div class="activity-timeline">
                {self._format_timeline(today_timeline)}
            </div>
        </div>
        
        <!-- Week Summary -->
        <div class="dashboard-section">
            <h2 class="section-title">Week Summary</h2>
            
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-value">{weekly_trends.get('averages', {}).get('toileting_per_day', 0):.1f}</div>
                    <div class="metric-label">Avg Toiletings/Day</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{weekly_trends.get('averages', {}).get('diaper_per_day', 0):.1f}</div>
                    <div class="metric-label">Avg Diapers/Day</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{weekly_trends.get('averages', {}).get('nap_duration_minutes', 0):.0f}</div>
                    <div class="metric-label">Avg Nap (mins)</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{weekly_trends.get('averages', {}).get('activities_per_day', 0):.1f}</div>
                    <div class="metric-label">Avg Activities/Day</div>
                </div>
            </div>
            
            <h3 style="margin-top: 20px; color: #2c3e50;">Daily Breakdown</h3>
            <div class="activity-timeline">
                {self._format_weekly_breakdown(weekly_trends.get('daily_breakdown', []))}
            </div>
        </div>
        
        <!-- Lifetime Summary -->
        <div class="dashboard-section">
            <h2 class="section-title">Lifetime Summary</h2>
            
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-value">{lifetime_summary.get('total_toileting', 0)}</div>
                    <div class="metric-label">Total Toiletings</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{lifetime_summary.get('total_diapers', 0)}</div>
                    <div class="metric-label">Total Diapers</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{lifetime_summary.get('total_naps', 0)}</div>
                    <div class="metric-label">Total Naps</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{lifetime_summary.get('days_tracked', 0)}</div>
                    <div class="metric-label">Days Tracked</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{lifetime_summary.get('total_activities', 0)}</div>
                    <div class="metric-label">Total Activities</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{lifetime_summary.get('unique_other_activities', 0)}</div>
                    <div class="metric-label">Unique Other Activities</div>
                </div>
            </div>
            
            <div class="stats-row">
                <span><strong>Tracking Since:</strong></span>
                <span>{lifetime_summary.get('first_activity_date', 'N/A')}</span>
            </div>
            
            <div class="stats-row">
                <span><strong>Most Recent Activity:</strong></span>
                <span>{lifetime_summary.get('last_activity_date', 'N/A')}</span>
            </div>
            
            <div class="stats-row">
                <span><strong>Average Nap Duration:</strong></span>
                <span class="nap-duration">{self._format_nap_duration(lifetime_summary.get('avg_nap_duration', 0))}</span>
            </div>
        </div>
        
        <div class="last-updated">
            Last updated: {datetime.now().strftime('%I:%M %p on %B %d, %Y')}
            <br>
            <button class="refresh-btn" onclick="window.location.reload()">Refresh Dashboard</button>
        </div>
    </div>
    
    <script>
        function changeDate() {{
            const datePicker = document.getElementById('datePicker');
            const selectedDate = datePicker.value;
            
            // Reload page with new date parameter
            const url = new URL(window.location);
            url.searchParams.set('date', selectedDate);
            window.location.href = url.toString();
        }}
    </script>
</body>
</html>"""
    
    def _format_nap_duration(self, minutes):
        """Format nap duration in a readable way"""
        if minutes == 0:
            return "No nap"
        hours = minutes // 60
        mins = minutes % 60
        if hours > 0:
            return f"{hours}h {mins}m"
        return f"{mins} mins"
    
    def _format_other_activities(self, activities):
        """Format other activities as HTML tags"""
        if not activities:
            return '<span class="other-activity">None today</span>'
        
        html = []
        for activity in activities[:10]:  # Limit to 10 activities
            html.append(f'<span class="other-activity">{activity}</span>')
        
        if len(activities) > 10:
            html.append(f'<span class="other-activity">+{len(activities) - 10} more</span>')
        
        return ''.join(html)
    
    def _format_timeline(self, timeline):
        """Format timeline as HTML"""
        if not timeline:
            return '<div class="timeline-item"><span>No activities recorded today</span></div>'
        
        html = []
        for item in timeline[:20]:  # Limit to 20 most recent
            html.append(f'''
                <div class="timeline-item">
                    <span class="timeline-time">{item.get('parsed_time', 'Unknown')}</span>
                    <div class="timeline-activity">
                        <strong>{item.get('activity_name', 'Unknown')}</strong>
                        {f'<div class="timeline-type">{item.get("activity_subtype", "")}</div>' if item.get('activity_subtype') else ''}
                    </div>
                </div>
            ''')
        
        return ''.join(html)
    
    def _format_weekly_breakdown(self, breakdown):
        """Format weekly breakdown as HTML"""
        if not breakdown:
            return '<div class="timeline-item"><span>No weekly data available</span></div>'
        
        html = []
        for day in breakdown:
            date_obj = datetime.strptime(day['date'], '%Y-%m-%d')
            day_name = date_obj.strftime('%A, %B %d')
            
            html.append(f'''
                <div class="timeline-item">
                    <span class="timeline-time">{day_name}</span>
                    <div class="timeline-activity">
                        <strong>{day.get('total_activities', 0)} activities</strong>
                        <div class="timeline-type">
                            Toileting: {day.get('toileting_count', 0)} | 
                            Diapers: {day.get('diaper_count', 0)} | 
                            Nap: {self._format_nap_duration(day.get('nap_duration', 0))}
                        </div>
                    </div>
                </div>
            ''')
        
        return ''.join(html)
    
    def _generate_date_options(self, available_dates: list, selected_date: str) -> str:
        """Generate HTML options for date picker"""
        if not available_dates:
            return '<option value="">No dates available</option>'
        
        options = []
        for date in available_dates:
            try:
                # Format date for display
                date_obj = datetime.strptime(date, '%Y-%m-%d')
                display_date = date_obj.strftime('%A, %B %d, %Y')
                
                # Mark as selected if this is the current date
                selected = 'selected' if date == selected_date else ''
                
                options.append(f'<option value="{date}" {selected}>{display_date}</option>')
            except:
                # Fallback for invalid dates
                selected = 'selected' if date == selected_date else ''
                options.append(f'<option value="{date}" {selected}>{date}</option>')
        
        return '\n'.join(options)

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