#!/usr/bin/env python3

from datetime import datetime, timezone
import json
import os
import requests
from bs4 import BeautifulSoup
from sys import argv, exit

rfcNum = 9293

if len(argv) > 1:
  rfcNum = int(argv[1])

resp = requests.get('http://localhost:8000/doc/rfc{}/history/'.format(rfcNum))
if resp.status_code == 404:
  print('RFC {r} does not exist'.format(r=rfcNum))
  exit(0)

assert resp.ok
soup = BeautifulSoup(resp.text, "lxml")

if len(soup.find_all(lambda tag: tag.name == 'a' and 'IESG evaluation record' in tag.text)) == 0:
  print('RFC {r} was not evaluated by the IESG'.format(r=rfcNum))
  exit(0)

adEndsFile = os.path.join(os.path.dirname(__file__), 'AD_term_ends.json')
with open(adEndsFile, 'r') as f:
  adEnds = json.load(f)

iesgsFile = os.path.join(os.path.dirname(__file__), 'IESGs.json')
with open(iesgsFile, 'r') as f:
  iesgsJ = json.load(f)

def date_from_json(s):
  if s is None:
    return None
  return datetime.strptime(s, '%Y-%m-%d').replace(tzinfo=timezone.utc)

iesgs = []
for iesg in iesgsJ:
  iesgs.append({
    'date_start': date_from_json(iesg['date_start']),
    'date_end': date_from_json(iesg['date_end']),
    'members': iesg['members'],
  })

for ad in adEnds:
  adEnds[ad] = [date_from_json(e) for e in adEnds[ad]]
  # print('{ad}: {s}'.format(ad=ad, s=adEnds[ad]))

#print(soup.prettify())

class Ballot:
  ad = None
  ballotType = None
  startTime = None
  endTime = None
  text = None
  endReason = None

  def __init__(self, ad, ballotType, startTime):
    self.ad = ad
    self.ballotType = ballotType
    self.startTime = startTime
  
  def __str__(self):
    return '{t} {s} {e} {txt}'.format(t=self.ballotType, s=self.startTime, e=self.endTime, txt=self.text if False else '')

ballots = {}
ballotStartTime = None
ballotEndTime = None

rows = soup.body.table.tbody.findAll('tr')
for row in reversed(rows):
  rowId = row['id']
  cells = row.findAll('td')
  timeStamp = datetime.strptime(cells[0].div['title'], '%Y-%m-%d %H:%M:%S %z')
  revision = cells[1].text
  author = cells[2].text
  fullActionDivs = cells[3].find_all(attrs={"class": "full"})
  if len(fullActionDivs) > 0:
    action = ' '.join(fullActionDivs[0].strings)
  else:
    action = cells[3].text
  if action == 'Created "Approve" ballot':
    ballotStartTime = timeStamp
    for iesg in iesgs:
      if iesg['date_start'] > timeStamp:
        continue
      if iesg['date_end'] is not None and iesg['date_end'] < timeStamp:
        continue
      for ad in iesg['members']:
        ballotsForAd = ballots.get(ad, [])
        ballotsForAd.append(Ballot(ad, 'No Record', timeStamp))
        ballots[ad] = ballotsForAd
    # print('{t} - {a}'.format(t=timeStamp, a=action))
  elif action == 'Closed "Approve" ballot':
    ballotEndTime = timeStamp
    for a in ballots:
      ballots[a][-1].endTime = timeStamp
      ballots[a][-1].endReason = 'evaluation_closed'
  elif action.startswith('['):
    actionType = action[1:action.find(']')]
    if actionType == 'Ballot Position Update':
      actionDetails = action[action.find(']') + 2:]
      # print('{t} - {d}'.format(t=timeStamp, d=actionDetails))
      if actionDetails.startswith('New position, '):
        ballotType = actionDetails.split(', ')[1]
        ballotsForAuthor = ballots.get(author, [])
        if len(ballotsForAuthor) > 0:
          ballotsForAuthor[-1].endTime = timeStamp
          ballotsForAuthor[-1].endReason = 'new_position'
        ballotsForAuthor.append(Ballot(author, ballotType, timeStamp))
        ballots[author] = ballotsForAuthor
      else:
        changeSplit = actionDetails.split(' has been changed to ')
        if len(changeSplit) > 1:
          ballotType = changeSplit[1].split(' from ')[0]
          ballotsForAuthor = ballots.get(author, [])
          if len(ballotsForAuthor) > 0:
            ballotsForAuthor[-1].endTime = timeStamp
            ballotsForAuthor[-1].endReason = 'position_updated'
          ballotsForAuthor.append(Ballot(author, ballotType, timeStamp))
          ballots[author] = ballotsForAuthor
    elif actionType == 'Ballot discuss':
      actionDetails = action[action.find(']') + 2:]
      ballotsForAuthor = ballots.get(author, [])
      if len(ballotsForAuthor) > 0:
        if ballots[author][-1].text is None:
          ballots[author][-1].text = actionDetails
        else:
          ballotsForAuthor[-1].endTime = timeStamp
          ballotsForAuthor[-1].endReason = 'discuss_updated'
          newBallot = Ballot(author, ballots[author][-1].ballotType, timeStamp)
          newBallot.text = actionDetails
          ballotsForAuthor.append(newBallot)
      ballots[author] = ballotsForAuthor
    elif actionType == 'Ballot comment':
      actionDetails = action[action.find(']') + 2:]
      ballotsForAuthor = ballots.get(author, [])
      if len(ballotsForAuthor) > 0 and ballots[author][-1].ballotType == 'Abstain':
        if ballots[author][-1].text is None:
          ballots[author][-1].text = actionDetails
        else:
          ballotsForAuthor[-1].endTime = timeStamp
          ballotsForAuthor[-1].endReason = 'comment_updated'
          newBallot = Ballot(author, ballots[author][-1].ballotType, timeStamp)
          newBallot.text = actionDetails
          ballotsForAuthor.append(newBallot)
      ballots[author] = ballotsForAuthor

# print('ballotStartTime={}'.format(ballotStartTime))

res = {}
res['rfc'] = rfcNum
res['evaluation_start'] = ballotStartTime
res['evaluation_end'] = ballotEndTime

resBallots = {}

for a in ballots:
  # print(a)
  resBallotsForAd = []
  for b in ballots[a]:
    for adEnd in adEnds[b.ad]:
      if b.startTime < adEnd and (b.endTime is None or adEnd < b.endTime):
        b.endTime = adEnd
        b.endReason = "ad_term_ended"
    resBallotsForAd.append({
      'type': b.ballotType,
      'start': b.startTime,
      'end': b.endTime,
      'end_reason': b.endReason,
      'text': b.text,
    })
    # print('  {}'.format(b)) 
  resBallots[a] = resBallotsForAd

res['all_ballots'] = resBallots

rfcFile = os.path.join(os.path.dirname(__file__), 'rfc{}.json'.format(rfcNum))
with open(rfcFile, "w") as f:
  json.dump(res, f, indent=2, sort_keys=True, default=str)

print('RFC {r} analyzed succesfully'.format(r=rfcNum))
exit(0)
