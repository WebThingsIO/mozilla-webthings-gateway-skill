from mycroft import MycroftSkill, intent_handler
from adapt.intent import IntentBuilder
from mycroft.api import DeviceApi

import requests
import base64
import json


class MozillaIotGateway(MycroftSkill):
    def __init__(self):
        MycroftSkill.__init__(self)

        self.host = 'https://gateway.local'
        self.token = ''

    def get_headers(self):
        return {
            'Authorization': 'Bearer ' + self.token,
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }

    def get_oauth_token(self):
        try:
            token = DeviceApi().get_oauth_token(1172752248686736379)
        except requests.HTTPError:
            return None
        return token['access_token']

    def get_oauth_host(self):
        try:
            token = DeviceApi().get_oauth_token(1172752248686736379)
        except requests.HTTPError:
            return None
        jwt = token['access_token']
        parts = jwt.split(".")
        if len(parts) < 2:
            return None
        payload_raw = parts[1]
        if len(payload_raw) % 3 > 0:
            payload_raw += "=" * (3 - (len(payload_raw) % 3))
        try:
            payload_medium_rare = base64.b64decode(payload_raw)
            payload = json.loads(payload_medium_rare)
            return payload['iss']
        except ValueError:
            return None

    @intent_handler(IntentBuilder('CommandIntent').require('Action')
                    .require('Type'))
    # .require('Thing'))
    def handle_command_intent(self, message):
        host = self.settings.get('host')
        if not host:
            host = self.get_oauth_host()
        if host:
            self.host = host
        token = self.settings.get('token')
        if not token:
            token = self.get_oauth_token()
        if token:
            self.token = token

        if not self.token:
            self.speak_dialog('needs.configure')
            return

        utt = message.data.get('utterance')
        response = requests.post(self.host + '/commands', json={'text': utt},
                                 headers=self.get_headers())
        data = response.json()

        if response.status_code != 201:
            self.speak(data['message'])
            return
        verb = ''
        preposition = ''

        keyword = data['payload']['keyword']
        if keyword == 'make':
            verb = 'making'
        elif keyword == 'change':
            verb = 'changing'
        elif keyword == 'set':
            verb = 'setting'
            preposition = 'to '
        elif keyword == 'dim':
            verb = 'dimming'
            preposition = 'by '
        elif keyword == 'brighten':
            verb = 'brightening'
            preposition = 'by '
        else:
            verb = keyword + 'ing'

        value = data['payload']['value']
        if value is None:
            value = ''

        thing = data['payload']['thing']
        message = 'Okay, ' + verb + ' the ' + thing + ' ' + preposition + value
        self.speak(message)


def create_skill():
    return MozillaIotGateway()
