#!/usr/bin/env python

import requests

from utils import calculate_available_time

import logging
logging.basicConfig(filename="sender.log", level=logging.DEBUG)

try:
    import config
except ImportError:
    raise ImportError(msg="config.py not found")

from core import storage, agents

DT_FORMAT = "%Y-%m-%d %H:%M:%S"

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
                                                    avail_status='available',
                                                    not_avail_status='not_available',
                                                    f=DT_FORMAT)
        plaintext = self._render_to_plaintext(agent_id, agent_name, reversed_stack, total_avail_time)
        html = self._render_to_html(agent_id, agent_name, reversed_stack, total_avail_time)
        subject = f"ZD {agent_name} TALK STATUS REPORT"
        self._send(subject, plaintext, html)


if __name__ == "__main__":
    default_sender = Sender()
    for agent in agents:
        agent_id = agent.agent_id
        stack = storage.data[agent_id]['stack']
        default_sender.send_talk_status(agent_id=agent_id, agent_name=agent.agent_name, stack=stack)
        storage.data[agent_id]['stack'] = []
    storage.dump()

