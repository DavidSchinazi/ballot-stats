from datetime import datetime, timezone


def date_from_str(s):
    if s is None:
        return None
    return datetime.strptime(s, "%Y-%m-%d").replace(tzinfo=timezone.utc)


class Ballot:
    ad = None
    ballot_type = None
    start_time = None
    end_time = None
    text = None
    end_reason = None

    def __init__(self, ad, ballot_type, start_time):
        self.ad = ad
        self.ballot_type = ballot_type
        self.start_time = start_time

    def __str__(self):
        return "{t} {s} {e} {txt}".format(
            t=self.ballot_type,
            s=self.start_time,
            e=self.end_time,
            txt=self.text if False else "",
        )

    def as_dict(self):
        return {
            "ad": self.ad,
            "type": self.ballot_type,
            "start": self.start_time,
            "end": self.end_time,
            "end_reason": self.end_reason,
            "text": self.text,
        }

    @classmethod
    def from_dict(cls, d):
        b = cls(
            ad=d["ad"],
            ballot_type=d["type"],
            start_time=d["start"],
        )
        b.end_time = d["end"]
        b.end_reason = d["end_reason"]
        b.text = d["text"]
        return b


class Iesg:
    date_start = None
    date_end = None
    members = None

    def __init__(self, date_start, date_end, members):
        self.date_start = date_start
        self.date_end = date_end
        self.members = members

    def as_dict(self):
        return {
            "date_start": self.date_start,
            "date_end": self.date_end,
            "members": self.members,
        }

    @classmethod
    def from_dict(cls, d):
        b = cls(
            date_start=date_from_str(d["date_start"]),
            date_end=date_from_str(d["date_end"]),
            members=d["members"],
        )
        return b


class DocBallot:
    doc_name = None
    start_time = None
    end_time = None
    all_ballots = None  # dict ad_name => Ballot

    def __init__(self, doc_name, start_time, end_time):
        self.doc_name = doc_name
        self.start_time = start_time
        self.end_time = end_time

    def as_dict(self):
        all_ballots = {}
        for ad in self.all_ballots:
            all_ballots[ad] = [b.as_dict() for b in self.all_ballots[ad]]
        return {
            "doc_name": self.doc_name,
            "evaluation_start": self.start_time,
            "evaluation_end": self.end_time,
            "all_ballots": all_ballots,
        }

    @classmethod
    def from_dict(cls, d):
        db = cls(
            doc_name=d["doc_name"],
            start_time=d["evaluation_start"],
            end_time=d["evaluation_end"],
        )
        all_ballots = d["all_ballots"]
        db.all_ballots = {}
        for ad in all_ballots:
            db.all_ballots[ad] = [Ballot.from_dict(b) for b in all_ballots[ad]]
        return db


class DownloadedHistoryMetadata:
    download_time = None

    def __init__(self, download_time):
        self.download_time = download_time

    def as_dict(self):
        return {
            "download_time": self.download_time.isoformat(),
        }

    @classmethod
    def from_dict(cls, d):
        b = cls(
            download_time=datetime.fromisoformat(d["download_time"]),
        )
        return b