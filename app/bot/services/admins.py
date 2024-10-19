from bot.config import BotConfig

def user_check_admin_str(id: int, cfg: BotConfig) -> str:
    """Check if user corresponds to an admin and returns
    a string.

    Args:
        id (int): telegram user id.
        cfg (BotConfig): bot configuration.

    Returns:
        str: `You are and admin.` in case of admin,
        otherwise it returns `You are not an admin.`.
        In case of the root admin will return `You are
        the root admin.`.
    """
    
    if id == cfg.rootadmin_id:
        return "You are the root admin."
    elif id in cfg.admin_ids:
        return "You are an admin."
    else:
        return "You are not an admin."

def user_check_admin(id: int, cfg: BotConfig) -> tuple[bool, str]:
    """Check if user corresponds to an admin and returns
    a bool.

    Args:
        id (int): telegram user id.
        cfg (BotConfig): bot configuration.

    Returns:
        bool: `True` if user is a administrator, `False` otherwise.
    """
    
    if id == cfg.rootadmin_id:
        return (True, user_check_admin_str(id, cfg))
    elif id in cfg.admin_ids:
        return (True, user_check_admin_str(id, cfg))
    else:
        return (False, user_check_admin_str(id, cfg))
    