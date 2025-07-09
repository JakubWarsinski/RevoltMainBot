import config as cfg

from revolt import Member

def on_member_update(before: Member, after: Member):  
    roles_before = {role.name for role in before.roles}
    roles_after = {role.name for role in after.roles}

    added_roles = roles_after - roles_before
    removed_roles = roles_before - roles_after

    counter_roles(added_roles, 1)
    counter_roles(removed_roles, -1)


def counter_roles(role_list, amount):
    for role in role_list:
        if role in cfg.AMOUNT_OF_ROLES:
            cfg.AMOUNT_OF_ROLES[role] += amount