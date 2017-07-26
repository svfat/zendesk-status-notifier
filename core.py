import json
import logging
import sys
from collections import defaultdict
from datetime import datetime
from urllib import request

import requests

from utils import calculate_available_time

logging.basicConfig(filename="main.log", level=logging.DEBUG)

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


class Sender():
    def __init__(self):
        pass

    def _send(self, subject, text, html):
        data = {"from": config.MAILGUN_EMAIL,
                "to": config.EMAIL_ADDR,
                "cc": config.MAILGUN_CC_LIST,
                "subject": subject,
                "text": text,
                "html": html}
        logging.debug(f'Sending email {data} via {config.MAILGUN_API_HOST}')
        response = requests.post(
            f'https://api.mailgun.net/v3/{config.MAILGUN_API_HOST}/messages',
            auth=("api", config.MAILGUN_API_KEY),
            data=data)
        if response.status_code == 200:
            logging.debug(f'Email with subject {subject} - Success')
        else:
            logging.error(f'Email with subject {subject} - Status {response.status_code}')

    def _render_to_html(self, agent_id, agent_name, stack, total_avail):
        HTML_HEADER = """<!DOCTYPE html>
                        <html>
                        <body>
                        <table border="1">
                            <thead>
                            <tr>
                                <th>ID</th>
                                <th>NAME</th>
                                <th>SERVICE</th>
                                <th>STATUS</th>
                                <th>DATETIME</th>
                            </tr>
                            </thead>
                      """

        HTML_FOOTER = """
                        <p>Total available: {}</p>
                        </table>
                        </body>
                        </html>
                      """
        line_tpl = """
                    <tr>
                        <td>{}</td>
                        <td>{}</td>
                        <td>TALK</td>
                        <td><strong>{}</strong></td>
                        <td>{}</td>
                    </tr>
                   """
        result = []
        for item in stack:
            status = item['status'].upper()
            str_time = item['dt']
            result.append(line_tpl.format(agent_id, agent_name, status, str_time))
        return HTML_HEADER + '\n'.join(result) + HTML_FOOTER.format(total_avail)

    def _render_to_plaintext(self, agent_id, agent_name, stack, total_avail):
        """
        TO: support@natomounts.com
        SUBJECT: ZD ACCOUNT NAME TOOL STATUS DATE TIME IN PDT
        EXAMPLE: SUBJECT: ZD MISTY KENNEDY TALK DISABLED XX/XX/XXXX - XX:XX:XX (PDT)

        BODY: Please show the last 12 status changes for this TOOL and ACCOUNT NAME.
        EXAMPLE:
        ZD MISTY KENNEDY TALK DISABLED 04/23/2017 - 01:03:05PM (PDT)
        ZD MISTY KENNEDY TALK ENABLED 04/23/2017 - 09:03:05AM (PDT)
        ZD MISTY KENNEDY TALK DISABLED 04/22/2017 - 01:03:05PM (PDT)
        ZD MISTY KENNEDY TALK ENABLED 04/22/2017 - 09:03:05AM (PDT)
        ZD MISTY KENNEDY TALK DISABLED 04/21/2017 - 01:03:05PM (PDT)
        ZD MISTY KENNEDY TALK ENABLED 04/21/2017 - 09:03:05AM (PDT)
        ZD MISTY KENNEDY TALK DISABLED 04/20/2017 - 01:03:05PM (PDT)
        ZD MISTY KENNEDY TALK ENABLED 04/20/2017 - 09:03:05AM (PDT)
        ZD MISTY KENNEDY TALK DISABLED 04/19/2017 - 01:03:05PM (PDT)
        ZD MISTY KENNEDY TALK ENABLED 04/19/2017 - 09:03:05AM (PDT)
        ZD MISTY KENNEDY TALK DISABLED 04/18/2017 - 01:03:05PM (PDT)
        ZD MISTY KENNEDY TALK ENABLED 04/18/2017 - 09:03:05AM (PDT)
        """
        line_tpl = "Id: {}, Name: {} TALK {} {}"
        result = []
        for item in stack:
            result.append(line_tpl.format(agent_id, agent_name, item['status'].upper(), item['dt']))
        result.append("Total available: {}".format(total_avail))
        return '\n'.join(result)

    def send_talk_status(self, agent_id, agent_name, stack):
        # reverse stack
        reversed_stack = stack[::-1]
        total_avail_time = calculate_available_time(data=stack,
                                                    avail_status='AVAILABLE',
                                                    not_avail_status='NOT_AVAILABLE',
                                                    f=DT_FORMAT)
        plaintext = self._render_to_plaintext(agent_id, agent_name, reversed_stack, total_avail_time)
        html = self._render_to_html(agent_id, agent_name, reversed_stack, total_avail_time)
        subject = f"ZD {agent_name} TALK STATUS REPORT"
        self._send(subject, plaintext, html)


default_sender = Sender()


class Storage():
    def __init__(self, filename="storage.json", sender=default_sender):
        self._filename = filename
        self.sender = sender
        self.__save_history = False
        self.data = defaultdict(lambda: {'stack': [], 'history': []})
        try:
            self._load()
        except FileNotFoundError:
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
            stack = self.data[agent_id]['stack']
            self.sender.send_talk_status(agent_id=agent_id, agent_name=agent.agent_name, stack=stack)
            if len(stack) >= size:
                if self.__save_history:
                    self.data[agent_id]['history'] += stack
                self.data[agent_id]['stack'] = []
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
