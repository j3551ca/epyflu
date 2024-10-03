import json
import pandas as pd
import sqlite3
import gisflu


def parse_gisaid_jsons(gisaid_json_dict: dict[str, tuple[str, str]]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Convert json log file(s) produced by upload to GISAID & associated metadata
    files into df for input into SQLite database.

    input: dict{dataset: (/path/to/log/json, /path/to/metadata/used/in/upload)}.
    output: (isolate_meta_df, segments_df).
    """
    observations = []
    meta_list = []
    df = []
    meta = []

    for k, v in gisaid_json_dict.items():
        print(f"Parsing dataset: {k}...")
        if v != None:
            with open(v[0], "r") as in_json:
                for line in in_json:
                    observation = json.loads(line.strip())
                    observation["dataset_id"] = k
                    observations.append(observation)
            meta_df = pd.read_csv(v[1], sep=",", header=0)
        meta_list.append(meta_df)

    df = pd.DataFrame(observations)
    meta = pd.concat(meta_list)

    df[["sample_id", "gisaid_id"]] = df["msg"].str.split("; ", expand=True)
    df[["submission_date", "submission_time"]] = df["timestamp"].str.split(" ", expand=True)
    df.drop(["timestamp", "msg"], axis=1, inplace=True)

    epi_ids_df = df.loc[df["code"].isin(["epi_id", "epi_isl_id"])].copy()

    epi_ids_df["sample_id"] = epi_ids_df["sample_id"].str.split(" ", expand=True)[0]

    epi_isl_df = epi_ids_df[epi_ids_df["code"] == "epi_isl_id"]
    epi_segs_df = epi_ids_df[epi_ids_df["code"] == "epi_id"]

    meta.columns = meta.columns.str.lower()
    meta.columns = [col.replace("(", "").replace(")", "").replace(" ", "_") for col in meta.columns]
    seg_cols = meta.filter(regex=r"^seq_id").columns.tolist()

    meta_minimal = meta[["isolate_name", "collection_date", "subtype", "location", "host"]]
    meta_melted = pd.melt(
        meta,
        id_vars="isolate_name",
        value_vars=seg_cols,
        var_name="segment",
        value_name="segment_seq_id",
    )

    # only what has been uploaded is deposited into db
    epi_isl_meta = pd.merge(
        epi_isl_df,
        meta_minimal,
        how="left",
        left_on="sample_id",
        right_on="isolate_name",
    ).drop(columns=["isolate_name"])

    epi_isl_meta.rename(columns={"sample_id": "isolate_id"}, inplace=True)
    # default is not release by gisaid - will be updated in `gisaid_search` function
    epi_isl_meta["released"] = "No"

    epi_segs_meta = pd.merge(
        epi_segs_df,
        meta_melted,
        how="left",
        left_on="sample_id",
        right_on="segment_seq_id",
    ).drop(columns=["segment_seq_id"])
    #  validate = "one_to_one")

    epi_segs_meta.rename(columns={"sample_id": "seg_id", "isolate_name": "isolate_id"}, inplace=True)

    epi_isl_meta = epi_isl_meta.drop_duplicates(subset=["isolate_id", "gisaid_id"])
    epi_segs_meta = epi_segs_meta.drop_duplicates(subset=["isolate_id", "gisaid_id"])

    return epi_isl_meta, epi_segs_meta


def add_to_sqlite_db(parsed_df: pd.DataFrame, table_name: str, db_path: str) -> None:
    """
    Add isolates and corresponding segments with associated GISAID IDs
    to user-specified SQLite database file. Creates a backup file,
    enforces schema, then adds data.

    input: pandas dataframe.
    output: None. Table is created in database file.
    """
    print(parsed_df.head())
    cnxn = sqlite3.connect(db_path)

    db_backup = db_path.replace(".db", "_backup.db")
    with open(db_path, "rb") as source_file:
        with open(db_backup, "wb") as destination_file:
            destination_file.write(source_file.read())

    cnxn.execute("PRAGMA foreign_keys = ON")
    # store date time as text since sqlite not support DATE/ TIME types. Also primary key is not null by default
    cnxn.execute(
        """
    CREATE TABLE IF NOT EXISTS isolate_meta (
        isolate_id TEXT NOT NULL,
        code TEXT,
        dataset_id TEXT,
        gisaid_id TEXT,
        submission_date TEXT,
        submission_time TEXT, 
        collection_date TEXT,
        subtype TEXT,
        location TEXT,
        host TEXT,
        released TEXT,
        PRIMARY KEY (isolate_id, submission_time),
        UNIQUE (isolate_id, gisaid_id)
    );
    """
    )

    cnxn.execute(
        """
    CREATE TABLE IF NOT EXISTS segment_seqs (
        seg_id TEXT PRIMARY KEY NOT NULL,
        isolate_id TEXT NOT NULL,
        code TEXT,
        dataset_id TEXT,
        gisaid_id TEXT,
        submission_date TEXT,
        submission_time TEXT, 
        segment TEXT,
        FOREIGN KEY (isolate_id, submission_time) REFERENCES isolate_meta (isolate_id, submission_time)
    );
    """
    )

    cnxn.commit()

    parsed_df.to_sql(table_name, cnxn, if_exists="append", index=False)
    cnxn.commit()

    foreign_key_check = cnxn.execute("PRAGMA foreign_key_check").fetchall()
    if foreign_key_check:
        print("Foreign key violations found:", foreign_key_check)

    cnxn.close()


def collect_unreleased(db_path: str) -> str:
    """
    Collect a list of GISAID IDs that are the most-recently submitted &
    not yet released to be searched for in GISAID EpiFlu.

    input: absolute path to user-specified SQLite database file.
    output: str of search pattern (GISAID IDs).
    """

    cnxn = sqlite3.connect(db_path)
    # may be multiple gisaid_ids per isolate_id, but should not be the case vice versa - therefore search using
    # gisaid_ids to get current, accurate pair published on GISAID
    cursor = cnxn.cursor()

    cursor.execute(
        """
                   WITH isolate_recent AS (
                   SELECT gisaid_id, MAX(submission_date || ' ' || submission_time) AS latest_submission
                   FROM isolate_meta
                   GROUP BY isolate_id
                   )
                   SELECT gisaid_id
                   FROM isolate_meta
                   WHERE (submission_date || ' ' || submission_time) = (
                   SELECT latest_submission
                   FROM isolate_recent
                   WHERE isolate_meta.gisaid_id = isolate_recent.gisaid_id
                   )
                   AND released = 'No';
                   """
    )

    results = cursor.fetchall()

    results_flat = [id[0] for id in results]
    not_released_str = " ".join(results_flat)

    return not_released_str


def gisaid_search(user: str, password: str, isl_ids: str) -> pd.DataFrame:
    """
    Log into GISAID and search EpiFlu for unreleased GISAID IDs.

    input: GISAID credentials & str of search pattern (GISAID IDs).
    output: pandas dataframe of publicly available GISAID IDs.
    """

    cred = gisflu.login(user, password)

    gisaid_df = gisflu.search(cred, searchPattern=isl_ids, submitDateFrom="2017-01-01", recordLimit=700000)

    gisaid_df.columns = gisaid_df.columns.str.lower()
    gisaid_df.columns = [col.replace(" ", "_") for col in gisaid_df.columns]

    return gisaid_df


def update_release_status(gisaid_query_results: pd.DataFrame, db_path: str) -> None:
    """
    Update local SQLite database release status with results of EpiFlu
    database search.

    input: pandas dataframe of publicly available GISAID IDs.
    output: None. SQLite database with updated release status.
    """

    with sqlite3.connect(db_path) as cnxn:

        gisaid_query_results.to_sql("released_ids", cnxn, if_exists="replace", index=False)

        cnxn.execute(
            """
        UPDATE isolate_meta
        SET released = 'Yes'
        WHERE (isolate_id, gisaid_id) IN (SELECT name, isolate_id FROM released_ids)
        """
        )
        cnxn.commit()

        cursor = cnxn.cursor()
        cursor.execute("SELECT gisaid_id, released, submission_date FROM isolate_meta WHERE released LIKE '%Yes%'")
        results = cursor.fetchall()
        print(results[-5:])

        # remove temp query result table
        cursor.execute("DROP TABLE released_ids")


# %%


def query_sqlite_db(db_path: str, query: str) -> pd.DataFrame:
    """
    Execute SQL query on database and return results as pandas dataframe.

    input: absolute path to local SQLite database file, str of SQL query.
    output: pandas dataframe of results from SQL query.
    """

    cnxn = sqlite3.connect(db_path)
    try:
        results_df = pd.read_sql_query(query, cnxn)
        print(results_df.tail(4))
    finally:
        cnxn.close()

    return results_df
