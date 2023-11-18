#!/usr/bin/env python3

from sys import argv

from util.parse_ballots import parse_ballot

if __name__ == "__main__":
    if len(argv) > 1:
        rfc_num = int(argv[1])
        parse_ballot("rfc{r}".format(r=rfc_num))
    else:
        for rfc_num in range(9600, 8500, -1):
            parse_ballot("rfc{r}".format(r=rfc_num))
