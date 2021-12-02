from operator import getitem
import json
import os

output_filepath = 'clean_entries.json'
input_filepath = 'entries.json'
metadata_filepath = 'tags.json'
with open(output_filepath, 'w', encoding='UTF-8') as o:
    o.write("[\n")
    with open(input_filepath, encoding='UTF-8') as f:

        for line in f:
            bad_line = False
            if line[0] == '}':  # end of the current JSON object
                line = '},\n{\n'
            if line == '    "code": {\n':
                bad_line = True
            if line == '    "name": {\n':
                bad_line = True
            if bad_line == False:
                o.write(line)

# delete trailing partial entries after final json object by searching for }
with open(output_filepath, "r+", encoding="utf-8") as file:
    # Move the pointer (similar to a cursor in a text editor) to the end of the file
    file.seek(0, os.SEEK_END)

    # This code means the following code skips the very last character in the file -
    # i.e. in the case the last line is null we delete the last line
    # and the penultimate one
    pos = file.tell() - 1

    # Read each character in the file one at a time from the penultimate
    # character going backwards, searching for a }
    # If we find a }, exit the search
    while pos > 0 and file.read(1) != "}":
        pos -= 1
        file.seek(pos, os.SEEK_SET)
    pos += 1
    file.seek(pos, os.SEEK_SET)

    # So long as we're not at the start of the file, delete all the characters ahead
    # of this position
    if pos > 0:
        file.seek(pos, os.SEEK_SET)
        file.truncate()

with open(output_filepath, 'a', encoding='UTF-8') as o:
    o.write("\n]")

with open(output_filepath, 'r', encoding='UTF-8') as o:
    x = json.load(o)

# Collect all tags, count how many entries include the tag
metadata = {}
for entry in x:
    tags = entry["tags"]
    id = entry["id"]
    for tag in tags:
        if tag in metadata:
            metadata[tag]["entries"] += 1
            metadata[tag]["ids"].append(id)
        else:
            metadata[tag] = {"entries": 1, "ids": [id]}

# Sort tags by decreasing frequency
tmp = metadata.items()
metadata = dict(
    sorted(metadata.items(), key=lambda x: getitem(x[1], 'entries'), reverse=True))
with open(metadata_filepath, 'w', encoding='utf-8') as md:
    json.dump(metadata, md, indent=4, sort_keys=False)

nshaders = len(x)
ntags = len(metadata)
nprint = 10
print(f"Scraped {nshaders} shaders with {ntags} unique tags.")
print(f"The {nprint} highest frequency tags are as follows:")
klist = list(metadata)
for i in range(nprint):
    tag = klist[i]
    frequency = metadata[klist[i]]["entries"]
    print(f"{tag:>20}:{frequency:>10}")
