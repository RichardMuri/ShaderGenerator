import os
import requests
import json
from ratelimit import limits, sleep_and_retry


base_url = "https://www.shadertoy.com/api/v1/shaders/"
key = ''
with open('shader_api_key') as file:
    key = file.readline()

# Retain failed entries in case we want to retry later
failed_entries = []
fail_path = 'failed_ids.json'
id_index = 0
# Retain index of key in case we want to retry from that point
prev_path = 'prev_index'
if os.path.exists(prev_path):
    with open(prev_path, 'r') as file:
        id_index = int(file.readline())

output_path = "entries.json"
entries = []


def dumpToFiles():
    # Dump errors to files
    with open(fail_path, '+a') as file:
        for item in failed_entries:
            file.write(item + '\n')
    with open(prev_path, 'w') as file:
        file.write(str(id_index))


@sleep_and_retry
@limits(calls=1, period=1)
def getRequest(id, retry=False):
    # Request a shader once per second, retry up to once if it fails
    request = base_url + id + key
    response = requests.get(request)
    success = response.status_code == 200
    if success == False and retry:
        response, success = getRequest(id)
    elif success == True and retry == False:
        failed_entries.append(id)
    return response, success


def requestToEntry(request):
    # Retain only information we care about from the shader
    json_obj = request.json()["Shader"]
    output = {}
    output["id"] = json_obj["info"]['id']
    output['name'] = json_obj['info']['name']
    output['tags'] = json_obj['info']['tags']
    output['description'] = json_obj['info']['description']
    output['nfiles'] = len(json_obj['renderpass'])
    # Convert multi-file shaders into single code block
    output['code'] = ''
    for code in json_obj['renderpass']:
        output['code'] = output['code'] + '\n' + code['code']
    return output


# Get the ID for all API visible shaders
get_all = "https://www.shadertoy.com/api/v1/shaders" + key
if not os.path.exists('shader_ids.json'):
    all = requests.get(get_all)
    with open('shader_ids.json', 'w', encoding='utf-8') as file:
        ids = all.json()
        json.dump(ids, file, ensure_ascii=False, indent=4)
else:
    with open('shader_ids.json') as file:
        ids = json.load(file)
ids = ids["Results"]

# Begin scraping, dump every entry to file as we scrape
output_file = open(output_path, 'a+', encoding='utf-8')
entries_scraped = 0
N = len(ids)
for i in range(id_index, N):
    id_index = i
    try:
        # Request shader
        request, success = getRequest(ids[i], retry=True)
    except Exception as e:
        # Failed to get shader for some reason, add to list if we want to retry later
        failed_entries.append(ids[i])
        print(f"Caught exception while making request: {e}")
    if success:
        try:
            # Convert the shader into our format and write to file
            entry = requestToEntry(request)
            json.dump(entry, output_file, ensure_ascii=False, indent=4)
            entries_scraped = entries_scraped + 1
        except Exception as e:
            # We likely had an encoding error, avoid crashing the program but give up on this ID
            print(f"Caught exception while writing to file:\n{e}")
    if entries_scraped % 250 == 0:
        print(f"Scraped {entries_scraped} out of {N} entries.")
        output_file.flush()

output_file.close()
dumpToFiles()
