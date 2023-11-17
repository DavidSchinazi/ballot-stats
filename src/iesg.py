#!/usr/bin/env python3

import calendar
import json
import os
from datetime import date

from bs4 import BeautifulSoup

metaDataDir = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "data/meta")
)
if not os.path.exists(metaDataDir):
    os.makedirs(metaDataDir)

# Using offline download pulled from this link:
# https://www.ietf.org/how/meetings/past/
pastIetfsFile = os.path.join(metaDataDir, "IETF_Past_Meetings.html")
with open(pastIetfsFile) as fp:
    pastIetfsSoup = BeautifulSoup(fp, "lxml")

# Using offline download pulled from this link:
# https://www.ietf.org/about/groups/iesg/past-members/
pastIesgFile = os.path.join(metaDataDir, "IESG_Past_Members.html")
with open(pastIesgFile) as fp:
    pastIesgSoup = BeautifulSoup(fp, "lxml")

ietfStartDates = {}
ietfEndDates = {}

for bp in pastIetfsSoup.body.main.find_all("div", class_="block-paragraph"):
    if len(bp.text) < 1000:
        continue
    pastIetfElements = bp.contents
    break

months = {name: num for num, name in enumerate(calendar.month_name) if num}

i = 0
numPastIetfElements = len(pastIetfElements)
while i + 1 < numPastIetfElements:
    titleElement = pastIetfElements[i]
    if titleElement.name == "p":
        i += 1
        continue
    assert titleElement.name == "h2"
    paragraphElement = pastIetfElements[i + 1]
    assert paragraphElement.name == "p"
    titleText = titleElement.text
    if titleText.startswith("IETF "):
        ietfNum = int(titleText[5:])
    else:
        assert titleText.endswith(" IETF")
        ietfNum = int(titleText[:-7])
    assert ietfNum > 0
    dateLine = paragraphElement.strings.__next__()
    if dateLine[0].isdigit():
        dls = dateLine.split(" ")
        year = dls[2][:4]
        startMonth = dls[1]
        endMonth = startMonth
        ds = dls[0].split("-")
        startDay = ds[0]
        endDay = ds[1]
    else:
        dls = dateLine.split(", ")
        year = dls[1][:4]
        ds = dls[0].split("-")
        ss = ds[0].strip().split(" ")
        startMonth = ss[0]
        startDay = ss[1]
        end = ds[1].strip()
        if end.isdigit():
            endMonth = startMonth
            endDay = end
        else:
            es = end.split(" ")
            endMonth = es[0]
            endDay = es[1]
    ietfStartDates[ietfNum] = date(int(year), months[startMonth], int(startDay))
    ietfEndDates[ietfNum] = date(int(year), months[endMonth], int(endDay))
    # print('IETF {n}: {s} - {e}'.format(n=ietfNum, s=ietfStartDates[ietfNum], e=ietfEndDates[ietfNum]))
    i += 2


def is_block(css_class):
    return css_class == "block-heading" or css_class == "block-paragraph"


def get_ietf_date(ietf, dates, minusOne=False):
    s = ietf.split(" (")[0]
    assert s.startswith("IETF ")
    ietfNum = int(s[5:])
    if minusOne:
        ietfNum -= 1
    return dates[ietfNum]


iesgBlocks = pastIesgSoup.body.main.find_all("div", class_=is_block)

i = 0
numIesgBlocks = len(iesgBlocks)
while i < numIesgBlocks:
    i += 1
    if iesgBlocks[i - 1].text == "Past IESG Members":
        break

adIetfs = {}
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
        "date_start": ietfStartDates[CURRENT_IETF - 1],
        "date_end": None,
        "members": CURRENT_IESG,
    }
)

while i + 1 < numIesgBlocks:
    timeframeBlock = iesgBlocks[i]
    assert "block-heading" in timeframeBlock["class"]
    membersBlock = iesgBlocks[i + 1]
    assert "block-paragraph" in membersBlock["class"]
    ietfs = set()
    for ietfStr in timeframeBlock.text.split(", "):
        ietfStr = ietfStr[: ietfStr.find(" (")]
        assert ietfStr.startswith("IETF ")
        ietfs.add(int(ietfStr[5:]))
    print(timeframeBlock.text)
    startDate = ietfStartDates[min(ietfs) - 1]
    endDate = ietfEndDates[max(ietfs)]
    print("timeframe {s} to {e}".format(s=startDate, e=endDate))
    names = []
    for memberItem in membersBlock.find_all("li"):
        memberDetails = memberItem.text.split(", ")
        assert len(memberDetails) == 2
        name = memberDetails[0]
        name = name.replace("\u00A0", "")
        names.append(name)
        adSet = adIetfs.get(name, set())
        adSet |= ietfs
        adIetfs[name] = adSet
        area = memberDetails[1]
        print('  {a}: "{n}"'.format(a=area, n=name))
    print(names)
    iesgs.append(
        {
            "date_start": startDate,
            "date_end": endDate,
            "members": names,
        }
    )
    i += 2

for name in CURRENT_IESG:
    adSet = adIetfs.get(name, set())
    adSet.add(CURRENT_IETF)
    adIetfs[name] = adSet

adEnds = {}
for ad in adIetfs:
    ietfs = adIetfs[ad]
    adEnds[ad] = [
        ietfEndDates[i] for i in ietfs if i + 1 not in ietfs and i != CURRENT_IETF
    ]

# for ad in adEnds:
#   print('{ad}: {s}'.format(ad=ad, s=adEnds[ad]))

# print(json.dumps(adEnds, indent=2, sort_keys=True, default=str))

adEndsFile = os.path.join(metaDataDir, "AD_term_ends.json")
with open(adEndsFile, "w") as f:
    json.dump(adEnds, f, indent=2, sort_keys=True, default=str)


iesgsFile = os.path.join(metaDataDir, "IESGs.json")
with open(iesgsFile, "w") as f:
    json.dump(iesgs, f, indent=2, sort_keys=True, default=str)
