import config as cfg
from revolt import Member

async def change_user_role(member: Member, roles : list[str], *, replace=True):
    new_roles = []
    
    for role in roles:
        if role in cfg.ROLE_IDS:
            new_roles.append(cfg.ROLES[role])

    if not replace:
        current_roles = member.roles

        for role in current_roles:
            new_roles.append(role)

    await member.edit(roles=new_roles)