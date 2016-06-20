import datetime
from annotator import db
from werkzeug.security import check_password_hash, generate_password_hash


class User(db.Document):
    created_at = db.DateTimeField(default=datetime.datetime.now, required=True)
    name = db.StringField(max_length=255, required=True, unique=True, pk=True)
    password_hash = db.StringField(max_length=255, default='')
    permission = db.StringField(max_length=255, default='user')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @classmethod
    def create(cls, name, password, permission='user'):
        user = User(name=name, permission=permission)
        user.set_password(password)
        return user

    meta = {
        'indexes': ['-created_at', 'name']
    }


class Annotation(db.Document):
    created_at = db.DateTimeField(default=datetime.datetime.now, required=True)
    video_id = db.StringField(max_length=255, required=True, unique=False)
    state = db.StringField(default='todo', required=True)
    annotator = db.StringField(max_length=255, required=True)
    arousal = db.DictField()
    valence = db.DictField()
    emotion = db.StringField(default='unknown')
    comment = db.StringField()
    actor = db.StringField()

    meta = {
        'allow_inheritance': True,
        'indexes': ['-created_at', 'video_id', 'annotator', 'state'],
        'ordering': ['-created_at', 'video_id', 'annotator']
    }
