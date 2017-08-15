import json
import logging
import sys
from collections import defaultdict
from datetime import datetime
from urllib import request
from data import create_agents, add_record

create_agents()

try:
    import config
except ImportError:
    raise ImportError(msg="config.py not found")
from urllib.request import Request, urlopen
from urllib.error import URLError

DT_FORMAT = "%Y-%m-%d %H:%M:%S"

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




class Storage():
    def __init__(self, filename="storage.json"):
        self._filename = filename
        self.__save_history = False
        self.data = defaultdict(lambda: {'stack': [], 'history': []})
        try:
            self._load()
        except FileNotFoundError:
            self._dump()

    def dump(self):
        self._dump()

    def _dump(self):
        with open(self._filename, 'w') as outfile:
            json.dump(self.data, outfile, indent=4, sort_keys=True)

    def _load(self):
        with open(self._filename, 'r') as source:
            for k, v in json.load(source).items():
                self.data[k] = v

    def _load_if_changed(self):
        # TODO add change check
        self._load()

    def get_last_status(self, agent):
        agent_id = agent.agent_id
        self._load_if_changed()
        stack = self.data[agent_id]['stack']
        if len(stack):
            last_status = stack[-1]['status']
        else:
            last_status = None
        return last_status

    def add_status(self, agent, status, size=12):
        if status.lower() in ['available', 'not_available']:
            agent_id = agent.agent_id
            self.data[agent_id]['stack'].append(
                {'status': status,
                 'dt': datetime.now().strftime(DT_FORMAT)
                 }
            )
            add_record(status=status, agent_id=agent_id)
            self._dump()


storage = Storage()


class ZendeskAPIGenericClass:
    def __init__(self):
        self._api_url = f"{top_level_url}api/v2/"
        self._api = zc


class Agent(ZendeskAPIGenericClass):
    def __init__(self, agent_id, agent_name):
        super().__init__()
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.__urls = {
            'talk_availiblity': f"{self._api_url}channels/voice/availabilities/{self.agent_id}.json",
        }

    def get_talk_availability(self):
        data = json.loads(_get(self.__urls['talk_availiblity']))
        return data['availability']

    def get_talk_status(self):
        print(f'Agent: {self.agent_id} - Getting talk status: ', end='')
        avail = self.get_talk_availability()
        status = avail['status']
        print(status)
        return status

    def get_chat_availability(self):
        raise NotImplementedError
        u = self._api.users(id=self.agent_id)


agents = [Agent(k, v) for k, v in config.ZENDESK_AGENTS]
