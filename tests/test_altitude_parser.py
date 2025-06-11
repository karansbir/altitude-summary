#!/usr/bin/env python3
"""
Tests for Altitude Parser
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from altitude_parser import AltitudeParser

def test_extract_toileting_activities():
    parser = AltitudeParser()
    content = "Toileting: Wet Kavitha Baradol - posted 10:00 AM"
    activities = parser.extract_activities_from_message({'snippet': content})
    
    assert len(activities) == 1
    assert activities[0]['activity'] == 'Toileting'
    assert activities[0]['type'] == 'Wet'
    assert activities[0]['time'] == '10:00 AM'

def test_extract_multiple_activities():
    parser = AltitudeParser()
    content = "Lunch: All Kavitha - posted 12:14 PM Toileting: Wet Kavitha - posted 12:15 PM"
    activities = parser.extract_activities_from_message({'snippet': content})
    
    assert len(activities) == 2
    assert any(a['activity'] == 'Lunch' for a in activities)
    assert any(a['activity'] == 'Toileting' for a in activities)

def test_count_activities_by_type():
    parser = AltitudeParser()
    activities = [
        {'activity': 'Toileting', 'type': 'Wet'},
        {'activity': 'Toileting', 'type': 'Dry'},
        {'activity': 'Toileting', 'type': 'Wet'},
    ]
    
    counts = parser.count_activities_by_type(activities, 'Toileting')
    assert counts['wet'] == 2
    assert counts['dry'] == 1
    assert counts['bm'] == 0

def test_calculate_nap_duration():
    parser = AltitudeParser()
    activities = [
        {'activity': 'Nap', 'type': 'Start', 'time': '12:46 PM'},
        {'activity': 'Nap', 'type': 'Stop', 'time': '02:53 PM'},
    ]
    
    duration = parser.calculate_nap_duration(activities)
    assert duration == 127  # 2h 7m = 127 minutes

if __name__ == "__main__":
    test_extract_toileting_activities()
    test_extract_multiple_activities()
    test_count_activities_by_type()
    test_calculate_nap_duration()
    print("All tests passed! ✅")
