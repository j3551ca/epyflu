#!/usr/bin/env python3
#%%
import os, sys
import argparse
from glob import glob 
import subprocess


def verify_dataset(dataset_path:str) -> dict[str, tuple[str, str]]:

    if not os.path.isdir(dataset_path):
        print(f'Error: The folder {dataset_path} does not exist. Check that spelling and path are accurate.')
        sys.exit(1)
    
    seqs_path = []
    for e in ('*.fasta', '*.fa'):
        seqs_path.extend(glob(os.path.join(dataset_path,'**', e), recursive=True))
    
    seqs = {}
    for file in seqs_path:
        k = os.path.basename(file).rsplit('.', 1)[0]
        if k in seqs.keys():
            print(f'Error: multiple sequence files with the name "{k}" in {dataset_path}*.\nRename with unique name.')
            sys.exit(1)
        seqs[k] = os.path.abspath(file)
    
    # for k, v in seqs.items():
    #     print(k,v)

    metadata_path = glob(os.path.join(dataset_path, '**','*.csv'), recursive=True)

    meta = {}
    for file in metadata_path:
        k = os.path.basename(file).split('.csv')[0]
        if k in meta.keys():
            print(f'Error: multiple metadata files with the name {k} in {dataset_path}.\nRename with unique name.')
            sys.exit(1)
        meta[k] = os.path.abspath(file)
    
    # print(metadata_path)
    # only identically named fasta and meta will be kept
    common_files = set(meta.keys()).intersection(seqs.keys())
    # print(common_files)

    missing = []
    if len(set(seqs.keys())-set(meta.keys())) > 0:
        seqs_missing_meta = set(seqs.keys())-set(meta.keys())
        for k in seqs_missing_meta:
            missing.append(os.path.basename(seqs[k]))
        print(f"Note: The following sequence file(s) are missing metadata and will not be uploaded:\n{missing}")

    datasets = {k: (seqs[k], meta[k]) for k in common_files}
    
    return datasets
    # for v in datasets.values():
    #     print(v)
    

# verify_dataset("/data/analysis/flu_production/gisaid_uplds/test/")


#%%

# def gisaid_upload(user, psswd, clientid, dateformat, log_path, datasets):

def gisaid_upload(datasets:dict[str,tuple[str, str]]) -> str:
    """
    Upload datasets to GISAID with EpiFlu CLI executable.

    input: dictionary of {name: (seqs, meta)}

    output: GISAID log

    """
    
    executable = os.path.join(os.getcwd(),'bin', 'fluCLI')

    if not os.path.isfile(executable):
        print(f'Error: GISAID executable not found in {executable}.\nCheck path & permissions.')

    # for k, v in datasets.items():
    #     print(f'Uploading {k} dataset to GISAID...')

    # cmmnd = [executable, 'upload', 
    #          '--username', user,
    #          '--password', psswd,
    #          '--clientid', clientid,
    #          '--log', log_path,
    #          '--metadata', meta,
    #          '--dateformat', dateformat]
     #'--fasta', seqs,

    # subprocess.run(cmmnd, check = True)

    

# gisaid_upload()


#%%









def main(args):
    verified_datasets = verify_dataset(args.input)
    gisaid_upload(verified_datasets)


#tells this script is to be run, not just imported as part of another script
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Upload flu seqs to GISAID and accession into local SQLite database.")
    parser.add_argument('-i','--input', type=str, required=True, help='Path to folder containing "metadata" dir and "sequences" dir to upload.')
    # parser.add_argument('-o','--output', type=str, required=True, help='Path to folder uploaded dataset should be moved to.')
    # parser.add_argument('-a','--interactive', type= bool = False, help='Run upload process interactively.')
    # parser.add_argument('-u', '--username', type=str, help='GISAID EpiFlu username.')
    # parser.add_argument('-p', '--password', type=str, help='GISAID EpiFlu password.')
    # parser.add_argument('-c', '--clientid', type=str, help='GISAID EpiFlu clientID.')
    # parser.add_argument('-d', '--dateformat', type = str, default='YYYYMMDD', 
    #                     help = 'The format of dates in GISAID EpiFlu metadata.\nOne of YYYYMMDD,YYYYDDMM,DDMMYYYY,MMDDYYYY.')
    # parser.add_argument('-l', '--log', type = str, help = 'Path to file to write log to.')

    args = parser.parse_args()
    # args = None
    main(args)
