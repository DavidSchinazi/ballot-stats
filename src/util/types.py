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