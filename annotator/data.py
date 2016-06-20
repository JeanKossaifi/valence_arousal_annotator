from flask import url_for
from pathlib import Path
import json
from collections import OrderedDict


def read_sequence_annotation(json_filename):
    """Reads the annotations corresponding to a sequence (video)
    Parameters
    ----------
    json_filename: str

    Returns
    -------
    OrederedDict
        The resulting dictionary is ordered, from the first to the last frame ;)

    Notes
    -----
    Annotations are assumed to be in the following format:
    {
        'random info': 'random value',
        ...
        'subset': 'training',
        'frames': {
            'frame_number': {
              'key_1': val_1,
              ...
              'key_m': val_n
            },
            '2': {
              'key_1': val_1,
              ...
              'key_m': val_n
            },
            ...

            'NNN': {
              'key_1': val_1,
              ...
              'key_m': val_n
            }
        }
    }
    """
    with open(json_filename, 'r') as f:
        annotations = json.load(f)
    # We really want an OrderedDict, don't trust the user to think of sorting the dict by key
    # (otherwise since keys are integer, the order might be messed up)
    frames_annotations = annotations['frames']
    annotations['frames'] = OrderedDict((key, frames_annotations[key])
                                        for key in sorted(frames_annotations.keys(), key=int))
    return annotations


class Data:
    """ Class to serve the images for each video of the dataset
    """
    def __init__(self, folder='./annotator/static/dataset/data'):
        """
        Parameters
        ----------
        folder   : string, default is 'static/data'
                    Path to the storing folder from the local directory
                    Important, *must not* start by '/' or './'
        """
        self.folder = folder
        self.path = Path(folder)
        self.videos = dict()
        for video_path in self.path.iterdir():
            if video_path.is_dir():
                video_name = video_path.name
                self.videos[video_name] = video_path

    def image_files(self, video_id):
        path = self.videos[video_id]
        img_files = sorted(list(p.relative_to('./annotator/static') for p in path.glob('*.png')),
                           key=lambda x: int(x.stem))
        return img_files

    def image_urls(self, video_id):
        """ Return the urls of the images corresponding to the video_id

        Parameters
        ----------
        video_id: relative path to the folder
                  path from the current directory
        """
        img_files = self.image_files(video_id)
        urls = [url_for('static', filename=filename) for filename in img_files]
        return urls

    def __iter__(self):
        """ Iterator on the video ids
        """
        for video_id in self.videos:
            yield video_id

    def init_valence_arousal_it(self):
        """ Iterator on pre-filled annotations
        """
        for video_id, path in self.videos.items():
            img_files = self.image_files(video_id)
            n_frames = len(img_files)
            valence = {img_files[i].stem: None for i in range(n_frames)}
            arousal = {img_files[i].stem: None for i in range(n_frames)}
            emotion = ''
            try: # If an annotation file exists, try to use it to fill the values
                path = self.videos[video_id]
                annotation_path = path.joinpath(video_id + '.json')
                if annotation_path.exists():
                    annotations = read_sequence_annotation(annotation_path.as_posix())
                    for frame, d in annotations['frames'].items():
                        valence[frame] = d['valence']
                        arousal[frame] = d['arousal']
                    emotion = annotations['emotion']
            except KeyboardInterrupt:
                raise
            except:
                print('Impossible to read the annotations for video {} from {}.'.format(video_id, path))
            yield (video_id, valence, arousal, emotion)
