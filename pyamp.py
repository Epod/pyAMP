import sys
if (sys.version_info < (3, 0)):
    # Stop running if running python 2
    print("Scripted for python 3+ only. Halting...")
    exit(0)

import base64
import csv
import os
import configparser

try:
    import pandas as pd
except ImportError:
    print("Missing module: pandas\nConsider running \"setup.py install\"")
    exit(2)

try:
    import menu3
except ImportError:
    print("Missing module: menu3\nConsider running \"setup.py install\"")
    exit(2)


try:
    import requests
except ImportError:
    print("Missing module: requests\nConsider running \"setup.py install\"")
    exit(2)


def stringToBase64(s):
    return base64.b64encode(s.encode('utf-8'))


def to_string(s):
    try:
        return str(s)
    except:
        #Change the encoding type if needed
        return s.encode('utf-8')


def reduce_item(key, value):
    global reduced_item
    # Reduction Condition 1
    if type(value) is list:
        i = 0
        for sub_item in value:
            reduce_item(key + '_' + to_string(i), sub_item)
            i = i + 1
    # Reduction Condition 2
    elif type(value) is dict:
        sub_keys = value.keys()
        for sub_key in sub_keys:
            reduce_item(key + '_' + to_string(sub_key), value[sub_key])
    # Base Condition
    else:
        reduced_item[to_string(key)] = to_string(value)



def getAMPauth(clientID, apiKey):
    return str(stringToBase64(str(clientID) + ":" + str(apiKey)), 'utf-8')


def getEventList(authstring, region):
    responseTypes = requests.get(region + "/v1/event_types",
                                 headers={'Authorization': 'Basic ' + authstring})
    return responseTypes.json()


def validateAMPcreds(region, authstring):
    try:
        response = requests.get(region + "/v1/version", headers={'Authorization': 'Basic ' + authstring})
        data = response.json()
        if (response.status_code == 200):
            return "ok"
        else:
            print("Error Connecting: " + str(response.status_code) + "\n" + str(data["errors"][0]["description"]))
            return "fail"
    except:
        print("Unknown Error: Failed to test if AMP credentials were valid. "
              "Likely due to no network connection or invalid AMP URL.")
        return "fail"


def getEvents(authstring, region, event_type, offset):
    if event_type == "all":
        responseTypes = requests.get(region + "/v1/events?&offset=" + offset,
                                     headers={'Authorization': 'Basic ' + authstring})
        return responseTypes.json()
    else:
        responseTypes = requests.get(region + "/v1/events?event_type[]=" + event_type + "&offset=" + offset,
                                     headers={'Authorization': 'Basic ' + authstring})
        return responseTypes.json()


def downloadMISPintel(url, key):
    try:
        # Disable SSL Warnings, as some internal MIST installs leverage self signed certs
        requests.packages.urllib3.disable_warnings()

        intel = requests.get(url + "/events/csv/download/", verify=False, headers={'Authorization': key})
        if intel.status_code == 200:
            try:
                intelcsv = open('intel/misp.csv', 'w', encoding='utf-8')
            except FileNotFoundError:
                os.makedirs('intel')
                intelcsv = open('intel/misp.csv', 'w', encoding='utf-8')
            intelcsv.write(intel.text)
            intel.close()
            return "success"
        else:
            print(bcolors.WARNING + "ERROR: Failed to fetch intel. Error code: " + str(intel.status_code)
                  + bcolors.ENDC)

    except:
        print(bcolors.WARNING + "ERROR: No HTTP status code returned. Could not download MISP Intel\n"
                                "Check URL & Connectivity"
              + bcolors.ENDC)
        exit()


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


# Start Script
print("AMP Tool Box")
config = configparser.ConfigParser()
# Check if config.ini file exists. If not, download new one or error
try:
    file = open('config.ini', 'r')
    file.close()
except IOError:
    try:
        print(bcolors.WARNING + "WARNING: config.ini file missing. Attempting to download a default copy... \n"
              + bcolors.ENDC)
        configfile = requests.get('https://raw.githubusercontent.com/Epod/pyAMP/master/config.ini')
        if configfile.status_code == 200:
            file = open('config.ini', 'w')
            file.write(configfile.text)
            file.close()
            print(bcolors.OKBLUE + "SUCCESS: The config.ini file was missing. "
                                   "Successfully re-downloaded with default values.\n "
                                   "Consider updating this file." + bcolors.ENDC)
        else:
            print("ERROR: The config.ini file is missing. Attempted to download a copy, but failed.\n")
            exit()
    except:
        print(bcolors.WARNING + "ERROR: config.ini file missing. Failed to automatically resolve... \n"
              + bcolors.ENDC)
        exit()


# Load Global Config Values
config.read('config.ini')
regionURL = config['AMP_API']['AMP_URL']

rootMenu = menu3.Menu(True)
rootMenuOptions = ["MISP", "Export CSVs"]
rootSelection = rootMenu.menu("Please make a selection", rootMenuOptions, "Your choice, 'q' to quit:")
rootMenu.success("You selected: " + rootMenuOptions[rootSelection-1])

# MISP Menu
if rootMenuOptions[rootSelection-1] == "MISP":
    mistMenu = menu3.Menu(False)
    mistMenuOptions = ["Update/Download Intel", "Compare Intel To AMP"]
    mistMenuSelection = mistMenu.menu("Select action", mistMenuOptions, "Your choice:")

# Download intel from MISP
    if mistMenuOptions[mistMenuSelection-1] == "Update/Download Intel":
        if downloadMISPintel(config['MISP_API']['MISP_URL'], config['MISP_API']['MISP_KEY']) == "success":
            data = pd.read_csv('intel/misp.csv')
            print(bcolors.OKBLUE)
            print(data['type'].value_counts())
            print("SUCCESS: Intelligence from MISP downloaded:\n" + bcolors.ENDC)

        else:
            print("ERROR: Could not download intelligence from MISP")
            exit(1)

# Compare intel from MISP to all events in AMP
    if mistMenuOptions[mistMenuSelection - 1] == "Compare Intel To AMP":
        exportMenu = menu3.Menu(False)

        creds = {'3rd Party API Client ID': config['AMP_API']['CLIENT_ID'], 'API Key': config['AMP_API']['API_KEY']}
        creds = exportMenu.config_menu("Enter AMP API Credentials", creds,
                                       "Select which field to edit, or Return to proceed: ")

        # Confirm Login Details Are Correct
        auth = getAMPauth(creds['3rd Party API Client ID'], creds['API Key'])

        if validateAMPcreds(regionURL, auth) == "ok":
            exportMenu.success("Credentials Accepted")
        else:
            print("ERROR: Could not validate AMP credentials.")
            exit()

        offsetloop = 0
        data = getEvents(auth, regionURL, "all", str(offsetloop))

        recordPerPage = data["metadata"]["results"]["items_per_page"]
        totalRecords = data["metadata"]["results"]["total"]
        cyclesNeeded = totalRecords / recordPerPage
        currentCycle = 0
        data2 = []

        while cyclesNeeded >= currentCycle:
            out = getEvents(auth, regionURL, "all", str(currentCycle * recordPerPage))
            for i in out["data"]:
                print(i["event_type"])
                # TODO: Cycle through amp events and compare against CSV.
            currentCycle += 1






# Export CSVs
# Step 1: Select The AMP Region Where The API Keys Are Located

if rootMenuOptions[rootSelection-1] == "Export CSVs":
    exportMenu = menu3.Menu(False)

    creds = {'3rd Party API Client ID': config['AMP_API']['CLIENT_ID'], 'API Key': config['AMP_API']['API_KEY']}
    creds = exportMenu.config_menu("Enter AMP API Credentials", creds,
                                   "Select which field to edit, or Return to proceed: ")

    # Confirm Login Details Are Correct
    auth = getAMPauth(creds['3rd Party API Client ID'], creds['API Key'])

    if validateAMPcreds(regionURL, auth) == "ok":
        exportMenu.success("Credentials Accepted")
    else:
        print("ERROR: Could not validate AMP credentials.")
        exit()



    # Get List Of Events To Export
    data = getEventList(auth, regionURL)
    eventTypes = []
    try:
        for i in data['data']:
            eventTypes.append(i['name'] + " (" + i['description'] + ")")
    except:
        print("Unknown Error")
        exit(1)
    eventSelection = exportMenu.menu("Select Which Event Type To Export", eventTypes, "Your choice: ")
    eventid = data['data'][int(eventSelection-1)]['id']


    # Get All Events From Selected Event ID
    offsetloop = 0
    data = getEvents(auth, regionURL, str(eventid), str(offsetloop))

    recordPerPage = data["metadata"]["results"]["items_per_page"]
    totalRecords = data["metadata"]["results"]["total"]
    cyclesNeeded = totalRecords/recordPerPage
    currentCycle = 1
    data2 = []

    while cyclesNeeded >= currentCycle:
        out = getEvents(auth, regionURL, str(eventid), str(currentCycle * recordPerPage))
        for i in out["data"]:
            data["data"].append(i)
        currentCycle += 1

    # Export JSON to CSV
    node = "data"
    csv_file_path = "output.csv"
    raw_data = data

    try:
        data_to_be_processed = raw_data[node]
    except:
        data_to_be_processed = raw_data

    processed_data = []
    header = []
    for item in data_to_be_processed:
        reduced_item = {}
        reduce_item(node, item)
        header += reduced_item.keys()
        processed_data.append(reduced_item)

    header = list(set(header))
    header.sort()

    with open(csv_file_path, 'w+', newline='') as f:
        writer = csv.DictWriter(f, header, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        for row in processed_data:
            writer.writerow(row)

