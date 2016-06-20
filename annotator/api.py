from annotator.models import *
from annotator import app, data_handle, db
from flask import request, jsonify, session, abort
import json


@app.route('/<string:username>/annotations')
def api_annotations(username):
    res = {i.video_id:i.state for i in Annotation.objects(annotator=username)}
    return jsonify(res)


@app.route('/<string:username>/annotations/<string:video_id>',
           methods=['POST', 'PUT', 'GET'])
def api_article(username, video_id):
    if not session.get('logged_in', False) and session.get('permission')=='admin':
        return abort(403)

    if request.method == 'POST' or request.method == 'PUT':
        data = request.data.decode()
        data = json.loads(data)
        name = data['username']
        arousal = data['arousal']
        valence = data['valence']
        state = data['state']
        comment = data['comment']
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
        annotation.state = state
        annotation.comment = comment
        annotation.save()
        return jsonify(message='Annotation saved!')
    else:
        annotation = Annotation.objects.get(annotator=username,
                                            video_id=video_id)
        return annotation_to_json(annotation)


def annotation_to_json(annotation):
    video_id = annotation.video_id
    # Don't forget to sort the values by key...
    state = annotation.state
    comment = annotation.comment
    emotion = annotation.emotion
    # If you also want to return the image urls, uncomment that line
    # image_urls = data_handle.image_urls(video_id)
    annotator = annotation.annotator
    frames = dict()
    for key in sorted(list(annotation.valence.keys())):
        frames[key] = {'valence':annotation.valence[key], 'arousal':annotation.arousal[key]}
    data = {'video_id':video_id, 'annotator':annotator, 'emotion':emotion, 'comment':comment, 'frames':frames}
    return data