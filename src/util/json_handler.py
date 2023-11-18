import json

from .files import Files
from .types import Ballot, DocBallot, Iesg, date_from_str


def save_json(obj, file_path):
    with open(file_path, "w") as f:
        json.dump(obj, f, indent=2, sort_keys=True, default=str)


def load_json(file_path):
    with open(file_path, "r") as f:
        return json.load(f)


def load_iesgs():
    return [Iesg.from_dict(iesg) for iesg in load_json(Files.iesgs_file())]


def save_iesgs(iesgs):
    save_json([iesg.as_dict() for iesg in iesgs], Files.iesgs_file())


def load_ad_term_ends():
    ad_ends = load_json(Files.ad_term_ends_file())
    for ad in ad_ends:
        ad_ends[ad] = [date_from_str(e) for e in ad_ends[ad]]
    return ad_ends


def save_ad_term_ends(ad_ends):
    save_json(ad_ends, Files.ad_term_ends_file())


def save_doc_ballots(doc_ballots, file_path):
    save_json(doc_ballots.as_dict(), file_path)


def load_doc_ballots(file_path):
    return DocBallot.from_dict(load_json(file_path))


def save_ballot_list(ballot_list, file_path):
    save_json([b.as_dict() for b in ballot_list], file_path)


def save_discuss_ballots(discuss_ballots):
    save_ballot_list(discuss_ballots, Files.discusses_file())
