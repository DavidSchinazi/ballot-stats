#!/usr/bin/env python3

from sys import argv

from util.parse_ballots import parse_ballot


class ParsedRfc:
    rfc_nums = []

    def parse_rfc(self, rfcs):
        if isinstance(rfcs, int):
            if rfcs not in self.rfc_nums:
                self.rfc_nums.append(rfcs)
        elif isinstance(rfcs, str):
            if "," in rfcs:
                self.parse_rfc(rfcs.split(","))
            elif "-" in rfcs:
                rfcs_split = rfcs.split("-")
                assert len(rfcs_split) == 2
                start_rfc_num = int(rfcs_split[0])
                end_rfc_num = int(rfcs_split[1])
                rfc_increment = 1 if start_rfc_num <= end_rfc_num else -1
                self.parse_rfc(
                    range(start_rfc_num, end_rfc_num + rfc_increment, rfc_increment)
                )
            else:
                self.parse_rfc(int(rfcs))
        else:
            for rfc in rfcs:
                self.parse_rfc(rfc)


if __name__ == "__main__":
    parsed_rfc = ParsedRfc()
    if len(argv) > 1:
        parsed_rfc.parse_rfc(argv[1:])
    else:
        parsed_rfc.parse_rfc("9600-7000")
    for rfc_num in parsed_rfc.rfc_nums:
        parse_ballot("rfc{r}".format(r=rfc_num))
