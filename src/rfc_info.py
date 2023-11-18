#!/usr/bin/env python3

import json
import os
from datetime import datetime, timezone
from sys import argv, exit

import requests
from bs4 import BeautifulSoup

from util.files import Files

rfc_num = 9293

if len(argv) > 1:
    rfc_num = int(argv[1])

resp = requests.get("http://localhost:8000/doc/rfc{r}/history/".format(r=rfc_num))
if resp.status_code == 404:
    print("RFC {r} does not exist".format(r=rfc_num))
    exit(0)

assert resp.ok
soup = BeautifulSoup(resp.text, "lxml")

if (
    len(
        soup.find_all(
            lambda tag: tag.name == "a" and "IESG evaluation record" in tag.text
        )
    )
    == 0
):
    print("RFC {r} was not evaluated by the IESG".format(r=rfc_num))
    exit(0)


with open(Files.ad_term_ends_file(), "r") as f:
    ad_ends = json.load(f)

with open(Files.iesgs_file(), "r") as f:
    iesgs_from_json = json.load(f)


def date_from_json(s):
    if s is None:
        return None
    return datetime.strptime(s, "%Y-%m-%d").replace(tzinfo=timezone.utc)


iesgs = []
for iesg in iesgs_from_json:
    iesgs.append(
        {
            "date_start": date_from_json(iesg["date_start"]),
            "date_end": date_from_json(iesg["date_end"]),
            "members": iesg["members"],
        }
    )

for ad in ad_ends:
    ad_ends[ad] = [date_from_json(e) for e in ad_ends[ad]]
    # print('{ad}: {s}'.format(ad=ad, s=ad_ends[ad]))

# print(soup.prettify())


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


ballots = {}
ballot_start_time = None
ballot_end_time = None

rows = soup.body.table.tbody.findAll("tr")
for row in reversed(rows):
    cells = row.findAll("td")
    timestamp = datetime.strptime(cells[0].div["title"], "%Y-%m-%d %H:%M:%S %z")
    revision = cells[1].text
    author = cells[2].text
    full_action_divs = cells[3].find_all(attrs={"class": "full"})
    if len(full_action_divs) > 0:
        action = " ".join(full_action_divs[0].strings)
    else:
        action = cells[3].text
    if action == 'Created "Approve" ballot':
        ballot_start_time = timestamp
        for iesg in iesgs:
            if iesg["date_start"] > timestamp:
                continue
            if iesg["date_end"] is not None and iesg["date_end"] < timestamp:
                continue
            for ad in iesg["members"]:
                ballots_for_ad = ballots.get(ad, [])
                ballots_for_ad.append(Ballot(ad, "No Record", timestamp))
                ballots[ad] = ballots_for_ad
        # print('{t} - {a}'.format(t=timestamp, a=action))
    elif action == 'Closed "Approve" ballot':
        ballot_end_time = timestamp
        for a in ballots:
            ballots[a][-1].end_time = timestamp
            ballots[a][-1].end_reason = "evaluation_closed"
    elif action.startswith("["):
        action_type = action[1 : action.find("]")]
        if action_type == "Ballot Position Update":
            action_details = action[action.find("]") + 2 :]
            # print('{t} - {d}'.format(t=timestamp, d=action_details))
            if action_details.startswith("New position, "):
                ballot_type = action_details.split(", ")[1]
                ballots_for_author = ballots.get(author, [])
                if len(ballots_for_author) > 0:
                    ballots_for_author[-1].end_time = timestamp
                    ballots_for_author[-1].end_reason = "new_position"
                ballots_for_author.append(Ballot(author, ballot_type, timestamp))
                ballots[author] = ballots_for_author
            else:
                change_split = action_details.split(" has been changed to ")
                if len(change_split) > 1:
                    ballot_type = change_split[1].split(" from ")[0]
                    ballots_for_author = ballots.get(author, [])
                    if len(ballots_for_author) > 0:
                        ballots_for_author[-1].end_time = timestamp
                        ballots_for_author[-1].end_reason = "position_updated"
                    ballots_for_author.append(Ballot(author, ballot_type, timestamp))
                    ballots[author] = ballots_for_author
        elif action_type == "Ballot discuss":
            action_details = action[action.find("]") + 2 :]
            ballots_for_author = ballots.get(author, [])
            if len(ballots_for_author) > 0:
                if ballots[author][-1].text is None:
                    ballots[author][-1].text = action_details
                else:
                    ballots_for_author[-1].end_time = timestamp
                    ballots_for_author[-1].end_reason = "discuss_updated"
                    new_ballot = Ballot(
                        author, ballots[author][-1].ballot_type, timestamp
                    )
                    new_ballot.text = action_details
                    ballots_for_author.append(new_ballot)
            ballots[author] = ballots_for_author
        elif action_type == "Ballot comment":
            action_details = action[action.find("]") + 2 :]
            ballots_for_author = ballots.get(author, [])
            if (
                len(ballots_for_author) > 0
                and ballots[author][-1].ballot_type == "Abstain"
            ):
                if ballots[author][-1].text is None:
                    ballots[author][-1].text = action_details
                else:
                    ballots_for_author[-1].end_time = timestamp
                    ballots_for_author[-1].end_reason = "comment_updated"
                    new_ballot = Ballot(
                        author, ballots[author][-1].ballot_type, timestamp
                    )
                    new_ballot.text = action_details
                    ballots_for_author.append(new_ballot)
            ballots[author] = ballots_for_author

# print('ballot_start_time={}'.format(ballot_start_time))

res = {}
res["rfc"] = rfc_num
res["evaluation_start"] = ballot_start_time
res["evaluation_end"] = ballot_end_time

res_ballots = {}

for a in ballots:
    # print(a)
    res_ballots_for_ad = []
    for b in ballots[a]:
        for ad_end in ad_ends[b.ad]:
            if b.start_time < ad_end and (b.end_time is None or ad_end < b.end_time):
                b.end_time = ad_end
                b.end_reason = "ad_term_ended"
        res_ballots_for_ad.append(
            {
                "type": b.ballot_type,
                "start": b.start_time,
                "end": b.end_time,
                "end_reason": b.end_reason,
                "text": b.text,
            }
        )
        # print('  {}'.format(b))
    res_ballots[a] = res_ballots_for_ad

res["all_ballots"] = res_ballots

with open(Files.rfc_dir("rfc{}.json".format(rfc_num)), "w") as f:
    json.dump(res, f, indent=2, sort_keys=True, default=str)

print("RFC {r} analyzed succesfully".format(r=rfc_num))
exit(0)
