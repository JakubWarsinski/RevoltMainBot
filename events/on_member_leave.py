import config as cfg
from revolt import Member

def on_member_leave(member: Member):
    roles = (role.name for role in member.roles)

    for role in roles:
        if role in cfg.AMOUNT_OF_ROLES: 
            cfg.AMOUNT_OF_ROLES[role] -= 1