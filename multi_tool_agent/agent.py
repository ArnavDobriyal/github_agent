import datetime
from zoneinfo import ZoneInfo
from google.adk.agents import Agent
import subprocess

def get_status():
    result = subprocess.run(["git", "status"], capture_output=True, text=True)
    return result.stdout

def add_data():
    result = subprocess.run(["git", "add","."], capture_output=True, text=True)
    return result.stdout


def get_current_time(city: str) -> dict:
    """Returns the current time in a specified city.

    Args:
        city (str): The name of the city for which to retrieve the current time.

    Returns:
        dict: status and result or error msg.
    """

    if city.lower() == "new york":
        tz_identifier = "America/New_York"
    else:
        return {
            "status": "error",
            "error_message": (
                f"Sorry, I don't have timezone information for {city}."
            ),
        }

    tz = ZoneInfo(tz_identifier)
    now = datetime.datetime.now(tz)
    report = (
        f'The current time in {city} is {now.strftime("%Y-%m-%d %H:%M:%S %Z%z")}'
    )
    return {"status": "success", "report": report}


root_agent = Agent(
    name="weather_time_agent",
    model="gemini-2.0-flash",
    description=(
        "Agent to make git changes and present the changes ."
    ),
    instruction=(
        "You are a helpful agent who can go various git commands. you have 2 tools get_status,add_data use only that what was asked by user"
    ),
    tools=[get_status,add_data],
)