# zendesk-status-notifier
Small python app for sending email notifications on zendesk agent's status change

create config.py in directory:
ZENDESK_EMAIL = "example@example.com"
ZENDESK_PASSWORD = "password"
ZENDESK_SUBDOMAIN = "subdomain"
ZENDESK_AGENTS = (
    ('0000000', "Alice"),
    ('1111111', "Bob"),
)
MAILGUN_API_HOST = 'mg.example.com'
MAILGUN_API_KEY = 'key-e1x2a3m4p5l6e'
MAILGUN_EMAIL = 'Status <mailgun@mg.example.com>'
EMAIL_ADDR = 'F F <john@example.com>'
MAILGUN_CC_LIST = ['ceo@example.com', 'mary@example.com']
DEBUG_SEND_ALL = False
STACK_SIZE = 4