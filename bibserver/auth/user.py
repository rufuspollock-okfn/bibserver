from bibserver.core import app, login_manager, current_user

def update(account, user):
    allowed = not account.is_anonymous() and user.id == account.id
    if not account.is_anonymous():
        if account.id in app.config['SUPER_USER']:
            allowed = True
    return allowed

def is_super(account):
    return not account.is_anonymous() and account.id in app.config['SUPER_USER']
