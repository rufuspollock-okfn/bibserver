from bibserver.core import current_user

def read(account, collection):
    return True

def update(account, collection):
    allowed = not account.is_anonymous() and collection["owner"] == account.id
    if account.id in collection.get('_admins',[]):
        allowed = True
    #if account.is_su:
    #    allowed = True
    return allowed

def create(account, collection):
    return not account.is_anonymous()

