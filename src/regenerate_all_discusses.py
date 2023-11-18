#!/usr/bin/env python3

import os

from util.files import Files
from util.json_handler import load_doc_ballots, save_discuss_ballots

if __name__ == "__main__":
    discuss_ballots = []
    for f in os.listdir(Files.rfc_dir()):
        db = load_doc_ballots(Files.rfc_dir(f))
        for ad in db.all_ballots:
            for ballot in db.all_ballots[ad]:
                if ballot.ballot_type == "Discuss":
                    print(ballot.text)
                    discuss_ballots.append(ballot)
    save_discuss_ballots(discuss_ballots)
