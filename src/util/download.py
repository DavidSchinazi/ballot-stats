import requests
from datetime import datetime, timedelta, timezone

from .files import Files
from .json_handler import load_json, save_json
from .types import DownloadedHistoryMetadata


def download_doc_history(doc_name):
    resp = requests.get("http://localhost:8000/doc/{d}/history/".format(d=doc_name))
    if resp.status_code == 404:
        print("{d} does not exist".format(d=doc_name))
        return False
    assert resp.ok
    with open(Files.history_html(doc_name), "w") as f:
        f.write(resp.text)
    metadata = DownloadedHistoryMetadata(download_time=datetime.now(timezone.utc))
    save_json(metadata.as_dict(), Files.history_json(doc_name))
    return True


def should_download_doc_history(doc_name):
    try:
        metadata = DownloadedHistoryMetadata.from_dict(
            load_json(Files.history_json(doc_name))
        )
    except FileNotFoundError:
        return True
    return datetime.now(timezone.utc) - metadata.download_time >= timedelta(days=7)


def maybe_download_doc_history(doc_name, force_download=False):
    if force_download or should_download_doc_history(doc_name):
        download_doc_history(doc_name)


def get_doc_history_html(doc_name, force_download=False):
    maybe_download_doc_history(doc_name, force_download=force_download)
    try:
        with open(Files.history_html(doc_name), "r") as f:
            history_html = f.read()
    except FileNotFoundError:
        return ""
    return history_html
