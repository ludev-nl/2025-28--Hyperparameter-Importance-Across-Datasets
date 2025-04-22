import pandas as pd
from typing import Dict
import io
import openmlfetcher


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

def DFtoDropdownDict():
    df = openmlfetcher.fetch_flows()
    print(df)
    optionslist = []
    for index, row in df.iterrows():
        lable = str(index) +'.' +str(row['name'])+ '.'+ str(row['version'])
        dic = dict(lable=lable, id=index, name = row['name'], version=row['version'])
        optionslist.append(dic)
    print (optionslist)
    return(optionslist)
DFtoDropdownDict()