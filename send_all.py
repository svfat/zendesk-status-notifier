#!/usr/bin/env python

import requests

from utils import calculate_available_time
from datetime import timedelta

import logging
logging.basicConfig(filename="sender.log", level=logging.DEBUG)

try:
    import config
except ImportError:
    raise ImportError(msg="config.py not found")

from core import agents

DT_FORMAT = "%Y-%m-%d %H:%M:%S"

class Sender():
    def __init__(self):
        pass

    def _send(self, subject, text, html=None):
        data = {"from": config.MAILGUN_EMAIL,
                "to": config.EMAIL_ADDR,
                "cc": config.MAILGUN_CC_LIST,
                "subject": subject,
                "text": text,}
        if html:
            data['html'] = html
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

    def send_total_status(self, agents):
        """
        Is there anyway to send ONE email summarizing all reps that show TALK time that day,
         into one email, with their name and talk time that day?
        3. Is there anyway to include the previous 7 days worth of totals in the one summary email?
        For example: TODAY - XX:XX Hours - YESTERDAY - XX:XX Hours, etc...
        """
        def adjust_length(s, max_len):
            if len(s) > max_len:
                return s[:max_len]
            else:
                return s
        plain_total_tpl = "{}\t{} Hours"
        plain_line_tpl = "Id: {}\tName: {}\tTALK\t{}\t{}"
        html_total_tpl = '<tr style="color: {}"><td>{}</td><td>{}</td></tr>'
        html_line_tpl = '<tr ><td>{}</td><td>{}</td></tr>'
        html_data = ["""<!DOCTYPE html>
                        <html>
                        <body>
                        <h1>Report</h1>
                        """,
                     ]
        plaintext_data = []
        for agent in agents:
            plaintext_data.append(agent.agent_name)
            html_data.append('<h2>{}</h2>'.format(agent.agent_name))
            html_data.append('<p>Id: {}</p>'.format(agent.agent_id))
            html_data.append('<table><tr><td>') # external table
            html_data.append('<table cellpadding="5" border="1" style="border-collapse: collapse;">')
            for date, total in agent.get_week_report().items():
                total = total - timedelta(microseconds=total.microseconds)
                if total.total_seconds() <= 0:
                    color = "#d0d0d0"
                else:
                    color = "#000000"
                plaintext_data.append(plain_total_tpl.format(date.strftime("%Y-%m-%d %A"), total))
                html_data.append(html_total_tpl.format(color, date.strftime("%Y-%m-%d %A"), total))
            plaintext_data.append("\n")
            plaintext_data.append("Day status")
            html_data.append("</table><h4>Day status</h4>")
            html_data.append("</td><td>") # second column
            day_report, total_day = agent.get_day_report()

            if day_report:

                html_data.append('<table cellpadding="5" border="1" style="border-collapse: collapse;">')
                for status, datetime in day_report:
                    dt = datetime.strftime(DT_FORMAT)
                    plaintext_data.append(plain_line_tpl.format(agent.agent_id,
                                                          agent.agent_name,
                                                          adjust_length(status.upper(), len('AVAILABLE')),
                                                          dt))
                    html_data.append(html_line_tpl.format(adjust_length(status.upper(), len('AVAILABLE')),
                                                          dt))
                html_data.append('</table>')
                plaintext_data.append("Total available: {}".format(total_day))
                html_data.append("<p>Total available: <strong>{}</strong></p>".format(str(total_day).split(".")[0]))
            else:
                plaintext_data.append('-- NO RECORDS --')
                html_data.append("<p>-- NO RECORDS --</p>")
            plaintext_data.append("\n")
            html_data.append('</td></tr></table>')
            html_data.append('<hr \>')
        html_data.append("</body></html>")
        plaintext = '\n'.join(plaintext_data)
        html = '\n'.join(html_data)
        print(html)
        with open("email.html", "w") as f:
            f.write(html)
        self._send("Report for last 7 days", plaintext, html)

if __name__ == "__main__":
    default_sender = Sender()
    from data import get_records_on_dt_range
    db_data = get_records_on_dt_range()
    for agent in agents:
        agent_id = agent.agent_id
        stack = db_data[agent_id]
        #default_sender.send_talk_status(agent_id=agent_id, agent_name=agent.agent_name, stack=stack)
    default_sender.send_total_status(agents)

