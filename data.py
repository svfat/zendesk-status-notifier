from datetime import datetime, timedelta
from datetime import timezone

from pony.orm import Database, Required, Set, db_session, desc

from config import ZENDESK_AGENTS, DT_FORMAT

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

    @db_session
    def records_for_date(self, dt):
        return list(self.records.select(lambda x: x.created_at >= dt and x.created_at < dt + timedelta(days=1)))

    def get_week_report(self, start_dt=None):
        if not start_dt:
            start_dt = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)-timedelta(hours=7)
        datelist = [start_dt-timedelta(days=x) for x in range(0, 7)]
        result = {date: self.get_total_on_date(date) for date in datelist}
        return result

    def get_day_report(self, dt=None):
        if not dt:
            dt = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)-timedelta(hours=12)
        result = [(r.status, r.created_at-timedelta(hours=7)) for r in self.records_for_date(dt)]
        return result

    def get_total_on_date(self, date):
        AVAILABLE = 'available'
        NOT_AVAILABLE = 'not_available'
        last_status = NOT_AVAILABLE
        start = None
        total = timedelta()
        with db_session():
            for record in self.records.select(lambda x: x.created_at >= date and x.created_at < date + timedelta(days=1)):
                if record.status == AVAILABLE and last_status != AVAILABLE:
                    # start timedelta
                    start = record.created_at
                elif record.status == NOT_AVAILABLE and last_status == AVAILABLE:
                    # end timedelta
                    total += record.created_at - start
                    start = None
                last_status = record.status
        print(f"{self.agent_id}: Total on date {date} - {total}")
        return total

    def get_last_status(self):
        with db_session():
            records = list(self.records.order_by(lambda x: x.id))
            if records:
                record = records[-1]
                print('***', record.created_at)
                return record.status
            else:
                return 'not_available'

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
def get_agents():
    return list(Agent.select())


@db_session
def add_record(agent_id, status):
    created_at = datetime.now()
    print(f"Datetime now {created_at}")
    utc = created_at.replace(tzinfo=timezone.utc)
    print(f"Datetime utc {utc}")
    pdt = utc.astimezone(tz=timezone(timedelta(hours=5)))
    print(f"Datetime pdt {pdt}")
    agent = Agent.get(agent_id=agent_id)
    Record(created_at=pdt, status=status, agent=agent)


@db_session
def get_last_status(agent_id):
    record = Record.select(lambda x: x.agent.agent_id == agent_id).order_by(lambda x: x.created_at).first()
    print('***', record)
    return record.status


@db_session
def get_records_on_dt_range(start_dt=None, end_dt=None):
    if not start_dt:
        yesterday = datetime.now() - timedelta(days=1)
        start_dt = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)+timedelta(hours=7)
        print('start_dt', start_dt)
    if not end_dt:
        end_dt = start_dt + timedelta(hours=24)
    data = Record.select(lambda x: x.created_at >= start_dt and x.created_at <= end_dt) \
        .order_by(lambda x: x.created_at)
    from collections import defaultdict
    result = defaultdict(list)
    for r in data:
        result[r.agent.agent_id].append({
            'dt': r.created_at.strftime(DT_FORMAT),
            'status': r.status,
        })
    from pprint import pprint
    print(start_dt)
    print(end_dt)
    pprint(result)
    return result

@db_session
def convert_tz():
    records = Record.select()
    for record in records:
        record.created_at.replace(tzinfo=None)
