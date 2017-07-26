#!/usr/bin/env python
import logging

logger = logging.getLogger(__name__)
from core import agents, storage
from config import DEBUG_SEND_ALL, STACK_SIZE

logger.debug(f"DEBUG_SEND_ALL {DEBUG_SEND_ALL}, STACK_SIZE {STACK_SIZE}")
for agent in agents:
    current_status = agent.get_talk_status()
    last_status = storage.get_last_status(agent=agent)

    if DEBUG_SEND_ALL:
        storage.add_status(agent=agent, status=current_status, size=STACK_SIZE)
    elif current_status != last_status:
        storage.add_status(agent=agent, status=current_status, size=STACK_SIZE)

# print(agent.get_chat_availability())2
