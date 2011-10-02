from bibserver.core import current_user

def read(account, collection):
    return True

def update(account, collection):
    allowed = not account.is_anonymous() and collection.owner.id == account.id
    return allowed

def create(account, collection):
    return not account.is_anonymous()

