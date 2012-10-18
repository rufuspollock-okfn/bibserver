from bibserver.core import app, login_manager, current_user

def read(account, collection):
    return True

def update(account, collection):
    allowed = not account.is_anonymous() and ( collection.owner == account.id or not collection.owner )
    if not account.is_anonymous():
        if account.id in app.config['SUPER_USER']:
            allowed = True
    return allowed

def create(account, collection):
    return not account.is_anonymous()

