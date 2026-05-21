"""
Digital clock utility for displaying current time in multiple time zones.
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, List, Tuple
import pytz


class TimezoneInfo:
    """Information about a specific timezone."""
    
    def __init__(self, name: str, timezone_str: str, offset: str = None):
        """
        Initialize timezone info.
        
        Args:
            name: Display name (e.g., "New York", "London")
            timezone_str: Timezone string (e.g., "America/New_York")
            offset: Optional UTC offset string
        """
        self.name = name
        self.timezone_str = timezone_str
        self.tz = pytz.timezone(timezone_str)
        self.offset = offset or self._calculate_offset()
    
    def _calculate_offset(self) -> str:
        """Calculate UTC offset for this timezone."""
        now = datetime.now(self.tz)
        offset_seconds = now.utcoffset().total_seconds()
        hours, remainder = divmod(abs(int(offset_seconds)), 3600)
        minutes = remainder // 60
        sign = '+' if offset_seconds >= 0 else '-'
        return f"UTC {sign}{hours:02d}:{minutes:02d}"


class DigitalClock:
    """
    Digital clock that displays current time in multiple time zones.
    """
    
    # Common timezones preset
    COMMON_TIMEZONES = {
        'New York': 'America/New_York',
        'London': 'Europe/London',
        'Paris': 'Europe/Paris',
        'Tokyo': 'Asia/Tokyo',
        'Sydney': 'Australia/Sydney',
        'Dubai': 'Asia/Dubai',
        'Singapore': 'Asia/Singapore',
        'Hong Kong': 'Asia/Hong_Kong',
        'Mumbai': 'Asia/Kolkata',
        'Toronto': 'America/Toronto',
        'Mexico City': 'America/Mexico_City',
        'São Paulo': 'America/Sao_Paulo',
        'Los Angeles': 'America/Los_Angeles',
        'Chicago': 'America/Chicago',
    }
    
    def __init__(self):
        """Initialize the clock with common timezones."""
        self.timezones: Dict[str, TimezoneInfo] = {}
        self.add_timezones_from_preset()
    
    def add_timezone(self, name: str, timezone_str: str) -> None:
        """
        Add a timezone to the clock.
        
        Args:
            name: Display name for the timezone
            timezone_str: Timezone string (e.g., "America/New_York")
        
        Raises:
            ValueError: If timezone string is invalid
        """
        try:
            self.timezones[name] = TimezoneInfo(name, timezone_str)
        except pytz.exceptions.UnknownTimeZoneError:
            raise ValueError(f"Unknown timezone: {timezone_str}\")\n    \n    def remove_timezone(self, name: str) -> None:\n        \"\"\"\n        Remove a timezone from the clock.\n        \n        Args:\n            name: Display name of timezone to remove\n        \"\"\"\n        if name in self.timezones:\n            del self.timezones[name]\n    \n    def add_timezones_from_preset(self) -> None:\n        \"\"\"\n        Add all common timezones from preset.\n        \"\"\"\n        for name, tz_str in self.COMMON_TIMEZONES.items():\n            self.add_timezone(name, tz_str)\n    \n    def get_time(self, timezone_name: str) -> Tuple[str, str, str]:\n        \"\"\"\n        Get current time in a specific timezone.\n        \n        Args:\n            timezone_name: Name of the timezone\n        \n        Returns:\n            Tuple of (formatted_time, offset, timezone_name)\n        \n        Raises:\n            KeyError: If timezone not found\n        \"\"\"\n        if timezone_name not in self.timezones:\n            raise KeyError(f\"Timezone not found: {timezone_name}\")\n        \n        tz_info = self.timezones[timezone_name]\n        now = datetime.now(tz_info.tz)\n        \n        # Format time as HH:MM:SS\n        formatted_time = now.strftime(\"%H:%M:%S\")\n        date_str = now.strftime(\"%Y-%m-%d\")\n        \n        return formatted_time, tz_info.offset, date_str\n    \n    def get_all_times(self) -> Dict[str, Dict[str, str]]:\n        \"\"\"\n        Get current time in all registered timezones.\n        \n        Returns:\n            Dictionary with timezone names as keys and time info as values\n        \"\"\"\n        result = {}\n        for tz_name in sorted(self.timezones.keys()):\n            time_str, offset, date_str = self.get_time(tz_name)\n            result[tz_name] = {\n                \"time\": time_str,\n                \"date\": date_str,\n                \"offset\": offset,\n                \"timezone\": self.timezones[tz_name].timezone_str\n            }\n        return result\n    \n    def format_analog_clock(self, timezone_name: str) -> str:\n        \"\"\"\n        Format time as an ASCII analog clock.\n        \n        Args:\n            timezone_name: Name of the timezone\n        \n        Returns:\n            ASCII representation of analog clock\n        \"\"\"\n        if timezone_name not in self.timezones:\n            raise KeyError(f\"Timezone not found: {timezone_name}\")\n        \n        tz_info = self.timezones[timezone_name]\n        now = datetime.now(tz_info.tz)\n        hours = now.hour % 12\n        minutes = now.minute\n        \n        # Simple analog clock representation\n        clock_str = f\"\"\"\n        ╔════════════════════╗\n        ║   {timezone_name:^16}   ║\n        ║                    ║\n        ║      {hours:2d}:{minutes:02d}         ║\n        ║                    ║\n        ║   {self.timezones[timezone_name].offset}    ║\n        ╚════════════════════╝\n        \"\"\"\n        return clock_str\n    \n    def display_table(self) -> str:\n        \"\"\"\n        Display all times in a formatted table.\n        \n        Returns:\n            Formatted table string\n        \"\"\"\n        times = self.get_all_times()\n        \n        # Header\n        table = \"╔═══════════════════╦══════════════╦══════════════╦═══════════════╗\\n\"\n        table += \"║ City              ║ Time         ║ Date         ║ Offset        ║\\n\"\n        table += \"╠═══════════════════╬══════════════╬══════════════╬═══════════════╣\\n\"\n        \n        # Rows\n        for city, info in times.items():\n            table += f\"║ {city:<17} ║ {info['time']:^12} ║ {info['date']:^12} ║ {info['offset']:^13} ║\\n\"\n        \n        # Footer\n        table += \"╚═══════════════════╩══════════════╩══════════════╩═══════════════╝\\n\"\n        \n        return table\n    \n    def get_list(self) -> List[Dict[str, str]]:\n        \"\"\"\n        Get all times as a list of dictionaries.\n        \n        Returns:\n            List of timezone info dictionaries\n        \"\"\"\n        result = []\n        times = self.get_all_times()\n        for city, info in times.items():\n            result.append({\n                \"city\": city,\n                \"time\": info[\"time\"],\n                \"date\": info[\"date\"],\n                \"offset\": info[\"offset\"],\n                \"timezone\": info[\"timezone\"]\n            })\n        return result\n    \n    def compare_times(self, tz1: str, tz2: str) -> Dict[str, any]:\n        \"\"\"\n        Compare times between two timezones.\n        \n        Args:\n            tz1: First timezone name\n            tz2: Second timezone name\n        \n        Returns:\n            Comparison data\n        \"\"\"\n        time1, offset1, date1 = self.get_time(tz1)\n        time2, offset2, date2 = self.get_time(tz2)\n        \n        # Calculate time difference\n        tz_info1 = self.timezones[tz1]\n        tz_info2 = self.timezones[tz2]\n        \n        now_utc = datetime.now(pytz.UTC)\n        now1 = now_utc.astimezone(tz_info1.tz)\n        now2 = now_utc.astimezone(tz_info2.tz)\n        \n        time_diff = (now2.utcoffset() - now1.utcoffset()).total_seconds() / 3600\n        \n        return {\n            \"timezone1\": tz1,\n            \"time1\": time1,\n            \"offset1\": offset1,\n            \"timezone2\": tz2,\n            \"time2\": time2,\n            \"offset2\": offset2,\n            \"time_difference_hours\": time_diff\n        }\n    \n    def get_noon_sunset_times(self, timezone_name: str) -> Dict[str, str]:\n        \"\"\"\n        Get approximate noon and sunset times (noon is 12:00).\n        For actual sunset, use a library like astral.\n        \n        Args:\n            timezone_name: Name of the timezone\n        \n        Returns:\n            Dictionary with noon and approximated times\n        \"\"\"\n        if timezone_name not in self.timezones:\n            raise KeyError(f\"Timezone not found: {timezone_name}\")\n        \n        tz_info = self.timezones[timezone_name]\n        now = datetime.now(tz_info.tz)\n        \n        # Next noon\n        noon = now.replace(hour=12, minute=0, second=0, microsecond=0)\n        if noon < now:\n            noon = noon.replace(day=now.day + 1)\n        \n        # Approximate sunset (6 PM)\n        sunset = now.replace(hour=18, minute=0, second=0, microsecond=0)\n        if sunset < now:\n            sunset = sunset.replace(day=now.day + 1)\n        \n        return {\n            \"timezone\": timezone_name,\n            \"next_noon\": noon.strftime(\"%H:%M:%S\"),\n            \"next_sunset\": sunset.strftime(\"%H:%M:%S\")\n        }\n\n\ndef create_clock() -> DigitalClock:\n    \"\"\"\n    Factory function to create a clock instance.\n    \n    Returns:\n        DigitalClock instance\n    \"\"\"\n    return DigitalClock()\n"