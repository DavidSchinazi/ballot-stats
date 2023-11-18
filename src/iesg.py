#!/usr/bin/env python3

import calendar
import json
import os
from datetime import date

from bs4 import BeautifulSoup

from util.files import Files

# Using offline download pulled from this link:
# https://www.ietf.org/how/meetings/past/
with open(Files.metadata_dir("IETF_Past_Meetings.html")) as fp:
    pastIetfsSoup = BeautifulSoup(fp, "lxml")

# Using offline download pulled from this link:
# https://www.ietf.org/about/groups/iesg/past-members/
with open(Files.metadata_dir("IESG_Past_Members.html")) as fp:
    pastIesgSoup = BeautifulSoup(fp, "lxml")

ietf_start_dates = {}
ietf_end_dates = {}

for bp in pastIetfsSoup.body.main.find_all("div", class_="block-paragraph"):
    if len(bp.text) < 1000:
        continue
    past_ietf_elements = bp.contents
    break

months = {name: num for num, name in enumerate(calendar.month_name) if num}

i = 0
num_past_ietf_elements = len(past_ietf_elements)
while i + 1 < num_past_ietf_elements:
    title_element = past_ietf_elements[i]
    if title_element.name == "p":
        i += 1
        continue
    assert title_element.name == "h2"
    paragraph_element = past_ietf_elements[i + 1]
    assert paragraph_element.name == "p"
    title_text = title_element.text
    if title_text.startswith("IETF "):
        ietf_num = int(title_text[5:])
    else:
        assert title_text.endswith(" IETF")
        ietf_num = int(title_text[:-7])
    assert ietf_num > 0
    date_line = paragraph_element.strings.__next__()
    if date_line[0].isdigit():
        dls = date_line.split(" ")
        year = dls[2][:4]
        start_month = dls[1]
        end_month = start_month
        ds = dls[0].split("-")
        start_day = ds[0]
        end_day = ds[1]
    else:
        dls = date_line.split(", ")
        year = dls[1][:4]
        ds = dls[0].split("-")
        ss = ds[0].strip().split(" ")
        start_month = ss[0]
        start_day = ss[1]
        end = ds[1].strip()
        if end.isdigit():
            end_month = start_month
            end_day = end
        else:
            es = end.split(" ")
            end_month = es[0]
            end_day = es[1]
    ietf_start_dates[ietf_num] = date(int(year), months[start_month], int(start_day))
    ietf_end_dates[ietf_num] = date(int(year), months[end_month], int(end_day))
    # print('IETF {n}: {s} - {e}'.format(n=ietf_num, s=ietf_start_dates[ietf_num], e=ietf_end_dates[ietf_num]))
    i += 2


def is_block(css_class):
    return css_class == "block-heading" or css_class == "block-paragraph"


def get_ietf_date(ietf, dates, minusOne=False):
    s = ietf.split(" (")[0]
    assert s.startswith("IETF ")
    ietf_num = int(s[5:])
    if minusOne:
        ietf_num -= 1
    return dates[ietf_num]


iesg_blocks = pastIesgSoup.body.main.find_all("div", class_=is_block)

i = 0
num_iesg_blocks = len(iesg_blocks)
while i < num_iesg_blocks:
    i += 1
    if iesg_blocks[i - 1].text == "Past IESG Members":
        break

ad_ietfs = {}
iesgs = []

CURRENT_IETF = 117
CURRENT_IESG = [
    "Andrew Alston",
    "Roman Danyliw",
    "Martin Duke",
    "Lars Eggert",
    "Erik Kline",
    "Murray Kucherawy",
    "Warren Kumari",
    "Francesca Palombini",
    "Zaheduzzaman Sarker",
    "John Scudder",
    "Éric Vyncke",
    "Robert Wilton",
    "Paul Wouters",
    "Jim Guichard",
]

iesgs.append(
    {
        "date_start": ietf_start_dates[CURRENT_IETF - 1],
        "date_end": None,
        "members": CURRENT_IESG,
    }
)

while i + 1 < num_iesg_blocks:
    timeframe_block = iesg_blocks[i]
    assert "block-heading" in timeframe_block["class"]
    members_block = iesg_blocks[i + 1]
    assert "block-paragraph" in members_block["class"]
    ietfs = set()
    for ietf_str in timeframe_block.text.split(", "):
        ietf_str = ietf_str[: ietf_str.find(" (")]
        assert ietf_str.startswith("IETF ")
        ietfs.add(int(ietf_str[5:]))
    print(timeframe_block.text)
    start_date = ietf_start_dates[min(ietfs) - 1]
    end_date = ietf_end_dates[max(ietfs)]
    print("timeframe {s} to {e}".format(s=start_date, e=end_date))
    names = []
    for member_item in members_block.find_all("li"):
        member_details = member_item.text.split(", ")
        assert len(member_details) == 2
        name = member_details[0]
        name = name.replace("\u00A0", "")
        names.append(name)
        ad_set = ad_ietfs.get(name, set())
        ad_set |= ietfs
        ad_ietfs[name] = ad_set
        area = member_details[1]
        print('  {a}: "{n}"'.format(a=area, n=name))
    print(names)
    iesgs.append(
        {
            "date_start": start_date,
            "date_end": end_date,
            "members": names,
        }
    )
    i += 2

for name in CURRENT_IESG:
    ad_set = ad_ietfs.get(name, set())
    ad_set.add(CURRENT_IETF)
    ad_ietfs[name] = ad_set

ad_ends = {}
for ad in ad_ietfs:
    ietfs = ad_ietfs[ad]
    ad_ends[ad] = [
        ietf_end_dates[i] for i in ietfs if i + 1 not in ietfs and i != CURRENT_IETF
    ]

# for ad in ad_ends:
#   print('{ad}: {s}'.format(ad=ad, s=ad_ends[ad]))

# print(json.dumps(ad_ends, indent=2, sort_keys=True, default=str))

with open(Files.ad_term_ends_file(), "w") as f:
    json.dump(ad_ends, f, indent=2, sort_keys=True, default=str)

with open(Files.iesgs_file(), "w") as f:
    json.dump(iesgs, f, indent=2, sort_keys=True, default=str)
