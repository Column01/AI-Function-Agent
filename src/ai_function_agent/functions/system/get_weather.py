import requests
import json


def get_weather(latitude: str, longitude: str) -> dict:
    response = requests.get(f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&current=temperature_2m,wind_speed_10m&hourly=temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code")
    data = response.json()
    current = data["current"]
    pairs = [f"{k}: {v}" for k, v in current.items()]
    return "\n".join(pairs)


function = get_weather
function_spec = {
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "Get's the weather for the specified location based on latitude and longitude",
        "parameters": {
            "type": "object",
            "properties": {
                "latitude": {"type": "string", "description": "The latitude of the location"},
                "longitude": {"type": "string", "description": "The longitude of the location"}
            },
            "required": ["latitude", "longitude"],
        },
    },
}
