import os
import json
import time
import math
from datetime import datetime, timedelta

from db import DB
from display import Display
from slack import Slack
from sensors import Sensors


config = None
with open(os.path.join(os.path.dirname(__file__), "../config.json")) as f:
    config = json.load(f)


COFFEE_BREW_TIME_SEC = config["coffeeBrewTimeSec"]
COFFEE_FRESH_TIME_SEC = config["coffeeFreshTimeSec"]
FLOW_DEBOUNCE_TIME_SEC = 5
FORCE_MIN_TIME_SEC = 3
MIN_FLOW_AMOUNT_LITRES = 0.001
MUG_SIZE_LITRES = 0.35
HELP_TEXT = (
    "Hi there! I'm Coffee Bot. Here's what you can ask me:\n"
    "`help` - This message.\n"
    "`status` - The quantity and freshness of the office coffee."
)

STATUS_WAITING = "waiting"
STATUS_FILLING = "filling"
STATUS_BREWING = "brewing"
STATUS_READY = "ready"


db = DB()
display = Display()
slack = Slack(
    config["slack"]["apiToken"],
    config["slack"]["channel"],
    config["slack"]["username"]
)
sensors = Sensors(
    config["gpioChannels"]["flow"],
    config["gpioChannels"]["force"]
)


status = "waiting"
did_notify_cold_coffee = False
last_litres_acc = 0
litres_remaining = 0
brew_start_time = None
time_of_last_flow = None


# Update users table with current list of Slack users
db.update_users_table(slack.get_users())


def handle_slack_command(command):
    """Handle incoming Slack chat command. Commands must be in the form
    @<username> <command>."""
    if command == "help":
        slack.send_message(HELP_TEXT)
    elif command == "status":
        message = "Status: {0}\n".format(status)
        if status == STATUS_FILLING:
            message = ("Someone's filling the coffee machine right now. "
                       "Check back soon.")
        elif status == STATUS_BREWING:
            elapsed_brew_time = datetime.now() - brew_start_time
            percent_complete = int(
                elapsed_brew_time.seconds / COFFEE_BREW_TIME_SEC * 100
            )
            message = (
                "Coffee is brewing: {0}% complete.".format(
                    percent_complete
                )
            )
        elif status == STATUS_WAITING:
            message = ("I'm not sure what's up with the coffee right now. "
                       "Try making a fresh pot.")
        elif status == STATUS_READY:
            time_since_brew = (datetime.now() - brew_start_time -
                               timedelta(seconds=COFFEE_BREW_TIME_SEC))
            hours_since_brew = 0
            minutes_since_brew = time_since_brew.seconds / 60
            if time_since_brew.seconds >= 3600:
                hours_since_brew = math.floor(
                    time_since_brew.seconds / 3600
                )
            if hours_since_brew:
                minutes_since_brew = (
                    minutes_since_brew - hours_since_brew * 60
                )
            message = (
                "Current pot ({0}L) was made{1} {2} minute(s) ago. There are "
                " left.".format(
                    round(litres_display, 2),
                    (" {0} hour(s) and".format(hours_since_brew) if
                        hours_since_brew else ""),
                    round(minutes_since_brew)
                )
            )
        slack.send_message(message)


print("Press Ctrl-C to quit.")


while True:
    # Main loop

    last_status = status
    litres_acc = sensors.get_litres_acc()
    litres_delta = litres_acc - last_litres_acc
    litres_display = 0

    # TODO: fix
    if (status == STATUS_WAITING or status == STATUS_READY) and (
            litres_delta > MIN_FLOW_AMOUNT_LITRES):
        # Check if water began flowing
        if litres_delta > MIN_FLOW_AMOUNT_LITRES:
            status = STATUS_FILLING
            did_notify_cold_coffee = False
            time_since_last_flow = datetime.now()
    elif status == STATUS_FILLING:
        # Check if filling completed
        if litres_delta > MIN_FLOW_AMOUNT_LITRES:
            time_of_last_flow = datetime.now()
        else:
            time_since_last_flow = datetime.now() - time_of_last_flow
            if time_since_last_flow.seconds > FLOW_DEBOUNCE_TIME_SEC:
                status = STATUS_BREWING
                time_of_last_flow = None
                litres_remaining = litres_acc
                litres_acc = 0
                sensors.reset_litres_acc()
                brew_start_time = datetime.now()
                slack.send_message("Coffee is brewing...")
    elif status == STATUS_BREWING:
        # Check if brewing completed
        elapsed_brew_time = datetime.now() - brew_start_time
        litres_display = (
            elapsed_brew_time.seconds / COFFEE_BREW_TIME_SEC
        ) * litres_remaining

        if elapsed_brew_time.seconds > COFFEE_BREW_TIME_SEC:
            status = STATUS_READY
            slack.send_message(
                "Fresh pot of coffee ready. Get it while it's hot!"
            )
    elif status == STATUS_READY:
        # Check if coffee is still fresh
        seconds_since_brew = (
            datetime.now() - brew_start_time -
            timedelta(seconds=COFFEE_BREW_TIME_SEC)
        ).seconds
        if (seconds_since_brew >= COFFEE_FRESH_TIME_SEC and
                not did_notify_cold_coffee):
            did_notify_cold_coffee = True
            slack.send_message(
                "The coffee is getting cold. Finish it off or make a new pot."
            )

        litres_display = litres_remaining

    last_litres_acc = litres_acc

    # Handle incoming Slack commands
    slack_commands = slack.get_incoming_commands()
    for command in slack_commands:
        handle_slack_command(command)

    display.show_text([
        "COFFEE BOT",
        "~~~~~~~~~~",
        "Status: {0}".format(status),
        "Coffee: {0}L".format(round(litres_display, 2)),
    ])
