import gisflu
from typing import List, Literal


def gisaid_download(
    user: str,
    password: str,
    gisaid_ids: list[str],
    output: str,
    download_type: Literal["dna", "protein", "metadata"],
    segs: List[Literal["PB2", "PB1", "PA", "HA", "NP", "NA", "MP", "NS"]],
) -> None:
    """
    Download seqs or metadata from GISAID EpiFlu to specified file.

    input: GISAID EpiFlu credentials, segments, path to output file, list of EPI_ISL_* IDs.
    output: None. User-specified file containing downloaded (meta)data.
    """
    cred = gisflu.login(user, password)
    gisflu.download(cred, gisaid_ids, downloadType=download_type, segments=segs, filename=output)
