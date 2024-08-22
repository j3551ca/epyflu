# epyflu

epyflu assists in uploading sequences and associated metadata to the GISAID EpiFlu database from command line while accessioning GISAID IDs of uploaded samples in a local SQLite database that can be queried. It can be installed by pip or conda. epyflu has the option to be run interactively.

## Input

Here, a **dataset** is defined as one multifasta file (\*.fa or \*.fasta) of sequences and one corresponding metadata file (\*.csv). epyflu requires that **each pair** of metadata and sequences **are named the same** (ex. 20240731-131521.fa & 20240731-131521.csv). If there is a need to upload multiple datasets simultaneously, simply specify the parent directory containing datasets to be uploaded.


## Quick-Start

```
pip install epyflu

import epyflu

epyflu --input /path/to/dataset(s)/to/upload 
```


## Usage 

```
p
```
