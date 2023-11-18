#!/usr/bin/env python3

from sys import argv

from util.parse_ballots import parse_ballot

rfc_num = 9293

if len(argv) > 1:
    rfc_num = int(argv[1])

parse_ballot("rfc{r}".format(r=rfc_num))
