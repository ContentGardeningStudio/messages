"""
Module designed to make creating and sending chat messages easy.

1.  TelegramBot
    - Send messages via the Telegram Bot feature
    - https://core.telegram.org/bots
"""

import sys

import requests

from ._config import configure
from ._eventloop import MESSAGELOOP
from ._interface import Message
from ._utils import timestamp


class TelegramBot(Message):
    """
    Create and send Telegram message via the Telegram Bot API.

    Args:
        :from_: (str) optional arg to specify who message is from.
        :credentials: (str) auth token for bot for access.
        :chat_id: (str) chat_id for already-intiated chat.
            chat_id is an integer represented as a string.
            Recipient must have already initiated chat at some
            point in the past for bot to send message.
        :to: (str) if chat_id is unknown, can specify username of
            recipient to lookup via API call.  This may return None if
            chat is older than 24-hours old.
        :subject: (str) optional arg to specify message subject.
        :body: (str) message to send.
        :attachments: (str or list) each item is a url to attach
        :params: (dict) additional attributes to add to message,
            i.e. parse_mode (HTML or Markdown, see API for information
            on which attributes are possible.
        :profile: (str) use a separate account profile specified by name
        :save: (bool) save pertinent values in the messages config file,
            such as from_, chat_id, bot_token (encrypted keyring) to make
            sending messages faster.

    Attributes:
        :message: (dict) current form of the message to be constructed

    Usage:
        Create a TelegramBot object with required Args above.
        Send message with self.send() or self.send_async() methods.

    Note:
        For API description:
        https://core.telegram.org/bots/api#available-methods
    """

    def __init__(
        self, from_=None, credentials=None, chat_id=None, to=None,
        subject=None, body='', attachments=None, params=None, profile=None,
        save=False, verbose=False
    ):

        config_kwargs = {'from_': from_, 'credentials': credentials,
                     'chat_id': chat_id, 'profile': profile, 'save': save}

        configure(self, params=config_kwargs,
                to_save={'from_', 'chat_id'}, credentials={'credentials'})

        self.to = to
        self.subject = subject
        self.body = body
        self.attachments = attachments or []
        self.params = params or {}
        self.base_url = 'https://api.telegram.org/bot' + self.credentials
        self.message = {}
        self.verbose = verbose


    def __str__(self, indentation='\n'):
        """print(Telegram(**args)) method.
           Indentation value can be overridden in the function call.
           The default is new line"""
        return('{}From: {}'
               '{}To: {}'
               '{}Chat ID: {}'
               '{}Subject: {}'
               '{}Body: {}...'
               '{}Attachments: {}'
               .format(indentation, self.from_,
                       indentation, self.to,
                       indentation, self.chat_id,
                       indentation, self.subject,
                       indentation, self.body[0:40],
                       indentation, self.attachments))


    def get_chat_id(self, username):
        """Lookup chat_id of username if chat_id is unknown via API call."""
        if username is not None:
            chats = requests.get(self.base_url + '/getUpdates').json()
            user = username.split('@')[-1]
            for chat in chats['result']:
                if chat['message']['from']['username'] == user:
                    return chat['message']['from']['id']


    def construct_message(self):
        """Build the message params."""
        self.message['chat_id'] = self.chat_id
        self.message['text'] = ''
        if self.from_:
            self.message['text'] += ('From: ' + self.from_ + '\n')
        if self.subject:
            self.message['text'] += ('Subject: ' + self.subject + '\n')

        self.message['text'] += self.body
        self.message.update(self.params)


    def send_content(self, method='/sendMessage'):
        """send via HTTP Post."""
        if method == '/sendMessage':
            content_type = 'Message body'
        elif method == '/sendDocument':
            content_type = ('Attachment: ' + self.message['document'])

        url = self.base_url + method
        r = requests.post(url, json=self.message)

        if r.status_code == 200 and self.verbose:
            print(timestamp(), content_type + ' sent.')
        if r.status_code > 300 and self.verbose:
            print(timestamp(), 'Error while sending ' + content_type)
            print(r.text)


    def send(self):
        """Start sending the message and attachments."""
        self.construct_message()
        if self.verbose:
            print('Debugging info'
                  '\n--------------'
                  '\n{} Message created.'.format(timestamp()))

        self.send_content('/sendMessage')

        for a in self.attachments:
            self.message['document'] = a
            self.send_content(method='/sendDocument')

        if self.verbose:
            print(timestamp(), type(self).__name__ + ' info:',
                self.__str__(indentation='\n * '))

        print('Message sent.')


    def send_async(self):
        """Send message asynchronously."""
        MESSAGELOOP.add_message(self)
