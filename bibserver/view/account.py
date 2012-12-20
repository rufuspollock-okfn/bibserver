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
            user = {"collections":len(acc),"_id":acc["_id"]}
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
        if user is None:
            user = dao.Account.get_by_email(username)
        if user is None:
            flash('Sorry, that user cannot be found', 'error')
        elif user.check_password(password):
            login_user(user, remember=True)
            flash('Welcome back ' + user.id, 'success')
            return redirect('/'+user.id)
        else:
            flash('Incorrect password', 'error')
    if request.method == 'POST' and not form.validate():
        flash('Invalid form', 'error')
    return render_template('account/login.html', form=form, upload=app.config['ALLOW_UPLOAD'])


@blueprint.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))


def existscheck(form, field):
    test = dao.Account.get(form.w.data)
    if test is not None:
        raise ValidationError('Taken! Please try another.')
    elif app.config['ACCOUNT_EMAIL_VALIDATION']:
        test = dao.UnapprovedAccount.get(form.w.data)
        if test is not None:
            raise ValidationError('Sorry! There is already a new account with that username awaiting validation. If you already tried to register, please check your emails and follow the link to enable your account.')

def emailexistscheck(form, field):
    test = dao.Account.get_by_email(form.n.data)
    if test is not None:
        raise ValidationError('Sorry! There is already a user named ' + test.id + ' registered with that email address.')
    elif app.config['ACCOUNT_EMAIL_VALIDATION']:
        test = dao.UnapprovedAccount.get(form.w.data)
        if test is not None:
            raise ValidationError('Sorry! There is already a new account awaiting validation registered with that email address. If you already tried to register, please check your emails and follow the link to enable your account.')

class RegisterForm(Form):
    w = TextField('Username', [validators.Length(min=3, max=25),existscheck])
    n = TextField('Email Address', [validators.Length(min=3, max=35), validators.Email(message='Must be a valid email address'), emailexistscheck])
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
        if app.config['ACCOUNT_EMAIL_VALIDATION'] and not app.config['DEBUG']:
            newaccount = dao.UnapprovedAccount(
                _id = form.w.data, 
                email = form.n.data,
                description = form.d.data,
                api_key = str(uuid.uuid4()),
                validate_key = str(uuid.uuid4())
            )
            newaccount.set_password(form.s.data)
            newaccount.requestvalidation()
            newaccount.save()
            flash('Thanks for signing-up. Please check your email for a validation request. Once you respond your account will become active.', 'success')
        else:
            newaccount = dao.Account(
                _id = form.w.data, 
                email = form.n.data,
                description = form.d.data,
                api_key = str(uuid.uuid4())
            )
            newaccount.set_password(form.s.data)
            newaccount.save()
            login_user(newaccount, remember=True)
            flash('Thanks for signing-up.', 'success')
        return redirect('/'+newaccount.id)
    if request.method == 'POST' and not form.validate():
        flash('Please correct the errors', 'error')
    return render_template('account/register.html', form=form)

