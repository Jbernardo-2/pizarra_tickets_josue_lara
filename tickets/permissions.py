from accounts.models import Profile


def get_role(user):
    if not user.is_authenticated:
        return None
    if user.is_superuser:
        return Profile.Role.ADMIN
    profile = getattr(user, 'profile', None)
    return profile.role if profile else Profile.Role.USER


def is_admin(user):
    return get_role(user) == Profile.Role.ADMIN


def is_supervisor(user):
    return get_role(user) == Profile.Role.SUPERVISOR


def is_technician(user):
    return get_role(user) == Profile.Role.TECHNICIAN


def is_staff_manager(user):
    return get_role(user) in {Profile.Role.SUPERVISOR, Profile.Role.ADMIN}


def can_view_ticket(user, ticket):
    role = get_role(user)
    if role in {Profile.Role.SUPERVISOR, Profile.Role.ADMIN}:
        return True
    if role == Profile.Role.TECHNICIAN:
        return ticket.assigned_to_id == user.id
    return ticket.created_by_id == user.id


def can_edit_ticket(user, ticket):
    role = get_role(user)
    if role in {Profile.Role.SUPERVISOR, Profile.Role.ADMIN}:
        return True
    return ticket.created_by_id == user.id and ticket.status == ticket.Status.PENDING


def can_comment_ticket(user, ticket):
    return can_view_ticket(user, ticket)


def can_upload_file(user, ticket):
    role = get_role(user)
    return role in {Profile.Role.TECHNICIAN, Profile.Role.SUPERVISOR, Profile.Role.ADMIN} and can_view_ticket(user, ticket)


def can_update_work(user, ticket):
    role = get_role(user)
    return role in {Profile.Role.TECHNICIAN, Profile.Role.SUPERVISOR, Profile.Role.ADMIN} and can_view_ticket(user, ticket)
