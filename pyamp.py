import base64
import csv

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

print("AMP Tool Box")

rootMenu = menu3.Menu(True)
rootMenuOptions = ["Export CSVs"]
rootSelection = rootMenu.menu("Please make a selection", rootMenuOptions, "Your choice, 'q' to quit:")
rootMenu.success("You selected: " + rootMenuOptions[rootSelection-1])


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


def getEventList(authstring, region):
    responseTypes = requests.get("https://" + region + "/v1/event_types",
                                 headers={'Authorization': 'Basic ' + authstring})
    return responseTypes.json()


def getEvents(authstring, region, event_type, offset):
    responseTypes = requests.get("https://" + region + "/v1/events?event_type[]=" + event_type + "&offset=" + offset,
                                 headers={'Authorization': 'Basic ' + authstring})
    return responseTypes.json()


# Export CSVs
# Step 1: Select The AMP Region Where The API Keys Are Located

if rootMenuOptions[rootSelection-1] == "Export CSVs":
    exportMenu = menu3.Menu(False)
    regionMenuOptions = ["NA", "APJC", "EU"]
    regionMenuSelection = exportMenu.menu("Select the region the AMP instance is located", regionMenuOptions,
                                          "Your choice:")
    exportMenu.success("Setting region to: " + regionMenuOptions[regionMenuSelection-1])

    if regionMenuOptions[regionMenuSelection-1] == "NA":
        regionURL = "api.amp.cisco.com"
    if regionMenuOptions[regionMenuSelection - 1] == "APJC":
        regionURL = "api.apjc.amp.cisco.com"
    if regionMenuOptions[regionMenuSelection - 1] == "EU":
        regionURL = "api.eu.amp.cisco.com"

    creds = {'3rd Party API Client ID': "000000000000000000000", 'API Key': "00000000-0000-0000-0000-000000000000"}
    creds = exportMenu.config_menu("Enter AMP API Credentials", creds,
                                   "Select which field to edit, or Return to proceed: ")

    # Confirm Login Details Are Correct
    auth = str(stringToBase64(creds['3rd Party API Client ID'] + ":" + creds['API Key']), 'utf-8')
    response = requests.get("https://" + regionURL + "/v1/version", headers={'Authorization': 'Basic ' + auth})
    data = response.json()

    try:
        if(response.status_code == 200):
            exportMenu.success("Credentials Accepted")
        else:
            exportMenu.warn("Error Connecting: " + str(response.status_code) + "\n"
                            + str(data["errors"][0]["description"]))
            exit(1)
    except:
        exportMenu.warn("Error Connecting: Unknown Error")
        exit(1)


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

