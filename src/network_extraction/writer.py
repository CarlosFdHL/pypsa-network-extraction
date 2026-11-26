"""Write the DataFrames returned by an extractor to disk."""

from pathlib import Path


def write_files(files, folder, timeseries_format="parquet"):
    """Write {file_name: DataFrame}; returns the names of the files written.

    *.parquet files are written as csv when timeseries_format is "csv".
    """
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    written = []
    for name, df in files.items():
        path = folder / name
        if path.suffix == ".parquet" and timeseries_format == "csv":
            path = path.with_suffix(".csv")
        if path.suffix == ".parquet":
            df.to_parquet(path)
        elif path.suffix == ".csv":
            df.to_csv(path)
        else:
            raise ValueError(f"Unsupported file type: {name}")
        written.append(path.name)
    return written
