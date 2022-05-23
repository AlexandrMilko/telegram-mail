import sys
from telethon.sync import functions, types
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.functions.messages import SaveDraftRequest
from telethon.sync import errors
import pandas as pd
import numpy as np
import math
import time
import threading
import os
import random

#IMPORTANT: EACH ACCOUNT SENDS ONLY TO THOSE CONTACTS WHICH WERE PARSED BY IT. TELEGRAM DOESNT ALLOW DO IT IN ANOTHER WAY

accounts = {
    #EXAMPLE:
    #'phone': {'api_id': api_id, 'api_hash': api_hash}
}
LATITUDE_LONGITUDE_STEP = 0.027272727272*4 # approximately 12 km (We need it to scatter points of parsing contacts all over the city)
PARSE_DELAY = 30 #seconds
PARSE_DELAY_NOT_UPDATING = 300 # We set a delay if telegram doesnt update data in GetLocatedRequest (People Nearby functionality)
BAN_DELAY = 88000
MIN_MSG_DELAY = 20 # For randomizing delay between sending messages
MAX_MSG_DELAY = 120
sh_start_script = 'start_gnome_client.sh' #shell script which runs a required client in a separate gnome-terminal window

TASK = sys.argv[1]
# "spam" - spamming messages to contacts from /Data/cities_people_parsed ; files format: (phone)_(city)_people.txt
# "parse" - gathering contacts from different points across cities, which are provided by a file downloaded from stopputin.net (PROTESTS_FILE VARIABLE)
# "count" - counts number of gathered contacts ;
# "groups" - currently is being developed. Grouping contacts into separate groups

PROTESTS_FILE = sys.argv[2]
WD = os.getcwd()

from datetime import datetime
now = datetime.now()
current_time = now.strftime("%H_%M_%S___%B_%d_%Y")
import logging #TODO add loging
logs_filename = f"{current_time}.log"
path = os.path.join(WD, 'logs',  logs_filename)
logging.basicConfig(level=logging.INFO, filename=path, filemode='w')

def create_dataframe_stopputin(html_text_file_name):
    def get_processed_data(file_name):
        with open(file_name, 'r') as file:
            lines = file.readlines()
            # uniting lines into data arrays
            # number_to_unite = 4
            data = []
            for i in range(len(lines)):
                if ((i + 1) % 4) == 0:
                    data_row = [lines[i - 3], lines[i - 2], lines[i - 1], lines[i]]
                    data.append(data_row)
            return data

    # html_text_file is downloaded from stopputin.net
    data = get_processed_data(html_text_file_name)
    dataframe = pd.DataFrame(data=data, columns=['Country', 'City', 'Time', 'Info'])
    dataframe.to_csv('stopputindata.csv')
    return dataframe

def calc_points_to_parse(starting_point, LATITUDE_LONGITUDE_STEP):
    points_to_parse = []
    for x_offset_point in range(-1, 2):
        for y_offset_point in range(-1, 1):
            point_x = starting_point[0] + x_offset_point * LATITUDE_LONGITUDE_STEP
            point_y = starting_point[1] + y_offset_point * LATITUDE_LONGITUDE_STEP
            point = [point_x, point_y]
            points_to_parse.append(point)

    return points_to_parse

def parse_cities():
    split_n = len(accounts)
    work_part = 0
    for phone in accounts.keys():
        os.system(f"gnome-terminal -x {WD}/{sh_start_script} {phone} {TASK} {split_n} {work_part} {PROTESTS_FILE}")
        time.sleep(5)
        work_part += 1

def client_parse_cities(client, phone, protests_df, cities_df): # client._phone somewhy doesn't work. That's why we use phone
    logs = []
    print("INFO: STARTED PARSING ALL THE CITIES")
    logging.info("STARTED PARSING ALL THE CITIES")
    print(client.session, "THIS CLIENT HAS STARTED PARSING")
    logging.info(f"{client.session}, THIS CLIENT HAS STARTED PARSING")
    for city in protests_df['City']:
        city = city.replace('\n', '') #Cities have \n in their end
        people_ids = parse_people_in_city(client, phone, city, cities_df, LATITUDE_LONGITUDE_STEP)
        try: #TODO check do we need here try statement??
            if people_ids and people_ids!=['City data wasnt found in world_cities.csv']:
                with open(f"{WD}/Data/cities_people_parsed/{phone}_{city.replace(' ', '_')}_people.txt", 'w') as file:
                    file.write("\n".join(map(str, people_ids)))
        except AttributeError as e:
            print(e, city, people_ids, "ln98")
    print("INFO: FINISHED PARSING")
    logging.info("FINISHED PARSING"+"\n")

    return logs

def parse_people_in_city(client, phone, city, cities_df, LATITUDE_LONGITUDE_STEP):

    #def init_ids(): #TODO add such func for readability
    city_data = cities_df.loc[cities_df['city'] == city]
    try:
        coords = city_data['lat'].values[0], city_data['lng'].values[0]
    except IndexError as e:
        print("WARNING: ", e, f"'{city}' value wasn't found in world_cities.csv")
        return ['City data wasnt found in world_cities.csv']
    points_to_parse = calc_points_to_parse(coords, LATITUDE_LONGITUDE_STEP)

    dir = f'{WD}/Data/cities_people_parsed'
    file = f'{phone}_{city.replace(" ", "_")}_people.txt'
    if does_exist(dir, file):
        ids_parsed_before = read_parsed_ids(dir, file)
        ids = ids_parsed_before.copy()
    else:
        ids_parsed_before = set()
        ids = set()

    for coords_i in range(len(points_to_parse)):
        coords = points_to_parse[coords_i]
        print('INFO: Parsing from new point: ', city, coords)
        people_data_array = get_people_nearby(client, coords[0], coords[1])
        number_to_pause = 10 # how many same contacts have to be spotted to delay program.
        repeats_number = 0
        for person in people_data_array:
            person_id = person[1]
            if person_id not in ids:
                ids.add(person_id) # to Check if the people_data_array wasn't updated by telegram
            else:
                if person_id not in ids_parsed_before: # If telegram doesnt update data, we set a delay.
                    repeats_number += 1
                    print(person, "FOUND A REPEAT!!!")
                    print(repeats_number, "REPEATS!!")
                    if repeats_number >= number_to_pause:
                        print("STARTED PAUSING")
                        repeats_number = 0
                        threading.Thread(target=print_delaying_progress, args=[PARSE_DELAY_NOT_UPDATING]).start()
                        time.sleep(PARSE_DELAY_NOT_UPDATING)
                        break
        try:
            print('INFO: I am going to parse: ', city, points_to_parse[coords_i+1])
        except IndexError:
            pass
        time.sleep(PARSE_DELAY)

    return ids

def read_parsed_ids(dir, file_name):
    ids_set = set()
    path = os.path.join(dir, file_name)
    with open(path, 'r') as file:
        ids_map = map(int, file.readlines())
    try:
        for id in ids_map:
            ids_set.add(id)
    except ValueError as e:
        print("ERROR: ", e, "WITH CITY: ", file_name)
    return ids_set

def count_parsed_ids(protest_df):
    ids = set()
    for phone in accounts.keys():
        for city in protest_df['City']:
            path = f'{WD}/Data/cities_people_parsed'
            filename = f'{phone}_{city.replace(" ", "_")}_people.txt'.replace("\n", '')
            if does_exist(path, filename):
                city_ids = read_parsed_ids(path, filename)
                for id in city_ids:
                    ids.add(id)
    return len(ids)

def does_exist(dir, file_name): return (file_name in os.listdir(dir))

def spam_message():
    task = "spam"
    for phone in accounts.keys():
        os.system(
            f"gnome-terminal -x {WD}/{sh_start_script} {phone} {task} {PROTESTS_FILE}")
        time.sleep(5)

def client_spam(client, phone, protests_df): #IMPORTANT: protests_df is file with full list of protests
    logs = []
    client.connect()
    people_count = 0
    for protest in protests_df.iterrows():
        print("INFO: Spamming citizens of", protest[1]['City'])
        logging.info(f"Spamming citizens of, {protest[1]['City']}")
        city = protest[1]['City'].replace("\n", "") #All cities have \n in their end, so we remove it
        Time = protest[1]['Time']
        details = protest[1]['Info']
        website_link = "https://www.stopputin.net/"
        video_link = "https://www.instagram.com/tv/Cah22a8IKjK/?utm_medium=share_sheet"
        message = f"Hi there! Please, come to support my country, Ukraine! I would really appreciate it. \nCity: {city} \nTime: {Time} \n{details} \nLet's stop Putin together! We can do it ;) \nP.S. please, do not report spam"
        dir = f'{WD}/Data/cities_people_parsed'
        file = f'{phone}_{city.replace(" ", "_")}_people.txt'
        if does_exist(dir, file):
            ids = read_parsed_ids(dir, file)
            for id in ids:
                if not client.get_messages(id, limit=10):
                    try:
                        result = client(SaveDraftRequest(peer=id, message=message, no_webpage=True))
                        # client.send_message(id, message)

                        people_count += 1
                        print("INFO: Sent message to", id)
                        logging.info("Sent message to, {id}")
                        print("INFO: People were sent: ", people_count)
                        logging.info("People were sent: {people_count}")

                        delay = random.randrange(MIN_MSG_DELAY, MAX_MSG_DELAY)
                        print("INFO: ", f"{delay}s DELAY BEFORE SENDING NEXT MESSAGE")
                        time.sleep(delay)
                    except errors.rpcerrorlist.PeerFloodError as e:
                        print(f"ERROR: Got PeerFloodError from telegram. Script is stopping now. It will resume in {BAN_DELAY} seconds")
                        logging.error(f"Got PeerFloodError from telegram. Script is stopping now. It will resume in {BAN_DELAY} seconds"+"\n")
                        client.disconnect()
                        print_delaying_progress(BAN_DELAY)
                        print("INFO: Resuming spamming")
                        logging.info("Resuming spamming"+"\n")
                        client.connect()
                        continue

                    except errors.rpcerrorlist.InputUserDeactivatedError as e:
                        print("ERROR(ln188): ", e)
                        logging.error(f"ERROR(ln188): , {e}")
    return logs

def create_groups(): #IMPORTANT! BETA VERSION
    task = "group"
    for phone in accounts.keys():
        os.system(
            f"gnome-terminal -x /home/aleksandr/Desktop/telegram_mailing/scripts_and_data/{sh_start_script} {phone} {task} {PROTESTS_FILE}")
        time.sleep(5)

def client_create_group(client, phone, protests_df):
    logs = []
    client.connect()
    people_count = 0
    for protest in protests_df.iterrows():
        print("INFO: Creating a group with citizens of", protest[1]['City'])
        logging.info(" Creating a group with citizens of, {protest[1]['City']}" + "\n")
        city = protest[1]['City'].replace('\n', '') #All cities have \n in their end, so we remove it
        dir = f'{WD}/Data/cities_people_parsed'
        file = f'{phone}_{city.replace(" ", "_")}_people.txt'
        if does_exist(dir, file):
            ids = read_parsed_ids(dir, file)
            i = 0
            for id in ids:
                if not client.get_messages(id, limit=10):
                    i += 1
                    print(i, "AddChatREQUESTS HAVE BEEN SENT ALREADY")
                    try:
                        result = client(functions.messages.AddChatUserRequest(
                            chat_id=617746958,
                            user_id=id,
                            fwd_limit=42
                        ))
                        print(id, f"WAS ADDED TO THE GROUP, {city}")
                        time.sleep(150)
                    except errors.rpcerrorlist.PeerFloodError as e:
                        print(e)
                        return None
                    except errors.rpcerrorlist.InputUserDeactivatedError as e:
                        print(e)
                        time.sleep(150)
                    except errors.rpcerrorlist.UserAlreadyParticipantError as e:
                        print(e)
                        time.sleep(150)
                    except errors.rpcerrorlist.UserNotMutualContactError as e:
                        print(e)
                        time.sleep(150)
                    except errors.rpcerrorlist.UserPrivacyRestrictedError as e:
                        print(e)
                        time.sleep(150)

    return logs

def print_delaying_progress(delay):
    for second in range(delay):
        time.sleep(1)
        print("INFO: STARTED WAITING")
        print(f"{second}/{delay} left")
        print("INFO: CONTINUING WORK..")

def triangulate_from_coords(p0, p1, p2, d0, d1, d2):

    #assuming elevation = 0
    earthR = 6371
    LatA = p0[0]
    LonA = p0[1]
    DistA = d0/1000 # meters to kilemeters
    LatB = p1[0]
    LonB = p1[1]
    DistB = d1/1000 # meters to kilemeters
    LatC = p2[0]
    LonC = p2[1]
    DistC = d2/1000 # meters to kilemeters

    #using authalic sphere
    #if using an ellipsoid this step is slightly different
    #Convert geodetic Lat/Long to ECEF xyz
    #   1. Convert Lat/Long to radians
    #   2. Convert Lat/Long(radians) to ECEF
    xA = earthR *(math.cos(math.radians(LatA)) * math.cos(math.radians(LonA)))
    yA = earthR *(math.cos(math.radians(LatA)) * math.sin(math.radians(LonA)))
    zA = earthR *(math.sin(math.radians(LatA)))

    xB = earthR *(math.cos(math.radians(LatB)) * math.cos(math.radians(LonB)))
    yB = earthR *(math.cos(math.radians(LatB)) * math.sin(math.radians(LonB)))
    zB = earthR *(math.sin(math.radians(LatB)))

    xC = earthR *(math.cos(math.radians(LatC)) * math.cos(math.radians(LonC)))
    yC = earthR *(math.cos(math.radians(LatC)) * math.sin(math.radians(LonC)))
    zC = earthR *(math.sin(math.radians(LatC)))

    P1 = np.array([xA, yA, zA])
    P2 = np.array([xB, yB, zB])
    P3 = np.array([xC, yC, zC])

    #from wikipedia
    #transform to get circle 1 at origin
    #transform to get circle 2 on x axis
    ex = (P2 - P1)/(np.linalg.norm(P2 - P1))
    i = np.dot(ex, P3 - P1)
    ey = (P3 - P1 - i*ex)/(np.linalg.norm(P3 - P1 - i*ex))
    ez = np.cross(ex,ey)
    d = np.linalg.norm(P2 - P1)
    j = np.dot(ey, P3 - P1)

    #from wikipedia
    #plug and chug using above values
    x = (pow(DistA,2) - pow(DistB,2) + pow(d,2))/(2*d)
    y = ((pow(DistA,2) - pow(DistC,2) + pow(i,2) + pow(j,2))/(2*j)) - ((i/j)*x)

    # only one case shown here
    z = np.sqrt((pow(DistA,2) - pow(x,2) - pow(y,2))*-1)

    #triPt is an array with ECEF x,y,z of trilateration point
    triPt = P1 + x*ex + y*ey + z*ez

    #convert back to lat/long from ECEF
    #convert to degrees
    lat = math.degrees(math.asin(triPt[2] / earthR))
    lon = math.degrees(math.atan2(triPt[1],triPt[0]))

    return lat, lon

def get_people_nearby(client, lat, long):
    client.connect()
    point = client(functions.contacts.GetLocatedRequest(
        geo_point=types.InputGeoPoint(lat=lat, long=long),
        self_expires=1000
    ))
    people_data_array = []
    for update_peer_located in point.updates:
        for peer_located in update_peer_located.peers:
            try:
                person = client(GetFullUserRequest(peer_located.peer.user_id))
                person_data = [person.user.first_name, person.user.id, peer_located.distance]
                people_data_array.append(person_data)
                print("INFO: Person has been parsed: ", person_data)
            except AttributeError as e:
                print(e, 'ln21')
    return people_data_array

def get_divided_work(df, split_n):
    return np.array_split(df, split_n)

if __name__ == "__main__":
    if TASK == 'spam':
        spam_message()
    elif TASK == 'parse':
        parse_cities()
    elif TASK == 'count':
        protests_df = create_dataframe_stopputin(PROTESTS_FILE)
        print("NUMBER OF PARSED IDS: ", count_parsed_ids(protests_df))
    elif TASK == 'group':
        create_groups()
