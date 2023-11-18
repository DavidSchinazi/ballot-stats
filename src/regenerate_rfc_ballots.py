#!/usr/bin/env python3

from sys import argv

from util.parse_ballots import parse_ballot

if __name__ == "__main__":
    start_rfc_num = 9600
    end_rfc_num = 8500
    if len(argv) > 1:
        start_rfc_num = int(argv[1])
        if len(argv) > 2:
            end_rfc_num = int(argv[2])
        else:
            end_rfc_num = start_rfc_num
    rfc_increment = 1 if start_rfc_num <= end_rfc_num else -1
    for rfc_num in range(start_rfc_num, end_rfc_num + rfc_increment, rfc_increment):
        parse_ballot("rfc{r}".format(r=rfc_num))
