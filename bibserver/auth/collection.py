from bibserver.core import app, login_manager, current_user

def read(account, collection):
    return True

def update(account, collection):
    allowed = not account.is_anonymous() and collection["owner"] == account.id
    if not account.is_anonymous():
        try:
            if account.id in collection['_admins']:
                allowed = True
        except:
            pass
        if account.id in app.config['SUPER_USER']:
            allowed = True
    return allowed

def create(account, collection):
    return not account.is_anonymous()

