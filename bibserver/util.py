from urllib import urlopen, urlencode
import md5
import re
from unicodedata import normalize
from functools import wraps
from flask import request, current_app

import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from email.Utils import COMMASPACE, formatdate
from email import Encoders
         

def send_mail(to, _from, subject, text, files=[],server="localhost"):
    assert type(to)==list
    assert type(files)==list
 
    msg = MIMEMultipart()
    msg['From'] = _from
    msg['To'] = COMMASPACE.join(to)
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = subject
 
    msg.attach( MIMEText(text) )
 
    for file in files:
        part = MIMEBase('application', "octet-stream")
        part.set_payload( open(file,"rb").read() )
        Encoders.encode_base64(part)
        part.add_header('Content-Disposition', 'attachment; filename="%s"'
                       % os.path.basename(file))
        msg.attach(part)
 
    smtp = smtplib.SMTP(server)
    smtp.sendmail(_from, to, msg.as_string() )
    smtp.close()


def jsonp(f):
    """Wraps JSONified output for JSONP"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        callback = request.args.get('callback', False)
        if callback:
            content = str(f(*args,**kwargs).data)
            if not content.startswith(str(callback) + '('):
                content = str(callback) + '(' + content + ')'
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
_punct_re = re.compile(r'[\t !"$%&\'()*\-/<=>?@\[\\\]^`{|},.]+')
def slugify(text, delim=u'_'):
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

