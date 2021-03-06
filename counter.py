import requests
import os
import time
import json
import datetime
import argparse

parser = argparse.ArgumentParser()
#parser.add_argument("-w", "--week", type=int, help="Specify which week of activity to review", default=-1)
parser.add_argument("-c", "--culumative", action="store_true", help="Switch to displaying culumative effort instead of weekly effort")
args = parser.parse_args()

start_time = 1615032000
time_in_a_week = 604800
per_page = 200 #200 per page seems to be the max
page = 1

def get_week_start_epoch():
    ''' Get the epoch value for the start of this weeks time period '''
    
    current_time = int(time.time())
    elasped_time = current_time - start_time
    week_start_time = start_time + (elasped_time - (elasped_time%(time_in_a_week)))

    return week_start_time
    
    

with open("data.txt", "r") as file:
    data = file.readlines()

expires = data[0].replace("\n", "")
refresh = data[1].replace("\n", "")
access  = data[2].replace("\n", "")
club_id = data[3].replace("\n", "")

if time.time() > int(expires):
        with open("client_info.txt", "r") as file:
            client_info = file.readlines()
        client_id = int(client_info[0].replace("\n", ""))
        client_secret = client_info[1].replace("\n", "")

        refresh_params = {"client_id": client_id, "client_secret": client_secret, "grant_type": "refresh_token", "refresh_token": refresh}
        r = requests.post("https://www.strava.com/api/v3/oauth/token", params=refresh_params)
        refresh_json = json.loads(r.text)
        expires = refresh_json["expires_at"]
        refresh = refresh_json["refresh_token"]
        access  = refresh_json["access_token"]

        # Update keys
        with open("data.txt", "w") as file:
            file.write(str(expires))
            file.write("\n")
            file.write(str(refresh))
            file.write("\n")
            file.write(str(access))
            file.write("\n")
            file.write(str(club_id))


if args.culumative:
    activity_start_time = start_time
    activity_end_time = start_time + 9*time_in_a_week
else:
    activity_start_time = get_week_start_epoch()
    activity_end_time = activity_start_time + time_in_a_week

request_url = "https://www.strava.com/api/v3/clubs/" + str(club_id) + "/activities"
params = {"after": activity_start_time, "per_page": per_page, "page": page} 
headers = {"Authorization": "Bearer " + access}

times = {}

activites_data = []
r = requests.get(request_url, params=params, headers=headers)
current_activites = json.loads(r.text)
activites_data += current_activites

''' This is my attempt to get multiple pages of information, but it seems to always return the same page
while len(current_activites) == per_page:
    page += 1
    params = {"after": activity_start_time, "per_page": per_page, "page": page}
    r = requests.get(request_url, params=params, headers=headers)
    current_activites = json.loads(r.text)
    activites_data += current_activites
'''

for activitiy in activites_data:
    name = activitiy["athlete"]["firstname"] + activitiy["athlete"]["lastname"]
    times[name] = times.get(name, 0) + activitiy["moving_time"]


times = {name[0]: times[name[0]] for name in sorted(times.items(), key=lambda x: x[1], reverse=True)}
        
readable_times = {name: str(datetime.timedelta(seconds=times[name])) for name in times.keys()}

total_time = sum(times.values())

print("Total time", str(datetime.timedelta(seconds=total_time)))
if len(activites_data) == per_page:
    print("Warning, this may not inculde all activities")
