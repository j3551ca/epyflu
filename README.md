# epyflu

Consolidated upload, download, and record-keeping of Influenza isolates with GISAID EpiFlu.

epyflu assists in uploading sequences and associated metadata to the GISAID EpiFlu database from command line while accessioning GISAID IDs of uploaded samples in a local SQLite database that can be queried. The local SQLite database is updated with the release status of isolates each time the database module is run. Metadata as well as protein & DNA sequences may be downloaded from GISAID EpiFlu to xls and fasta formats, respectively. This package is a wrapper of the EpiFlu CLI executable and [gisflu](https://github.com/william-swl/gisflu/tree/master). It can be installed by pip or conda. epyflu has the option to be run interactively.

## Table of Contents

- [Overview](#epyflu)
- [Quick-Start Guide](#quick-start)
- [Dependencies](#dependencies)
- [Installation](#installation)
- [Usage](#usage)
- [Input](#input)
- [Output](#output)

## Quick-Start

```
pip install epyflu

import epyflu

epyflu 
```

## Dependencies


## Installation


```

```

## Usage 

Run epyflu interactively and follow the prompts 
```
epyflu 
```

Run epyflu specifying CLI options 
```
epyflu upload --input /path/to/dataset/dir --username myname --password 6543adkg --clientid 1234id-hsaj --log /path/to/store/gisaid/logs --db /my/sqlite/flu.db
```

Optionally, specify username, password, and/or client ID as environmental variables
```
export EPYFLU_USER="myname"
export EPYFLU_PASSWORD="6543adkg"
export EPYFLU_CLIENTID="1234id"
```

then run interactively, noninteractively, or any combination of the two. In this example, since the environmental variables for `password` & `client-id` are set and `username` & `log` variables are entered on the command line, the user will be prompted for `input` & `db` file
```
epyflu upload --username myname --log /path/to/store/gisaid/logs
```

`epyflu` has three subcommands: `upload`, `update`, and `download`. 

Each of the subcommands is run independently. `update` can be run periodically *after* an `upload` has occurred and a SQLite database has been created. It is recommended that the same SQLite database file be used, to centralize records

### upload

The `upload` module searches for pairs of metadata and sequences named the same (ex. 20240731-131521.fa & 20240731-131521.csv; 20240801-162045.fasta & 20240801-162045.csv), passes user inputs to the GISAID EpiFlu executable to upload datasets, then uses GISAID json log files of successful uploads along with associated metadata files to create 2 SQLite tables: `isolate_meta` & `segments_seqs`. A SQLite database is stored in a \*.db file, which if not already present will be created at the time the upload subcommand is called or appended, otherwise. It is recommended to use the same \*.db file across uploads to ensure comprehensive collation of uploaded isolates. In this context, upload is defined as sent + successfully rececived by GISAID EpiFlu (ie. an isolate that was sent but rejected will *not* be recorded in your SQLite database). 

### update

There is often a lag between the time an isolate is uploaded to GISAID EpiFlu and publicly released. The `upload` subcommand allows GISAID IDs to be recorded in a local SQLite database at the time of upload, while the `update` subcommand allows the user to periodically query the GISAID EpiFlu database for the GISAID isolate IDs initially uploaded & recorded to see whether they are available.

This is done by collecting GISAID IDs from the SQLite database and searching EpiFlu using gisflu's [search function](https://github.com/william-swl/gisflu/blob/master/src/gisflu/browse.py). Results are then converted into a temporary SQLite table, left-joining the existing `isolate_meta` database table, and updating the `released` variable/ attribute if both `isolate_name` & `gisaid_id` are matched.

 The GISAID IDs (EPI_ISL_*) that are the most recent record of isolate ID groups and not yet released are collected as the query. For example, if an isolate named A/British_Columbia/PHL-124/2022 were uploaded, deleted, then re-uploaded, there would be multiple recorded uploads for the isolate with two different GISAID IDs in the SQLite database. Only the most recent GISAID ID in this example will be searched for in EpiFlu. This assumes 1\) a unique relationship between the isolate and isolate ID, regardless of how many times it is uploaded 2\) only one instance of isolate ID may be present on GISAID EpiFlu at a time (ie. it would need to be deleted prior to being accepted under the same name and assigned a new GISAID ID) 3\) the most recent submission is the GISAID ID that will be publicly released. It is possible to have multiple of the same isolate IDs, each with different GISAID IDs, and for the released column to be 'Yes' depending on when GISAID EpiFlu was queried. In the case of multiple identical isolate IDs that have been released, the most recently submitted record will be what is currently available on GISAID EpiFlu.  

### download

This subcommand allows variables to be interactively passed to the download function of [gisflu](https://github.com/william-swl/gisflu/tree/master). The user specifies which combination of segments and what type of data (metadata, dna, or protein seqs) to download for given isolate IDs (EPI_ISL_*). The file that data is written to can be either \*.xls for metadata or \*.fa for sequences. The user must enter a list of segments and GISAID isolate IDs separated *only* by commas (ex. HA,NA,NP,PB1).  

## Parameters

| Parameter | Description | Required | Subcommand |
| :--------------- | :--------------- | :--------------- | :--------------- |
| username    | GISAID EpiFlu username.| yes | upload,update,download |
| password    | GISAID EpiFlu password. | yes | upload,update,download |
| clientid    | GISAID EpiFlu client-id. This is the ID provided by GISAID EpiFlu after one manual upload is completed. | yes | upload |
| input    |The directory containing datasets to be uploaded. A **dataset** is defined as one multifasta file (\*.fa or \*.fasta) of sequences and one corresponding metadata file (\*.csv). epyflu requires that **each pair** of metadata and sequences **are named the same** (ex. 20240731-131521.fa & 20240731-131521.csv). If there is a need to upload multiple datasets simultaneously, simply specify the parent directory containing datasets to be uploaded. | yes | upload |
| dateformat    | Format of dates in GISAID EpiFlu metadata file. | no | upload |
| log    | Absolute path to **directory** to write GISAID EpiFlu logs to. | yes | upload |
| database    | Absolute path to **file** to write SQLite database to (\*.db). | yes | update |
| output    | Absolute path to **file** to write download to (*.xls for meta; *.fa for seqs). | yes | download |
| segments    | List of comma-separated segments to download sequences or metadata for. | no | download |
| gisaid_ids    | List of comma-separated GISAID IDs to download data for (EPI_ISL_1,EPI_ISL_2,EPI_ISL_45). | yes | download |
| download_type    | Type of data to download (metadata,dna,protein). | no | download |

