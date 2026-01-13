"""
Service to manage time, dates, timezones
"""

from datetime import datetime, timedelta
import pytz
from typing import Optional

class TimeService:
    
    @staticmethod
    def get_current_time(timezone: str = "UTC") -> dict:
        """
        Get current time in a specified timezone
        
        Args:
            timezone: Timezone (e.g., "Europe/Paris", "America/New_York", "UTC")
        
        Returns:
            Dict with formatted time, timestamp, day, etc.
        """
        try:
            tz = pytz.timezone(timezone)
            now = datetime.now(tz)
            
            return {
                "timezone": timezone,
                "time": now.strftime("%H:%M:%S"),
                "date": now.strftime("%Y-%m-%d"),
                "datetime": now.strftime("%Y-%m-%d %H:%M:%S"),
                "day_name": now.strftime("%A"),
                "month_name": now.strftime("%B"),
                "timestamp": int(now.timestamp()),
                "iso": now.isoformat()
            }
        except Exception as e:
            return {"error": f"Invalid timezone or error: {str(e)}"}
    
    @staticmethod
    def compare_timezones(tz1: str = "Europe/Paris", tz2: str = "America/New_York") -> dict:
        """
        Compares time between two timezones
        """
        time1 = TimeService.get_current_time(tz1)
        time2 = TimeService.get_current_time(tz2)
        
        if "error" in time1 or "error" in time2:
            return {"error": "Invalid timezone"}
        
        # Calculate time difference
        dt1 = datetime.fromtimestamp(time1["timestamp"], pytz.timezone(tz1))
        dt2 = datetime.fromtimestamp(time2["timestamp"], pytz.timezone(tz2))
        offset = (dt1.utcoffset() - dt2.utcoffset()).total_seconds() / 3600
        
        return {
            tz1: time1,
            tz2: time2,
            "time_difference_hours": offset
        }
    
    @staticmethod
    def time_until(target_date: str) -> dict:
        """
        Calculates the time remaining until a date
        
        Args:
            target_date: Target date in "YYYY-MM-DD" or "YYYY-MM-DD HH:MM" format
        """
        try:
            # Parse target date
            if len(target_date) == 10:  # YYYY-MM-DD
                target = datetime.strptime(target_date, "%Y-%m-%d")
            else:  # YYYY-MM-DD HH:MM
                target = datetime.strptime(target_date, "%Y-%m-%d %H:%M")
            
            now = datetime.now()
            delta = target - now
            
            if delta.total_seconds() < 0:
                return {
                    "passed": True,
                    "message": f"This date has already passed {abs(delta.days)} days ago"
                }
            
            days = delta.days
            hours, remainder = divmod(delta.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            
            return {
                "target_date": target_date,
                "days": days,
                "hours": hours,
                "minutes": minutes,
                "total_seconds": int(delta.total_seconds()),
                "formatted": f"{days}d {hours}h {minutes}m"
            }
        except Exception as e:
            return {"error": f"Invalid date format: {str(e)}"}
    
    @staticmethod
    def list_common_timezones() -> list:
        """List of common timezones"""
        return [
            "UTC",
            "Europe/Paris",
            "Europe/London",
            "America/New_York",
            "America/Los_Angeles",
            "America/Chicago",
            "Asia/Tokyo",
            "Asia/Shanghai",
            "Asia/Dubai",
            "Australia/Sydney",
            "Pacific/Auckland"
        ]
