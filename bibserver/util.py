from urllib import urlopen, urlencode
import md5
import re
from unicodedata import normalize
from functools import wraps
from flask import request, current_app


def jsonp(f):
    """Wraps JSONified output for JSONP"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        callback = request.args.get('callback', False)
        if callback:
            content = str(callback) + '(' + str(f(*args,**kwargs).data) + ')'
            return current_app.response_class(content, mimetype='application/javascript')
        else:
            return f(*args, **kwargs)
    return decorated_function


# derived from http://flask.pocoo.org/snippets/45/ (pd) and customised
def request_wants_json():
    best = request.accept_mimetypes.best_match(['application/json', 'text/html'])
    if best == 'application/json' and request.accept_mimetypes[best] > request.accept_mimetypes['text/html']:
        best = True
    else:
        best = False
    if request.values.get('format','').lower() == 'json' or request.path.endswith(".json"):
        best = True
    return best
        

# derived from http://flask.pocoo.org/snippets/5/ (public domain)
# changed delimiter to _ instead of - due to ES search problem on the -
_punct_re = re.compile(r'[\t !"#$%&\'()*\-/<=>?@\[\\\]^_`{|},.]+')
def slugify(text, delim=u'_'):
    """Generates an slightly worse ASCII-only slug."""
    result = []
    for word in _punct_re.split(text.lower()):
        word = normalize('NFKD', word).encode('ascii', 'ignore')
        if word:
            result.append(word)
    return unicode(delim.join(result))


# get gravatar for email address
def get_gravatar(email, size=None, default=None, border=None):
    email = email.lower().strip()
    hash = md5.md5(email).hexdigest()
    args = {'gravatar_id':hash}
    if size and 1 <= int(size) <= 512:
        args['size'] = size
    if default: args['default'] = default
    if border: args['border'] = border

    url = 'http://www.gravatar.com/avatar.php?' + urlencode(args)

    response = urlopen(url)
    image = response.read()
    response.close()

    return image

