import pandas as pd
import io

def dictDFtoJSON(frames):
    newdict = {key: [item.to_json(index=False)]
               for key, item in frames.items()}
    return newdict

def dictJSONtoDF(JsonDict):
    newdict = {key : pd.read_json(io.StringIO(item[0])) for key, item in JsonDict.items()}
    return newdict
