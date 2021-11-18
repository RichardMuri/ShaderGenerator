import os
import requests
import json
from ratelimit import limits, sleep_and_retry


base_url = "https://www.shadertoy.com/api/v1/shaders/"
key = '?key='

failed_entries = []
fail_path = 'failed_ids.json'
id_index = 0
prev_path = 'prev_index'
if os.path.exists(prev_path):
    with open(prev_path, 'r') as file:
        id_index = int(file.readline())

output_path = "entries.json"
entries = []


def dumpToFiles():
    with open(fail_path, '+a') as file:
        for item in failed_entries:
            file.write(item + '\n')
    with open(prev_path, 'w') as file:
        file.write(str(id_index))


@sleep_and_retry
@limits(calls=1, period=1)
def getRequest(id, retry=False):
    request = base_url + id + key
    response = requests.get(request)
    success = response.status_code == 200
    if success == False and retry:
        response, success = getRequest(id)
    elif success == True and retry == False:
        failed_entries.append(id)
    return response, success


def requestToEntry(request):
    json_obj = request.json()["Shader"]
    output = {}
    output["id"] = json_obj["info"]['id']
    output['name'] = json_obj['info']['name']
    output['tags'] = json_obj['info']['tags']
    output['nfiles'] = len(json_obj['renderpass'])
    output['code'] = ''
    for code in json_obj['renderpass']:
        output['code'] = output['code'] + '\n' + code['code']
    return output


# test_id = "NddSWs"
# test_id = "slt3z8"
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

output_file = open(output_path, 'a+')
entries_scraped = 0
N = len(ids)
for i in range(id_index, N):
    id_index = i
    try:
        request, success = getRequest(ids[i], retry=True)
    except Exception as e:
        failed_entries.append(ids[i])
        print(f"Caught exception while making request: {e}")
    if success:
        try:
            entry = requestToEntry(request)
            json.dump(entry, output_file, ensure_ascii=False, indent=4)
            entries_scraped = entries_scraped + 1
        except Exception as e:
            print(f"Caught exception while writing to file:\n{e}")
    if entries_scraped % 250 == 0:
        print(f"Scraped {entries_scraped} out of {N} entries.")
        output_file.flush()

output_file.close()
dumpToFiles()
