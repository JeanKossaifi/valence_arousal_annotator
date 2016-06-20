from annotator.models import *
from annotator import app, data_handle, db
import json
from functools import wraps
from flask import Flask, render_template, request, session, flash, url_for, redirect, jsonify, abort


def add_user(username, password, admin=0):
    """ Adds a user, and creates annotations in the database for that user and the existing data

    Args:
        username: str
        password: str
        admin: {0, 1}, default is 0
            if 1, user is given administration rights

    Returns:
        str: status (success of failure)
    """
    try:
        if admin:
            permission='admin'
        else:
            permission='user'
        user = User.create(name=username, password=password, permission=permission)
        user.save()
        for i, (video_id, valence, arousal, emotion) in enumerate(data_handle.init_valence_arousal_it()):
            print('adding video {}'.format(video_id))
            annotation = Annotation(video_id=video_id,
                                    valence=valence,
                                    arousal=arousal,
                                    emotion=emotion,
                                    annotator=username)
            annotation.save()
        print('processed {} videos'.format(i))
        return 'User {} has been successfully created.'.format(username)
    except db.NotUniqueError:
        return 'User {} already exists.'.format(username)


def update_users_data():
    """ Updates the database data for the users by adding potential new videos in the disk data folder.

    Returns: str (status)

    """
    for user in User.objects.all():
        username = user.name
        for i, (video_id, valence, arousal, emotion) in enumerate(data_handle.init_valence_arousal_it()):
            print('updating video {}'.format(video_id))
            try:
                Annotation.objects.get(video_id=video_id, annotator=username)
            except Annotation.DoesNotExist:
                annotation = Annotation(video_id=video_id,
                                        valence=valence,
                                        arousal=arousal,
                                        emotion=emotion,
                                        annotator=username)
                annotation.save()
    return 'Users data successfully updated'


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        session.get('logged_in')
        if not session.get('logged_in', False):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


def login_user(username, password):
    """ checks password and if correct logs the user in by setting the session variables.

    Args:
        username: str
        password: str

    Returns: bool
        True if login success, False otherwise.
    """
    try:
        user = User.objects.get(name=username)
    except User.DoesNotExist:
        return False

    if user.check_password(password):
        session['name'] = username
        session['permission'] = user.permission
        session['logged_in'] = True
        return True
    else:
        logout_user()
        return False


def logout_user():
    """Logs out a user by resetting the session variables.
    """
    session['logged_in'] = False
    session['permission'] = ''
    session['name'] = ''


@app.route('/logout/', methods=['GET', 'POST'])
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/', methods=['GET'])
def to_login():
    return redirect(url_for('login'))

@app.route('/login/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        name = request.form.get('username', 'Default')
        password = request.form.get('password', 'Default')
        if login_user(name, password):
            return redirect(url_for('home'))
        flash('Incorrect password')
    return render_template('login.html')


@app.route('/change_password/', methods=['GET', 'POST'])
def change_password():
    if request.method == 'POST':
        name = session['name']
        old_password = request.form.get('old_password', '')
        new_password = request.form.get('new_password', '')
        user = User.objects.get(name=name)
        if user.check_password(old_password):
            user.set_password(new_password)
            user.save()
            flash('Password successfully changed!')
            return redirect(url_for('home'))

        else:
            flash('Current password wrong')
            return redirect(url_for('change_password'))
    else:
        return render_template('change_password.html')


@app.route('/admin', methods=['GET'])
@login_required
def admin():
    return render_template('admin.html', users=[user for user in User.objects(name__ne=session['name'])])


@app.route('/delete_user/<string:username>', methods=['GET', 'POST'])
@login_required
def delete_user(username=None):
    annotation = Annotation.objects(annotator=username)
    if len(annotation) > 0:
        annotation.delete()
    try:
        user = User.objects.get(name=username)
        user.delete()
    except User.DoesNotExist:
        pass
    return redirect(url_for('admin'))


@app.route('/register', methods=['GET', 'POST'])
@login_required
def register():
    if session['permission'] != 'admin':
        return redirect(url_for('home'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if request.form.get('admin', None) is not None:
            admin=1
        else:
            admin=0
        msg = add_user(username, password, admin=admin)
        flash(msg)
        return redirect('home')
    return render_template('register.html')


@app.route('/home')
@login_required
def home():
    name = session['name']
    n_videos = len(Annotation.objects(annotator=name))
    done = len(Annotation.objects(annotator=name, state='done'))
    todo = len(Annotation.objects(annotator=name, state='todo'))
    check = len(Annotation.objects(annotator=name, state='check'))
    not_done = len(Annotation.objects(annotator=name, state__ne='done'))
    stats = {'n_videos':n_videos, 'todo':todo, 'check':check, 'done':done, 'not_done':not_done}
    return render_template('home.html', stats=stats)


@app.route('/_save_annotations', methods=['POST'])
@login_required
def _save_annotations():
    data = request.get_json()
    arousal = json.loads(data['arousal'])
    valence = json.loads(data['valence'])
    state = json.loads(data['state'])
    comment = json.loads(data['comment'])
    emotion = data['emotion']
    name = session['name']
    video_id = session['video_id']
    annotation = Annotation.objects.get(annotator=name, video_id=video_id)
    for i, key in enumerate(sorted(annotation.arousal.keys())):
        if arousal[i] is not None:
            annotation.arousal[key] = float(arousal[i])
        else:
            annotation.arousal[key] = None
    for i, key in enumerate(sorted(annotation.valence.keys())):
        if valence[i] is not None:
            annotation.valence[key] = float(valence[i])
        else:
            annotation.valence[key] = None
    annotation.emotion=emotion
    annotation.state=state
    annotation.comment=comment
    annotation.save()
    return jsonify(msg='saved')


@app.route('/annotate/')
@app.route('/annotate/state/<string:state>')
@app.route('/annotate/<string:video_id>')
@login_required
def annotate(video_id=None, state=None):
    username = session['name']
    if video_id is None:
        if state is None:
            annotations = Annotation.objects(annotator=username)
        else:
            annotations = Annotation.objects(annotator=username, state=state)
        n_videos = len(annotations)
        if n_videos == 0:
            return redirect(url_for('finished', state=state))
        from random import randint
        ind = randint(0, n_videos - 1)
        annotation = annotations[ind]
        video_id = annotation.video_id
    else:
        try:
            annotation = Annotation.objects.get(annotator=username, video_id=video_id)
        except Annotation.DoesNotExist:
            flash('video with id {} does not exist'.format(video_id))
            return redirect(url_for('home'))

    valence = [annotation.valence[i] for i in sorted(annotation.valence.keys())]
    arousal = [annotation.arousal[i] for i in sorted(annotation.arousal.keys())]
    state = annotation.state
    comment = annotation.comment
    if video_id is None:
        return redirect(url_for('finished', state=state))
    img_names = data_handle.image_urls(video_id)
    session['video_id'] = video_id
    return render_template('annotate.html', username=username,
                           img_names=img_names,
                           valence=valence,
                           arousal=arousal,
                           emotion=annotation.emotion,
                           state=state,
                           video_id=video_id,
                           comment=comment)


@app.route('/finished/')
@app.route('/finished/<string:state>')
@login_required
def finished(state=None):
    if state is not None:
        msg = 'You have annotated all the videos from state {}.'.format(state)
    else:
        msg = 'You have annotated all the videos.'
    return render_template('finished.html', msg=msg)


