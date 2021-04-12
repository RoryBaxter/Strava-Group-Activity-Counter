import requests
import os
import time
import json
import datetime
import argparse

parser = argparse.ArgumentParser()
#parser.add_argument("-w", "--week", type=int, help="Specify which week of activity to review", default=-1)
parser.add_argument("-c", "--culumative", action="store_true", help="Switch to displaying culumative effort instead of weekly effort")
parser.add_argument("-e", "--exclude", action="store_true", help="Excludes the current week's activities from the total")
parser.add_argument("-i", "--individual", action="store_true", help="In addition to the total time, also prints out the individual breakdown")
parser.add_argument("-l", "--last", action="store_true", help="Gets the details for last week's activities")
args = parser.parse_args()

start_time = 1615032000
time_in_a_week = 604800
per_page = 200 #200 per page seems to be the max
page = 1
daylight_savings_start = 1616893200

def get_week_start_epoch():
    ''' Get the epoch value for the start of this weeks time period '''
    
    current_time = int(time.time())
    elasped_time = current_time - start_time
    week_start_time = start_time + (elasped_time - (elasped_time%(time_in_a_week)))

    return week_start_time
    
def daylight_time_adjust(current_time):
    if current_time > daylight_savings_start:
        return current_time + 3600
    else:
        return current_time

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


if args.culumative and not args.exclude:
    activity_start_time = start_time
    activity_end_time = start_time + 9*time_in_a_week
    string = "overall"
else:
    activity_start_time = daylight_time_adjust(get_week_start_epoch())
    activity_end_time = daylight_time_adjust(activity_start_time + time_in_a_week)
    string = "this week"

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


total_time = sum(times.values())

if args.exclude:
    activity_start_time = start_time
    activity_end_time = start_time + 9*time_in_a_week

    request_url = "https://www.strava.com/api/v3/clubs/" + str(club_id) + "/activities"
    params = {"after": activity_start_time, "per_page": per_page, "page": page} 
    headers = {"Authorization": "Bearer " + access}

    times2 = {}

    activites_data2 = []
    r2 = requests.get(request_url, params=params, headers=headers)
    current_activites2 = json.loads(r2.text)
    activites_data2 += current_activites2

    for activitiy in activites_data2:
        name = activitiy["athlete"]["firstname"] + activitiy["athlete"]["lastname"]
        times2[name] = times2.get(name, 0) + activitiy["moving_time"]

    total_time2 = sum(times2.values())

    total_time = total_time2-total_time

    for athelte in times:
        times[athelte] = times2[athelte] - times[athelte]

    string = "excluding this week"

elif args.last:
    activity_start_time = daylight_time_adjust(get_week_start_epoch()-time_in_a_week)
    activity_end_time = activity_start_time + time_in_a_week

    request_url = "https://www.strava.com/api/v3/clubs/" + str(club_id) + "/activities"
    params = {"after": activity_start_time, "per_page": per_page, "page": page} 
    headers = {"Authorization": "Bearer " + access}

    times2 = {}

    activites_data2 = []
    r2 = requests.get(request_url, params=params, headers=headers)
    current_activites2 = json.loads(r2.text)
    activites_data2 += current_activites2

    for activitiy in activites_data2:
        name = activitiy["athlete"]["firstname"] + activitiy["athlete"]["lastname"]
        times2[name] = times2.get(name, 0) + activitiy["moving_time"]

    total_time2 = sum(times2.values())

    total_time = total_time2-total_time

    for athelte in times2:
        times[athelte] = times2[athelte] - times.get(athelte, 0)

    string = "last week"


times = {name[0]: times[name[0]] for name in sorted(times.items(), key=lambda x: x[1], reverse=True)}
readable_times = {name: str(datetime.timedelta(seconds=times[name])) for name in times.keys()}

if len(activites_data) == per_page:
    print("Warning, this may not inculde all activities")

print("Total time " + string, str(datetime.timedelta(seconds=total_time)))

if args.individual:
    for athelte, time in readable_times.items():
        if time == "0:00:00":
            break
        print(athelte[:-2], time)
