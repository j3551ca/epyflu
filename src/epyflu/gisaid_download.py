import gisflu
from typing import List, Literal

def gisaid_download(user: str, password: str, gisaid_ids: list[str], output: str, download_type: Literal["dna", "protein", "metadata"], 
segs: List[Literal["PB2", "PB1", "PA", "HA", "NP", "NA", "MP", "NS"]]) -> None:

    cred = gisflu.login(user, password)
    gisflu.download(cred, gisaid_ids, downloadType=download_type, segments=segs,
    filename=output)

