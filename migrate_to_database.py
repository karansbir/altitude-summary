#!/usr/bin/env python3
"""
Migration Script: Regex-based to Database-driven
Migrates existing functionality to use Supabase database
"""

import os
import sys
import json
from datetime import datetime, timedelta
from typing import List, Dict
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from gmail_client import GmailClient
from altitude_parser import AltitudeParser
from database_client import DatabaseClient

def migrate_historical_data(days_back: int = 30):
    """
    Migrate historical email data to database
    """
    print(f"🔄 Starting migration of last {days_back} days of data...")
    
    try:
        # Initialize clients
        gmail = GmailClient()
        parser = AltitudeParser(use_database=True)
        
        # Get date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        migrated_count = 0
        error_count = 0
        
        # Process each day
        for i in range(days_back):
            current_date = start_date + timedelta(days=i)
            date_str = current_date.strftime('%Y-%m-%d')
            
            print(f"📅 Processing {date_str}...")
            
            try:
                # Get messages for this date
                messages = gmail.get_altitude_messages(date_str)
                
                if messages:
                    # Process messages (will store in database)
                    result = parser.process_messages(messages, date_str)
                    activities_count = len(result.get('raw_activities', []))
                    
                    if activities_count > 0:
                        print(f"   ✅ Migrated {activities_count} activities")
                        migrated_count += activities_count
                    else:
                        print(f"   ⚠️  No activities found")
                else:
                    print(f"   📭 No messages found")
                    
            except Exception as e:
                print(f"   ❌ Error processing {date_str}: {e}")
                error_count += 1
        
        print(f"\n🎉 Migration completed!")
        print(f"   📊 Total activities migrated: {migrated_count}")
        print(f"   ❌ Errors encountered: {error_count}")
        
        return migrated_count, error_count
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return 0, 1

def test_database_connection():
    """Test database connection and setup"""
    print("🔧 Testing database connection...")
    
    try:
        db_client = DatabaseClient()
        print("   ✅ Database connection successful")
        
        # Test query
        today = datetime.now().strftime('%Y-%m-%d')
        activities = db_client.get_daily_activities(today)
        print(f"   📊 Found {len(activities)} activities for today")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Database connection failed: {e}")
        print("\n💡 Make sure you have:")
        print("   1. Created a Supabase project")
        print("   2. Run the database_setup.sql script")
        print("   3. Set SUPABASE_URL and SUPABASE_ANON_KEY environment variables")
        return False

def setup_environment_variables():
    """Guide user through setting up environment variables"""
    print("\n🔧 Environment Variables Setup")
    print("=" * 50)
    
    required_vars = {
        'SUPABASE_URL': 'Your Supabase project URL (https://xxx.supabase.co)',
        'SUPABASE_ANON_KEY': 'Your Supabase anon/public key'
    }
    
    missing_vars = []
    
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {'*' * 20} (set)")
        else:
            print(f"❌ {var}: Not set")
            print(f"   📝 {description}")
            missing_vars.append(var)
    
    if missing_vars:
        print(f"\n⚠️  Missing {len(missing_vars)} required environment variables")
        print("Add these to your Vercel environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        return False
    else:
        print("\n✅ All required environment variables are set!")
        return True

def create_sample_dashboard_query():
    """Create and run a sample dashboard query"""
    print("\n📊 Testing dashboard queries...")
    
    try:
        from dashboard_queries import DashboardQueries
        
        dashboard = DashboardQueries()
        
        # Test weekly trends
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        
        trends = dashboard.get_weekly_trends(start_date, end_date)
        print(f"   📈 Weekly trends: {len(trends['daily_stats'])} days of data")
        
        # Test timeline for today
        timeline = dashboard.get_activity_timeline(end_date)
        print(f"   ⏰ Today's timeline: {len(timeline)} activities")
        
        print("   ✅ Dashboard queries working correctly")
        return True
        
    except Exception as e:
        print(f"   ❌ Dashboard query failed: {e}")
        return False

def main():
    """Main migration function"""
    print("🚀 Altitude Summary: Database Migration Tool")
    print("=" * 50)
    
    # Step 1: Check environment variables
    if not setup_environment_variables():
        print("\n❌ Please set up environment variables first")
        return
    
    # Step 2: Test database connection
    if not test_database_connection():
        print("\n❌ Please check database setup")
        return
    
    # Step 3: Ask user about migration
    print("\n📥 Historical Data Migration")
    print("This will migrate existing email data to the database.")
    
    migrate = input("Do you want to migrate historical data? (y/n): ").lower().strip()
    
    if migrate == 'y':
        days = input("How many days back to migrate? (default: 30): ").strip()
        days = int(days) if days.isdigit() else 30
        
        migrated, errors = migrate_historical_data(days)
        
        if migrated > 0:
            print("\n🎉 Migration successful!")
            
            # Step 4: Test dashboard queries
            create_sample_dashboard_query()
            
            print("\n✅ Database migration completed successfully!")
            print("\n🔧 Next steps:")
            print("   1. Deploy to Vercel with new environment variables")
            print("   2. Test the dashboard API at /api/dashboard")
            print("   3. The system will now use database for all operations")
        else:
            print("\n⚠️  No data was migrated. Check your Gmail configuration.")
    else:
        print("\n⏭️  Skipping historical data migration")
        print("   The system will work with new data going forward")

if __name__ == "__main__":
    main()