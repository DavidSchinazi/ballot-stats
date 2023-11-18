# Ballot Statistics

This repository exists to help gather data about historical IESG ballots.
It focuses on DISCUSS and ABSTAIN ballots.

## Setup

To install dependencies, run:

```
python3 -m pip install -r requirements.txt
```

## Regenerating Data

The python scripts in the `src` directory can be run directly. Produced data is saved in the `data` directory.

The `regenerate_rfc_ballots.py` script requires querying the IETF datatracker.
This repository is currently configured to use a localhost copy to avoid overwhelming the real datatracker.
Instructions for running your own local copy of the datatracker can be found [here](https://github.com/ietf-tools/datatracker).
Other scripts such as `regenerate_all_discusses.py` run solely using local json files from this repository.
