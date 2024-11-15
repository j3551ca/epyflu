import argparse
import os
import sys
from getpass import getpass
from .gisaid_upload import verify_dataset, gisaid_upload
from .sqlite_db import (
    parse_gisaid_jsons,
    add_to_sqlite_db,
    collect_unreleased,
    gisaid_search,
    update_release_status,
)
from .gisaid_download import gisaid_download


def collect_common_vars(args):
    user = os.getenv("EPYFLU_USER") or args.username
    psswd = os.getenv("EPYFLU_PASSWORD") or args.password
    var_source = "cli"
    if not user or not psswd:
        var_source = "prompted"
    if not user:
        user = getpass("Please enter GISAID EpiFlu username: ")
        if not user:  # may have spaces in password? do not .strip()
            print("Error: GISAID EpiFlu username missing.")
            sys.exit(1)
    if not psswd:
        psswd = getpass("Please enter GISAID EpiFlu password: ")
        if not psswd:
            print("Error: GISAID EpiFlu password missing.")
            sys.exit(1)

    return user, psswd, var_source


def update_vars(args):
    db_path = args.database
    if not args.database:
        db_path = input("Specify path to existing or new SQLite database (*.db): ").strip()
        if not db_path:
            print("Error: No database specified.")
            sys.exit(1)

    return db_path


def download_vars(args, var_source):
    seg_list = args.segments or "HA,NA"
    download_type = args.download_type or "metadata"
    gids = args.gisaid_ids
    out_file = args.output
    if not args.output:
        out_file = input("Please enter path to file to write download to (*.xls for meta; *.fa for seqs): ")
        if not out_file:
            print("Error: No output file specified.")
            sys.exit(1)
    if not args.segments and var_source == "prompted":  # assume interactive mode
        seglist = input(
            "Please enter list of segments separated by commas to download data for or press Enter for <default>. "
            "<HA,NA>,PB1,PB2,PA,NP,MP,NS: "
        )
        if seglist:
            seg_list = seglist
    seg_list = seg_list.split(",")
    seg_list = [item.strip() for item in seg_list]
    if not args.download_type and var_source == "prompted":
        dtype = input(
            "Please enter type of data to download or press Enter for <default>. <'metadata'>,'dna','protein': "
        )
        if dtype:
            download_type = dtype
    if not args.gisaid_ids:
        gids = input(
            "Please enter list of GISAID IDs separated by commas to download data for. ex. "
            "EPI_ISL_1,EPI_ISL_2,EPI_ISL_45: "
        )
    gids = gids.split(",")
    gids = [item.strip() for item in gids]

    return seg_list, download_type, out_file, gids


def upload_vars(args, var_source):
    cid = os.getenv("EPYFLU_CLIENTID") or args.clientid
    input_dir = args.input
    log_dir = args.log
    dateform = args.dateformat or "YYYYMMDD"
    db_path = args.database

    if not input_dir:
        input_dir = input("Please enter path to folder containing dataset(s) to upload: ").strip()
        if not input_dir:
            print("Error: No dataset specified.")
            sys.exit(1)
    if not os.path.isdir(input_dir):
        print(f"Error: The folder {input_dir} does not exist. Check that spelling and path are accurate.")
        sys.exit(1)
    if not cid:
        cid = getpass("Please enter GISAID EpiFlu client ID: ")
        if not cid:
            print("Error: GISAID EpiFlu client ID missing.")
            sys.exit(1)
    if not log_dir:
        log_dir = input("Please enter path of directory to write GISAID logs to: ").strip()
        if not log_dir:
            print("Error: log path not specified.")
            sys.exit(1)
    if not os.path.isdir(log_dir):
        print(f"Error: The folder {log_dir} does not exist. Check that spelling and path are accurate.")
        sys.exit(1)
        # only for interactive user - assume cli user specified or is ok with default:
    if not args.dateformat and not args.input and var_source == "prompted":
        dateformat = input(
            "Please enter format of dates or press Enter for <default>. <YYYYMMDD>,YYYYDDMM,DDMMYYYY,MMDDYYYY: "
        )
        if dateformat:
            dateform = dateformat
    if not args.database:
        db_path = input("Specify path to existing or new SQLite database (*.db): ").strip()
        if not db_path:
            print("Error: No database specified.")
            sys.exit(1)

    return cid, input_dir, log_dir, dateform, db_path


def add_common_args(subcommand):
    """
    Add args that are common among subcommands so they are available to each
    respective parser.
    """
    subcommand.add_argument("-u", "--username", type=str, help="GISAID EpiFlu username.")
    subcommand.add_argument("-p", "--password", type=str, help="GISAID EpiFlu password.")


def main():
    
    parser = argparse.ArgumentParser(description="Upload flu seqs to GISAID and accession into local SQLite database.")
    # subcommand parsers
    subparsers = parser.add_subparsers(dest="command", help="epyflu subcommands.")
    upload_parser = subparsers.add_parser("upload", help="Upload datasets to GISAID EpiFlu.")
    update_parser = subparsers.add_parser(
        "update",
        help="Update local SQLite db with isolate availability on GISAID EpiFlu.",
    )
    download_parser = subparsers.add_parser(
        "download",
        help="Download metadata or DNA/protein sequences from GISAID EpiFlu.",
    )

    # subcommand arguments - upload
    upload_parser.add_argument(
        "-i",
        "--input",
        type=str,
        help='Path to folder containing "metadata" and "sequences" to upload.',
    )
    add_common_args(upload_parser)
    upload_parser.add_argument("-c", "--clientid", type=str, help="GISAID EpiFlu clientID.")
    upload_parser.add_argument(
        "-d",
        "--dateformat",
        type=str,
        choices=["YYYYMMDD", "YYYYDDMM", "DDMMYYYY", "MMDDYYYY"],
        help="The format of dates in GISAID EpiFlu metadata <YYYYMMDD>.",
    )
    upload_parser.add_argument("-l", "--log", type=str, help="Path to dir to write log to.")
    upload_parser.add_argument(
        "-b",
        "--database",
        type=str,
        help="Path to file to write sqlite database to (*.db).",
    )

    # refresh availability of isolates on GISAID in local db
    update_parser.add_argument(
        "-b",
        "--database",
        type=str,
        help="Path to file to write sqlite database to (*.db).",
    )
    add_common_args(update_parser)

    # args for download module
    download_parser.add_argument(
        "-o",
        "--output",
        type=str,
        help="Path to file to write download to (*.xls for meta; *.fa for seqs).",
    )
    add_common_args(download_parser)
    download_parser.add_argument(
        "-s",
        "--segments",
        type=str,
        help="List of segments to download metadata or sequences for <HA,NA>.",
    )
    download_parser.add_argument(
        "-t",
        "--download_type",
        type=str,
        choices=["dna", "metadata", "protein"],
        help="Type of data to download <metadata>.",
    )
    download_parser.add_argument(
        "-g",
        "--gisaid_ids",
        type=str,
        help="List of GISAID IDs to download data for (EPI_ISL_1,EPI_ISL_2,EPI_ISL_45).",
    )

    args = parser.parse_args()

    if args.command is None or args.command not in [ "upload", "update", "download"]:
        print("Error: No valid subcommand provided. Please specify a subcommand (upload, update, download).")
        parser.print_help()
    else:
        usr, psswd, var_source = collect_common_vars(args)

        if args.command == "upload":
            cid, input_dir, log_dir, dateform, db_path = upload_vars(args, var_source)
            verified_datasets = verify_dataset(input_dir)
            gisaid_jsons = gisaid_upload(verified_datasets, usr, psswd, cid, dateform, log_dir)
            isl_meta, segs_df = parse_gisaid_jsons(gisaid_jsons)
            add_to_sqlite_db(isl_meta, "isolate_meta", db_path)
            add_to_sqlite_db(segs_df, "segment_seqs", db_path)

        elif args.command == "update":

            db_path = update_vars(args)
            if not os.path.isfile(db_path):
                print("This database does not exist. Run epyflu upload first or check spelling matches existing db.")
                sys.exit(1)
            # gisaid_ids of isolates - showing as unreleased in sqlite db & part of isolate_id group that has
            # no released gisaid_ids - to be searched in gisaid
            not_released = collect_unreleased(db_path)
            gisaid_df = gisaid_search(usr, psswd, not_released)
            update_release_status(gisaid_df, db_path)

        elif args.command == "download":
            seg_list, download_type, out_file, gids = download_vars(args, var_source)
            gisaid_download(usr, psswd, gids, out_file, download_type, seg_list)


if __name__ == "__main__":

    main()
