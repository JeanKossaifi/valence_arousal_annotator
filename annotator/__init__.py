from flask import Flask
from flask.ext.mongoengine import MongoEngine
from annotator.data import Data

app = Flask(__name__)
app.config["MONGODB_SETTINGS"] = {'DB': 'annotations'}
app.config["SECRET_KEY"] = "d3v_annotations_k3y"

db = MongoEngine(app)
data_handle = Data()

def add_api():
    from annotator import api


def add_webapp():
    from annotator import views


add_webapp()
add_api()

if __name__ == '__main__':
    app.run()
