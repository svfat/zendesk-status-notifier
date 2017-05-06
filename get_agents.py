#!/usr/bin/env python
from core import zc

users = []
exclude = ['end-user']
include = ['agent']
for user in zc.users():
    role = user.role
    if role in exclude:
        continue
    if role in include:
        print(user.id, user.name)
        users.append(user)

