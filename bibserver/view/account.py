import uuid

from flask import Blueprint, request, url_for, flash, redirect, abort
from flask import render_template
from flask.ext.login import login_user, logout_user, current_user
from flask.ext.wtf import Form, TextField, TextAreaField, PasswordField, validators, ValidationError

from bibserver.core import app, login_manager
import bibserver.dao as dao
import bibserver.util as util

blueprint = Blueprint('account', __name__)


@blueprint.route('/')
def index():
    if current_user.is_anonymous():
        abort(401)
    users = dao.Account.query(sort={'_id':{'order':'asc'}},size=1000000)
    if users['hits']['total'] != 0:
        accs = [dao.Account.get(i['_source']['_id']) for i in users['hits']['hits']]
        # explicitly mapped to ensure no leakage of sensitive data. augment as necessary
        users = []
        for acc in accs:
            user = {"collections":len(acc.collections),"_id":acc["_id"]}
            try:
                user['_created'] = acc['_created']
                user['description'] = acc['description']
            except:
                pass
            users.append(user)
    if util.request_wants_json():
        resp = make_response( json.dumps(users, sort_keys=True, indent=4) )
        resp.mimetype = "application/json"
        return resp
    else:
        return render_template('account/users.html',users=users)


class LoginForm(Form):
    username = TextField('Username', [validators.Required()])
    password = PasswordField('Password', [validators.Required()])

@blueprint.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm(request.form, csrf_enabled=False)
    if request.method == 'POST' and form.validate():
        password = form.password.data
        username = form.username.data
        user = dao.Account.get(username)
        if user and user.check_password(password):
            login_user(user, remember=True)
            flash('Welcome back ' + user.id, 'success')
            return redirect('/'+user.id)
        else:
            flash('Incorrect username/password', 'error')
    if request.method == 'POST' and not form.validate():
        flash('Invalid form', 'error')
    return render_template('account/login.html', form=form, upload=app.config['ALLOW_UPLOAD'])


@blueprint.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))


def existscheck(form, field):
    test = dao.Account.get(form.w.data)
    if test:
        raise ValidationError('Taken! Please try another.')

class RegisterForm(Form):
    w = TextField('Username', [validators.Length(min=3, max=25),existscheck])
    n = TextField('Email Address', [validators.Length(min=3, max=35), validators.Email(message='Must be a valid email address')])
    s = PasswordField('Password', [
        validators.Required(),
        validators.EqualTo('c', message='Passwords must match')
    ])
    c = PasswordField('Repeat Password')
    d = TextAreaField('Describe yourself')

@blueprint.route('/register', methods=['GET', 'POST'])
def register():
    # TODO: re-enable csrf
    form = RegisterForm(request.form, csrf_enabled=False)
    if request.method == 'POST' and form.validate():
        api_key = str(uuid.uuid4())
        account = dao.Account(
            _id=form.w.data, 
            email=form.n.data,
            description = form.d.data,
            api_key=api_key
        )
        account.set_password(form.s.data)
        account.save()
        login_user(account, remember=True)
        flash('Thanks for signing-up', 'success')
        return redirect('/'+account.id)
    if request.method == 'POST' and not form.validate():
        flash('Please correct the errors', 'error')
    return render_template('account/register.html', form=form)

