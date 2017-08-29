import json
import logging
import sys
from urllib import request
from data import create_agents, add_record, get_agents

create_agents()

try:
    import config
except ImportError:
    raise ImportError(msg="config.py not found")
from urllib.request import Request, urlopen
from urllib.error import URLError



class WrongContentTypeException(BaseException):
    def __init__(self, message=None, errors=None):
        super().__init__(f"Response isn't in JSON format.{' '+message if message else ''}")


def _get(url):
    req = Request(url)
    try:
        response = urlopen(req)
    except URLError as e:
        if hasattr(e, 'reason'):
            logging.debug(f'We failed to reach a server. Reason: {e.reason}')
        elif hasattr(e, 'code'):
            logging.debug(f'The server couldn\'t fulfill the request. Error code: {e.code}')
        sys.exit(1)
    else:
        info = response.info()
        ct = info.get_content_type()
        if ct != 'application/json':
            raise WrongContentTypeException
        return response.read()


password_mgr = request.HTTPPasswordMgrWithDefaultRealm()
top_level_url = f"https://{config.ZENDESK_SUBDOMAIN}.zendesk.com/"
password_mgr.add_password(None, top_level_url, config.ZENDESK_EMAIL, config.ZENDESK_PASSWORD)
handler = request.HTTPBasicAuthHandler(password_mgr)
opener = request.build_opener(handler)
request.install_opener(opener)

from zenpy import Zenpy
import config

cred = {
    'subdomain': config.ZENDESK_SUBDOMAIN,
    'email': config.ZENDESK_EMAIL,
    'password': config.ZENDESK_PASSWORD
}

zc = Zenpy(**cred)


class ZendeskAPIGenericClass:
    def __init__(self):
        self._api_url = f"{top_level_url}api/v2/"
        self._api = zc


class Agent(ZendeskAPIGenericClass):
    # TODO incapsulate in Agent pony ORM model
    def __init__(self, model):
        super().__init__()
        self.model = model
        self.agent_id = model.agent_id
        self.agent_name = model.name
        self.__urls = {
            'talk_availiblity': f"{self._api_url}channels/voice/availabilities/{self.agent_id}.json",
        }

    def get_last_status(self):
        return self.model.get_last_status()

    def get_week_report(self):
        return self.model.get_week_report()

    def get_talk_availability(self):
        data = json.loads(_get(self.__urls['talk_availiblity']))
        return data['availability']

    def get_talk_status(self):
        avail = self.get_talk_availability()
        status = avail['status']
        if status == 'on_call':
            status = 'available'
        return status

    def save_current_status(self):
        status = self.get_talk_status()
        if status.lower() in ['available', 'not_available']:
            print(f"Saving {status}")
            agent_id = self.agent_id
            add_record(status=status, agent_id=agent_id)
        else:
            print(f"Status is wrong")

    def get_chat_availability(self):
        raise NotImplementedError
        u = self._api.users(id=self.agent_id)


agents = [Agent(a) for a in get_agents()]
