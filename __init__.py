from mycroft import MycroftSkill, intent_handler
from adapt.intent import IntentBuilder
import requests


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

    @intent_handler(IntentBuilder('CommandIntent').require('Action')
                    .require('Type'))
    # .require('Thing'))
    def handle_command_intent(self, message):
        host = self.settings.get('host')
        if host:
            self.host = host
        token = self.settings.get('token')
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
