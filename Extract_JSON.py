import json
# from pathlib import Path, PureWindowsPath

def getJSON(filename):
    data = open(filename + ".json")
    data = json.load(data)
    return data
