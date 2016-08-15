import re

from slackclient import SlackClient


class Slack(object):
    def __init__(self, api_token, channel, username):
        self._api_token = api_token
        self._channel = channel
        self._channel_id = ""
        self._username = username
        self._user_id = ""
        self._slack = SlackClient(api_token)

        channels = self._slack.api_call("channels.list",
                                        exclude_archived=1)["channels"]
        for channel_ in channels:
            if channel.endswith(channel_["name"]):
                self._channel_id = channel_["id"]
        if not self._channel_id:
            raise RuntimeError("Couldn't get channel ID.")

        users = self._slack.api_call("users.list")["members"]
        for user in users:
            if user["name"] == username:
                self._user_id = user["id"]
        if not self._user_id:
            raise RuntimeError("Couldn't get bot user ID.")

        # Start real-time messaging session
        if not self._slack.rtm_connect():
            raise RuntimeError("Couldn't open rtm connection.")

    def get_users(self):
        """Fetch a list of all non-deleted users on Slack."""
        raw_users = self._slack.api_call("users.list")["members"]
        users = []

        for value in raw_users:
            if not value["deleted"]:
                user = {
                    "id": value["id"],
                    "username": value["name"],
                    "first_name": value["profile"].get("first_name", ""),
                    "last_name": value["profile"].get("last_name", "")
                }
                users.append(user)

        return users

    def get_incoming_commands(self):
        """Get a list of incoming messages directed at coffee bot."""
        commands = []
        for message in self._slack.rtm_read():
            if (
                message["type"] == "message" and
                message["channel"] == self._channel_id and
                not message.get("subtype", "") and
                message["text"].startswith("<@{0}>".format(self._user_id))
            ):
                regex = re.compile(r"<@{0}> ".format(self._user_id))
                parsed = regex.split(message["text"])
                if len(parsed) == 2:
                    commands.append(regex.split(message["text"])[1])

        return commands

    def send_message(self, msg, as_user=True):
        """Send a text message to the configured Slack channel."""
        self._slack.api_call(
            "chat.postMessage",
            channel=self._channel,
            text=msg,
            as_user=as_user,
            username=self._username
        )
