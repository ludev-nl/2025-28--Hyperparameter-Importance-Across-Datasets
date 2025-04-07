import pandas as pd
from typing import Dict
import io


def dictDFtoJSON(frames: Dict[int, pd.DataFrame]) \
                -> Dict[str, str]:
    newdict = {key: [item.to_json(index=False)]
               for key, item in frames.items()}
    return newdict


def dictJSONtoDF(JsonDict: Dict[str, str]) \
                -> Dict[int, pd.DataFrame]:
    newdict = {key: pd.read_json(io.StringIO(item[0]))
               for key, item in JsonDict.items()}
    return newdict
