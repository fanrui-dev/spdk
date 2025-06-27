import re
import json

local_db_p99_lat = []
with open("local.log", "r") as file:
    for line in file:
        match = re.search(r'lat \(ms,99%\): (\d+\.\d{2})', line)
        if match:
            local_db_p99_lat.append(float(match.group(1)))

remote_db_p99_lat = []
with open("remote.log", "r") as file:
    for line in file:
        match = re.search(r'lat \(ms,99%\): (\d+\.\d{2})', line)
        if match:
            remote_db_p99_lat.append(float(match.group(1)))

local_storage_utilization = []
with open("local.csv", "r") as file:
    for line in file:
        local_storage_utilization.append(float(line))

remote_storage_utilization = []
with open("remote.csv", "r") as file:
    for line in file:
        remote_storage_utilization.append(float(line))

print(len(local_db_p99_lat))
print(len(remote_db_p99_lat))
print(len(local_storage_utilization))
print(len(remote_storage_utilization))

data = {
    "local_db_p99_lat": local_db_p99_lat,
    "local_storage_utilization": local_storage_utilization,
    "remote_db_p99_lat": remote_db_p99_lat,
    "remote_storage_utilization": remote_storage_utilization
}

with open("data.json", "w") as json_file:
    json.dump(data, json_file, indent=4)  # `indent=4` for pretty formatting
