# Set the path
import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask.ext.script import Manager, Server, Shell
from annotator import app
import json

from annotator.models import *
from annotator import data_handle
from annotator.views import add_user, update_users_data
from annotator.api import annotation_to_json

manager = Manager(app)


def _make_context():
    return dict(app=app, db=db, data_handle=data_handle, Annotation=Annotation, User=User)
manager.add_command("shell", Shell(make_context=_make_context))

@manager.option('-u', '--username', dest='username', default='admin')
@manager.option('-p', '--password', dest='password', default='admin')
@manager.option('-a', '--admin', help='If 1 user is given admin rights.', dest='admin', default=1)
def init(username='admin', password='admin', admin=1):
    """(re-)initialises the database and sets a new user

    Parameters:
    username: str
    password: str
    admin: {0, 1}, default=1
        if 1 the user is made admin otherwise simple user
    """
    Annotation.drop_collection()
    User.drop_collection()
    print('Database init.')
    add_user(username, password, admin=admin)
    if admin:
        print('ADMIN User {} created and initialised'.format(username))
    else:
        print('User {} created and initialised'.format(username))


@manager.command
def new_user(username, password, admin=0):
    """Adds a new user to the app

    Parameters:
    username: str
    password: str
    admin: {0, 1}, default=0
        if 1 the user is made admin otherwise simple user

    """
    add_user(username, password, admin=admin)
    if admin:
        print('ADMIN User {} created and initialised'.format(username))
    else:
        print('User {} created and initialised'.format(username))


@manager.command
def update_data():
    """
    Updates the data to be annotated for all users
    """
    update_users_data()


@manager.command
def save_annotations(folder, annotator):
    """Save the database as one json file per video

    Parameters:
    folder: str
        absolute path to the folder in which to save the data
    annotator: str
        name of the annotator whose annotation to save
    """
    for annotation in Annotation.objects(annotator=annotator):
        name = str(annotation.video_id)
        with open(os.path.join(folder, name + '.json'), 'w') as outfile:
                json.dump(annotation_to_json(annotation), outfile, indent=2)

# To save the db in a file:
# mongoexport -d annotations -c annotation -o '/data/AnnotationAFEW/savefile.json'
# To import back:
# mongoimport -d annotations -c annotation --file '/data/AnnotationAFEW/savefile.json'


# Turn on debugger by default and reloader
manager.add_command("runserver", Server(
    use_debugger = True,
    use_reloader = True,
    port = 55555,
    host = '0.0.0.0')
)

if __name__ == "__main__":
    manager.run()
