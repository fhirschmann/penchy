import os
import json


TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')


def get_json_data(name):
    """
    Return the content of the json data file with name.

    :param name: name of the json data file without extension
    :returns: content of json file
    """
    with open(os.path.join(TEST_DATA_DIR, name + '.json')) as f:
        ob = json.load(f)
    return ob
