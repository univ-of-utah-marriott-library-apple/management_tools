####
#
# This module allows for easy integration with Slack (https://slack.com/). The
# messages are sent via JSON over plaintext, so don't use them for transmitting
# anything sensitive.
#
####

## Imports
import json
import urllib2

####
#
# API Description
#
# These are all of the Slack API fields supported in this module.
supported_fields = [
    # The content of the message. This can be plaintext or Markdown text.
    'text',
    # The name of the bot posting hte webhook integration message.
    'username',
    # The link to an image for the bot's avatar.
    'icon_url',
    # An emoji to use as the bot's image. Overrides 'icon_url'.
    'icon_emoji',
    # Where to post the message.
    'channel',
    # Whether to allow Markdown formatting in the 'text' field.
    'mrkdwn',
    # A list of attachments.
    'attachments'
]
# These fields are supported as 'attachments' subfields.
supported_attachments_subfields = [
    # The title of the attachment.
    'title',
    # The pretext.
    'pretext',
    # The actual text.
    'text',
    # Where to allow Markdown. Valid options are: ["pretext", "text", "fields"].
    'mrkdwn_in'
]

class IncomingWebhooksSender(object):
    """
    The IncomingWebhooksSender is an object to facilitate using a bot to post
    to the Slack team communication platform.

    Slack defines an API of available calls for "incoming webhooks" here:
        https://api.slack.com/incoming-webhooks

    This implementation is meant to be fully-featured, but also provides high-
    level methods that abstract away most of the configuration to make use in
    scripts easier. (Plus it's easier to read and document.)
    """
    def __init__(self, integration_url, bot_name=None, icon_url=None, icon_emoji=None, channel=None, markdown=None):
        """
        Creates a IncomingWebhooksSender object to send messages to a given
        Slack team.

        :param integration_url: The incoming webhook integration URL. This must
                                be supplied at creation (or else the bot is
                                useless).
        :param bot_name:        The name the bot will use when posting.
        :param icon_url:        A URL to use as the bot's icon.
        :param icon_emoji:      A colon emoji to use as the bot's icon. This
                                overrides 'icon_url'.
        :param channel:         The default channel for this bot to post to.
        :param markdown:        Whether to allow markdown (defaults to True if
                                not specified).
        """
        self.url        = integration_url
        self.username   = bot_name
        self.icon_url   = icon_url
        self.icon_emoji = icon_emoji
        self.channel    = channel
        self.mrkdwn     = markdown
        # Check if the channel has a '#' or '@' at the beginning. If not,
        # throw an error.
        if not self.username and self.username is not None:
            raise ValueError("Null username specified.")
        if not self.channel and self.channel is not None:
            raise ValueError("Null channel specified.")
        if (channel is not None and not self.channel.startswith('#')
            and not self.channel.startswith('@')):
            raise ValueError(
                "Invalid channel. Need a '#' for channels or '@' for direct " +
                "messages."
            )
    ############################################################################
    # Public methods.
    def send_message(self, message):
        """
        Sends a message to the default channel for this webhook (which is
        determined by the URL passed in during object construction).

        :param message: Message text you want to send.
        """
        data = {'text': str(message)}
        self.__prep_and_send_data(data)
    def success(self, message=None):
        """
        Sends a check mark with a message (if desired).

        :param message: An optional string to include.
        """
        send_message = ":white_check_mark:"
        if message:
            send_message += " " + str(message)
        data = {'text': str(send_message)}
        self.__prep_and_send_data(data)
    def warning(self, message=None):
        """
        Sends a yellow warning sign with a message (if desired).

        :param message: An optional string to include.
        """
        send_message = ":warning:"
        if message:
            send_message += " " + str(message)
        data = {'text': str(send_message)}
        self.__prep_and_send_data(data)
    warn = warning
    def error(self, message=None):
        """
        Sends a red circle with a message (if desired).

        :param message: An optional string to include.
        """
        send_message = ":red_circle:"
        if message:
            send_message += " " + str(message)
        data = {'text': str(send_message)}
        self.__prep_and_send_data(data)
    critical = error
    def send_message_to_channel(self, message, channel):
        """
        Sends a message to a specific channel.

        Use '#' for channels and private groups, and '@' for direct messages.
        For example:
            #general
            #my-private-group
            @someguy

        :param message: Message text you want to send.
        :param channel: The channel to which you want to send the data.
        """
        data = {
            'text': str(message),
            'channel': channel
        }
        self.__prep_and_send_data(data)
    def send_dictionary(self, dictionary):
        """
        Takes any dictionary and sends it through. It will be verified first, so
        the dictionary must only use the available fields in the Slack API.

        Note that with this method, you can send any message with any name to
        any channel, et cetera.

        :param dictionary: A dictionary of values you want to send.
        """
        self.__prep_and_send_data(dictionary)
    ############################################################################
    # Private methods.
    def __prep_and_send_data(self, data):
        """
        Takes a dictionary and prepares it for transmission, then sends it.

        :param data: A map of Slack API fields to desired values.
        :type  data: dict
        """
        data = self.__update_data(data)
        self.__send_json(self.__prep_json_from_data(data))
    def __update_data(self, data):
        """
        Automatically updates the contents of the 'data' object with any fields
        that are set in the object but weren't specified in the data. This makes
        method calls simpler.

        This method will also verify the data in the dictionary.

        :param data: A map of Slack API fields to desired values.
        :type  data: dict
        :returns: A copy of the `data` dictionary, but with extra values if they
            were specified in the object constructor.
        """
        # Duplicate the data to make this method non-destructive.
        return_data = dict(data)
        # Iterate over each of the supported fields.
        for field in supported_fields:
            # Let's see if we have a value defined for that attribute.
            # Note that this requires the object's attributes to have the same
            # name as the Slack API fields.
            try:
                value = getattr(self, field)
            except AttributeError:
                # Didn't have it, but let's not throw an error. Just continue.
                continue
            # If the field isn't already in the data, add it.
            # This ensure that overriding calls are not overridden themselves.
            if value is not None and not field in return_data:
                return_data[field] = value
        # Ensure the dictionary is good-to-go.
        self.__verify_data(data)
        return return_data
    def __verify_data(self, data):
        """
        Verifies that all of the fields in the `data` dictionary are valid. If
        any field is found that isn't considered a supported field, an error is
        raised.

        This also checks inside the list of attachments (if it's present) to be
        sure nothing is wrong.

        :param data: A map of Slack API fields to desired values.
        :type  data: dict
        """
        # Check it's a dictionary.
        if not isinstance(data, dict):
            raise ValueError("Received a non-dictionary form of data.")
        # Iterate over every key.
        for key in data:
            # If the key isn't supported, that's a problem!
            if not key in supported_fields:
                raise ValueError("Bad key in data: {}".format(key))
            # The 'attachments' key should contain a list.
            if key == 'attachments':
                # Verify it's really a list.
                if not isinstance(data[key], list):
                    raise ValueError("'attachments' field in data must be a list.")
                # Ensure there are no rogue values.
                for subkey in data[key]:
                    if not subkey in supported_attachments_subfields:
                        raise ValueError("Bad key in 'attachments': {}".format(subkey))
    def __prep_json_from_data(self, data):
        """
        Given data, this updates the contents and then gives back the string
        form of the JSON data.

        :param data: A map of Slack API fields to desired values.
        :type  data: dict
        :returns: A string form of the dictionary.
        """
        # Update all the data.
        data = self.__update_data(data)
        # Return the JSON string form of the data.
        return self.__get_json_from_data(data)
    def __get_json_from_data(self, data):
        """
        Just gives back a string form of the data. This is just a wrapper so the
        'json' module doesn't have to be loaded in addition to this one.

        :param data: A map of Slack API fields to desired values.
        :type  data: dict
        :returns: The string format returned by `json.dumps(data)`.
        """
        return json.dumps(data)
    def __send_json(self, data):
        """
        Sends the given JSON data across an HTTP connection. This does not check
        if the data is valid. This is by design to ensure that if I ever mess
        something up with the `supported_fields` list or something, the object
        can still be used to send anything.

        :param data: JSON representation of a map of Slack API fields to desired
            values.
        :type  data: str
        """
        # Form the HTTP PUT request.
        request = urllib2.Request(self.url, data)
        # Send the data!
        urllib2.urlopen(request)
