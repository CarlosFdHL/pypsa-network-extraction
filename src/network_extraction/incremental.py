"""Decide whether a dataset has to be (re)extracted."""

from pathlib import Path


def is_up_to_date(record, folder, source_mtime):
    """True if the dataset was extracted from this version of the network and its files exist."""
    if not record:
        return False
    if record.get("source_mtime") != source_mtime:
        return False
    return all((Path(folder) / f).exists() for f in record.get("files", []))


def needs_extraction(record, folder, source_mtime, force):
    return force or not is_up_to_date(record, folder, source_mtime)
