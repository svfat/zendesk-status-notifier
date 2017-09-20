#!/usr/bin/env python
from core import agents
from config import DEBUG_SEND_ALL
from send_one import send_one

print(f"DEBUG_SEND_ALL {DEBUG_SEND_ALL}")
for agent in agents:
    current_status = agent.get_talk_status()
    last_status = agent.get_last_status()
    print(f'agent: {agent.agent_name}, status: {current_status}, last status: {last_status}')
    if current_status != last_status or DEBUG_SEND_ALL:
        record = agent.save_current_status()
        if record:
            send_one(record)
        else:
            print(f"Status changed to {current_status}. We don't track it")
    else:
        print(f"Stasus doesn't changed")
# print(agent.get_chat_availability())2
