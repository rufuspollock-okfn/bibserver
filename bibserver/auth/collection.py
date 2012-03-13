from bibserver.core import current_user
from bibserver.config import config

def read(account, collection):
    return True

def update(account, collection):
    allowed = not account.is_anonymous() and collection["owner"] == account.id
    if account.id in collection.get('_admins',[]):
        allowed = True
    if account.id == config['super_user']:
        allowed = True
    return allowed

def create(account, collection):
    return not account.is_anonymous()

