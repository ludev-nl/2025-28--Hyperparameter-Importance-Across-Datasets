import pandas as pd
import io

def dictDFtoJSON(frames):
    newdict = {}
    for key, item in frames.items():
        newdict[key] = [item.to_json(index=False)]  # Initialize list and append JSON string
    return newdict

def dictJSONtoDF(JsonDict):
    newdict = {}
    for key, item in JsonDict.items():
        value = pd.read_json(io.StringIO(item[0]))  # Read the JSON string into DataFrame
        newdict[key] = value  # Directly store the DataFrame
    return newdict
