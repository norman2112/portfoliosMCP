"""A tool to generate a AgilePlace manifest file with predefined IDs."""

import csv
import random
import json
from collections import defaultdict

ROWS = 7000000  # A huge file for NatWest would look like 4600000 rows

AP_TABLES_USED_IN_OKRS = ["user", "board", "card"]

# Need to be exhaustive
OTHER_AP_TABLES = [
    "lane",
    "taskBoards",
    "planningSeries",
    "planningIncrement",
    "customCardFieldValue",
    "cardTypes",
    "comment",
    "customCardFieldValue",
]


def gen_id(n=8):
    """Generate a random number with n digits."""
    d0 = str(random.randint(1, 9))
    ds = [str(random.randint(0, 9)) for _ in range(n - 1)]
    return "".join([d0] + ds)


def generate_rows(rows=ROWS):
    """Generate the manifest rows."""
    rs = []
    noted_ids = defaultdict(list)

    for i in range(rows):
        r = random.randint(0, 2)
        note = False
        if r in [0, 1]:
            entity = random.choice(AP_TABLES_USED_IN_OKRS)
            note = True
        else:
            entity = random.choice(OTHER_AP_TABLES)

        from_id = gen_id()
        if note:
            noted_ids[entity].append(from_id)
        to_id = gen_id(10)
        rs.append([from_id, to_id, entity, entity])
    return rs, noted_ids


def write_to_file(rows, file="output.csv"):
    """Write the rows to a file."""

    with open(file, "w", newline="") as csvfile:
        writer = csv.writer(csvfile, delimiter=",")
        writer.writerow(["OriginalId", "NewId", "TableName", "EntityName"])
        writer.writerows(rows)


if __name__ == "__main__":
    rows, noted_ids = generate_rows()
    write_to_file(rows)
    with open("noted_ids.json", "w") as jsonfile:
        jsonfile.write(json.dumps(noted_ids))
    print("done")
