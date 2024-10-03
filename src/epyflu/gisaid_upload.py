import os
import sys
from glob import glob
import subprocess


def verify_dataset(dataset_path: str) -> dict[str, tuple[str, str]]:
    """
    Check uniqueness and pairing of datasets to upload.

    input: path to directory containing datasets to upload.
    output: dict of verified datasets {name: /path/to/meta, /path/to/seqs}.
    """
    seqs_path = []
    for e in ("*.fasta", "*.fa"):
        seqs_path.extend(glob(os.path.join(dataset_path, "**", e), recursive=True))

    seqs = {}
    for file in seqs_path:
        k = os.path.basename(file).rsplit(".", 1)[0]
        if k in seqs.keys():
            print(f'Error: multiple sequence files with the name "{k}" in {dataset_path}*.\nRename with unique name.')
            sys.exit(1)
        seqs[k] = os.path.abspath(file)

    metadata_path = glob(os.path.join(dataset_path, "**", "*.csv"), recursive=True)

    meta = {}
    for file in metadata_path:
        k = os.path.basename(file).split(".csv")[0]
        if k in meta.keys():
            print(f"Error: multiple metadata files with the name {k} in {dataset_path}.\nRename with unique name.")
            sys.exit(1)
        meta[k] = os.path.abspath(file)

    # only identically named fasta and meta will be kept
    common_files = set(meta.keys()).intersection(seqs.keys())

    missing = []
    if len(set(seqs.keys()) - set(meta.keys())) > 0:
        seqs_missing_meta = set(seqs.keys()) - set(meta.keys())
        for k in seqs_missing_meta:
            missing.append(os.path.basename(seqs[k]))
        print(f"Note: The following sequence file(s) are missing metadata and will not be uploaded:\n{missing}")

    datasets = {k: (meta[k], seqs[k]) for k in common_files}

    return datasets


def gisaid_upload(
    datasets: dict[str, tuple[str, str]],
    user: str,
    psswd: str,
    clientid: str,
    dateformat: str,
    log_path: str,
) -> dict[str, tuple[str, str]]:
    """
    Upload datasets to GISAID with EpiFlu CLI executable.

    input: dictionary of {name: (meta, seqs)}.
    output: dict of GISAID logs {name: path/to/log/json}.
    """

    executable = os.path.join(os.getcwd(), "bin", "fluCLI")

    if not os.path.isfile(executable):
        print(f"Error: GISAID executable not found in {executable}.\nCheck path & permissions.")

    num_fails = 0
    dataset_logs = {}

    for k, pair in datasets.items():
        print(f"Uploading {k} dataset to GISAID...")

        gisaid_log = os.path.join(log_path, "dataset_" + k + "_gisaid.json")

        cmmnd = [
            executable,
            "upload",
            "--username",
            user,
            "--password",
            psswd,
            "--clientid",
            clientid,
            "--log",
            gisaid_log,
            "--metadata",
            pair[0],
            "--fasta",
            pair[1],
            "--dateformat",
            dateformat,
        ]

        output = subprocess.run(cmmnd, capture_output=True, text=True)

        # capture stderr but continue for case when multiple datasets to upload.
        # Also reason check = True removed in above command.
        if output.returncode != 0:
            num_fails += 1
            upload_error_file = os.path.join(log_path, "dataset_" + k + "_upload_error.log")
            with open(upload_error_file, "w") as f:
                for line in output.stderr:
                    f.write(line)
            print(f"Unsuccessful upload of {k} dataset. \nSee {upload_error_file} for details.")
            print(f"Exit status: {output.returncode}")
        else:
            print(f"Successful upload of {k} dataset to GISAID.")

        if os.path.exists(gisaid_log):
            dataset_logs[k] = (gisaid_log, pair[0])
        else:
            dataset_logs[k] = None

    num_pass = len(datasets.keys()) - num_fails
    print(f"{num_pass} of {len(datasets.keys())} datasets uploaded to GISAID successfully.")

    return dataset_logs
