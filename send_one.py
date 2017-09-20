from send_all import Sender, DT_FORMAT

default_sender = Sender()


def send_one(record):
    name = record.agent.name
    status = record.status
    created_at = record.created_at.strftime(DT_FORMAT)
    template = "{} status changed to: {} at {}"
    msg = template.format(name, status, created_at)
    default_sender._send(msg, msg)
    print(msg)