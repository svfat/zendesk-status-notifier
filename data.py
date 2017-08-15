from config import ZENDESK_AGENTS
from pony.orm import Database, Required, Set, db_session
from datetime import datetime

db = Database()
db.bind(provider='sqlite', filename='database.sqlite', create_db=True)

class GetOrCreateMixin:
    @classmethod
    def get_or_create(cls, **kwargs):
        r = cls.get(**kwargs)
        if r is None:
            return cls(**kwargs), True
        else:
            return r, False
# models
class Agent(db.Entity, GetOrCreateMixin):
    agent_id = Required(str, unique=True)
    name = Required(str, unique=True)
    records = Set('Record')


class Record(db.Entity, GetOrCreateMixin):
    created_at = Required(datetime)
    status = Required(str)
    agent = Required('Agent')

db.generate_mapping(create_tables=True)


# intitial data
@db_session
def create_agents():
    for agent_id, name in ZENDESK_AGENTS:
        Agent.get_or_create(agent_id=agent_id, name=name)


# methods
@db_session
def add_record(agent_id, status):
    created_at = datetime.now()
    agent = Agent.get(agent_id=agent_id)
    Record(created_at=created_at, status=status, agent=agent)

