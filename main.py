#!/usr/bin/env python
from core import agents
from config import DEBUG_SEND_ALL

print(f"DEBUG_SEND_ALL {DEBUG_SEND_ALL}")
for agent in agents:
    current_status = agent.get_talk_status()
    last_status = agent.get_last_status()
    print(f'agent: {agent.agent_name}, status: {current_status}, last status: {last_status}')
    if current_status != last_status or DEBUG_SEND_ALL:
        agent.save_current_status()
    else:
        print(f"Stasus doesn't changed")
# print(agent.get_chat_availability())2
