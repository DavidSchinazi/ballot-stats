import json
from datetime import datetime, timezone

from .files import Files
from .types import Iesg


def save_json(obj, file_path):
    with open(file_path, "w") as f:
        json.dump(obj, f, indent=2, sort_keys=True, default=str)


def load_json(file_path):
    with open(file_path, "r") as f:
        return json.load(f)


def date_from_json(s):
    if s is None:
        return None
    return datetime.strptime(s, "%Y-%m-%d").replace(tzinfo=timezone.utc)


def load_iesgs():
    iesgs_from_json = load_json(Files.iesgs_file())
    iesgs = []
    for iesg in iesgs_from_json:
        iesgs.append(
            Iesg(
                date_start=date_from_json(iesg["date_start"]),
                date_end=date_from_json(iesg["date_end"]),
                members=iesg["members"],
            )
        )
    return iesgs


def save_iesgs(iesgs):
    iesgs_to_json = []
    for iesg in iesgs:
        iesgs_to_json.append(
            {
                "date_start": iesg.date_start,
                "date_end": iesg.date_end,
                "members": iesg.members,
            }
        )
    save_json(iesgs_to_json, Files.iesgs_file())


def load_ad_term_ends():
    ad_ends = load_json(Files.ad_term_ends_file())
    for ad in ad_ends:
        ad_ends[ad] = [date_from_json(e) for e in ad_ends[ad]]
    return ad_ends
