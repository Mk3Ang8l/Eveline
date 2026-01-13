"""
Weather service with OpenWeatherMap (free API)
"""

import httpx
import os
import logging
from dotenv import load_dotenv
load_dotenv

logger = logging.getLogger(__name__)

WEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY") 

class WeatherService:
    
    @staticmethod
    async def get_weather(city: str, units: str = "metric") -> dict:
        """
        Get current weather for a city
        
        Args:
            city: Name of the city (e.g., "Paris", "New York")
            units: "metric" (Celsius) or "imperial" (Fahrenheit)
        """
        if not WEATHER_API_KEY:
            return {"error": "OPENWEATHER_API_KEY not configured"}
        
        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {
            "q": city,
            "appid": WEATHER_API_KEY,
            "units": units,
            "lang": "en" # Change language to English
        }
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params)
                
                if response.status_code != 200:
                    return {"error": f"City not found or API error: {response.status_code}"}
                
                data = response.json()
                
                # Format result
                return {
                    "city": data["name"],
                    "country": data["sys"]["country"],
                    "temperature": data["main"]["temp"],
                    "feels_like": data["main"]["feels_like"],
                    "description": data["weather"][0]["description"],
                    "humidity": data["main"]["humidity"],
                    "wind_speed": data["wind"]["speed"],
                    "icon": data["weather"][0]["icon"],
                    "icon_url": f"https://openweathermap.org/img/wn/{data['weather'][0]['icon']}@2x.png"
                }
                
        except Exception as e:
            logger.error(f"Weather API error: {e}")
            return {"error": str(e)}
