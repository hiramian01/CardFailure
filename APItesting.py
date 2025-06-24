import json
import time
from datetime import datetime, timedelta
import requests
import getpass
import re

def get_credentials():
    username = "GNMOA"
    password = "GNMOA123"
    #username = input("Enter your username: ")
    #password = getpass.getpass("Enter your password: ")
    return username, password


def fetch_circuits(username, password, payload):
    """Post request to fetch circuits, returns a list of circuit dicts"""
    response = requests.post(
        url = 'https://uts-prod.verizon.com/customerimpacts/api/v2/equipment', 
        json=payload, 
        timeout = (30, 200), 
        auth = (username, password)
    ) 
    return response.json()["results"]


def map_parent_child(circuits):
    """
    Creates a dict that maps each parent to a list of their children. If a ckt has no parent, added as a key with empty list. {parent: [child1, child2]}
     "parentCircuitList": {
                "parentCircuit": [
                    {
                        "parentCircuitId": "121744",
                        "parentCircuitName": "I1001/OTU4/DNVSMAHI/LYNNMACH"
    """
    parent_child_dict = {}
    #print(circuits)
    for circuit in circuits:
        parent = None
        #get the parentCircuitList if exists, if otw use empty dict
        parent_list = circuit.get("parentCircuitList", {})

        #get the parentCircuit list from above
        parent_array = parent_list.get("parentCircuit")

        #if parentCircuit exists and is non empty list, extract Name
        if isinstance(parent_array, list) and parent_array:
            parent = parent_array[0].get("parentCircuitName")
        

        #get child circuit name form current circuit object
        child = circuit["circuitName"]

        #if a valid parent exist and is not the same as the child, add to dict
        if parent and parent != child:
            parent_child_dict.setdefault(parent, []).append(child)

        else:
            #add the child as a top level circuit with no children
            parent_child_dict.setdefault(child, [])

    return parent_child_dict



def find_top_ckts(parent_child_dict):
    """Identifies top lvl ckts (aka those that are not children of any other ckt). Returns a list of ckt names"""
    all_children = {child for children in parent_child_dict.values() for child in children}   #flatten all children into a set
    return [parent for parent in parent_child_dict if parent not in all_children]             #top ckts are those not found in children set


def parse_port_aid(port_aid, raw_shelf, raw_slot, raw_port):
    """Parse shelf, slot and port from AID, if the format of AID is unrecognized, falls back to og raw json values"""
    if not port_aid:
        return raw_shelf, raw_slot, raw_port

    #pattern: dash seperated
    match = re.match(r"^[A-Za-z0-9]+-(\d+)-(\d+)-(\d+)", port_aid)
    if match:
        shelf, slot, port = map(int, match.groups())
        return shelf, slot, port
    
    #pattern: decimal 
    match = re.match(r"(\d+)\.(\d+)", port_aid)
    if match:
        shelf = slot = int(match.group(1))
        port = int(match.group(2))
        return shelf, slot, port

    return raw_shelf, raw_slot, raw_port



def extract_endpoint_info(endpoint):
    """Extracts endponit info and validates/corrects slot, shelf and port using AID. Falls back to raw json values when AID format is unrecognized"""

    port_aid = endpoint.get("portAID", "")

    #raw values from json
    raw_shelf = endpoint.get("shelfNumber")
    raw_slot = endpoint.get("slotNumber")
    raw_port = endpoint.get("portNumber")

    #extract correct values using portAID or fall back 
    shelfNumber, slotNumber, portNumber = parse_port_aid(port_aid, raw_shelf, raw_slot, raw_port)

    try:
        #print("inside extract:")
        #print(json.dumps(endpoint, indent=2))
        return {
            "name": endpoint.get("neName"),
            "portAID": port_aid,
            "shelfNumber": shelfNumber,
            "slotNumber": slotNumber,
            "portNumber": portNumber,
            "ipAddress": endpoint["ipAddressLst"][0]["ipAddresses"][0]["ipAddress"]
        }
    
    except (KeyError, IndexError):
        #return None for missing fields
        return {
            "name": None,
            "portAID": None,
            "shelfNumber": None,
            "slotNumber": None,
            "portNumber": None,
            "ipAddress": None
        }        
        

def fetch_endpoints(circuit_id):
    """Sends POST request to retrieve endpoint details for a given circuit_id (name, AID, slot, shelf, IP)"""

    payload = {
        "id": circuit_id,
        "system": "GNMOA",
        "sourceSys":"NAUTILUS",
        "clr" : "Y"
        }
    
    response = requests.post(
        url='https://uts-prod.verizon.com/circuitdetailms/api/v2/circuit/detail/b1', 
        json=payload, 
        timeout = (30, 200), 
        auth = ("GNMOA", "GNMOA123")
        )
    
    data = response.json()

    try:
        #navigate to portRef block for a and z end
        aEnd = data["circuitData"]["circuitLst"][0]["circuit"][0]["aEnd"][0]["portChannel"][0]["portRef"][0]
        zEnd = data["circuitData"]["circuitLst"][0]["circuit"][0]["zEnd"][0]["portChannel"][0]["portRef"][0]
        print('A Endpoint Raw Info:\n', aEnd, '\n')
        print('Z Endpoint Raw Info:\n', zEnd, '\n')
        #extract details using helper function
        aEndInfo = extract_endpoint_info(aEnd)
        zEndInfo = extract_endpoint_info(zEnd)
        print('A Extracted Info:\n', aEndInfo, '\n')
        print('Z Extracted Info:\n', zEndInfo, '\n')

        print(f"\nCircuit ID: {circuit_id}")

        print("A-End Info:")
        for k, v in aEndInfo.items():
            print(f"  {k}:  {v}")

        print("Z-End Info:")
        for k, v in zEndInfo.items():
            print(f"  {k}:  {v}")
        print('\n')

    except (KeyError, IndexError):
        print(f"\nCircuit ID: {circuit_id} - Endpoint data N/A")


def main():
    """
    Steps:
    1. Get login info
    2. Fetches all circuit data
    3. Maps parents to children
    4. Identifies top lvl ckts
    5. Fetches and prints endpoint info for each top lvl ckt
    """

    #Step 1: Get login 
    username, password = get_credentials()

    #Step 2: Fetch all circuit data
    payload = {
        "tid": "WTRLNYWT-0120324A",
        "shelfName": "21",
        "slotName": "8",       
        "system": "GNMOA"
    }

    circuits = fetch_circuits(username, password, payload)

    #Step 3: Mapping parent to children
    parent_child_dict = map_parent_child(circuits)
    print("Parent to Children mapping:")
    print(json.dumps(parent_child_dict, indent=2))


    #Step 4: Find all top level circuits
    top_circuits = find_top_ckts(parent_child_dict)
    print("\nTop Level Circuits:")
    print(top_circuits)

    #Step 5: Get endpoint info and print
    print("\nEndpoint details for top circuits:\n")
    for circuit_id in top_circuits:
        fetch_endpoints(circuit_id)


if __name__ == '__main__':
    main()

























# def circuit_details_new(self, cid='', mode='', sys=None):
#     if not cid:
#         return 'bad', None, 'A complete and valid circuit ID is required.'
#     cid = unquote_plus(cid)
#     url = f"{self.burl}circuitdetailms/api/v2/circuit/detail/GNMOA/b1?"
#     if mode == 'clr':
#         if sys:
#             url = f"{url}id={cid}&clr=Y&sourceSys={sys}"
#         else:
#             url = f"{url}id={cid}&clr=Y"
#     else:
#         if sys:
#             url = f"{url}id={cid}&circuitAttr=Y&cust=Y&diversity=Y&firstLvlRiderLst=Y&CircuitAliasLst=" \
#                 f"Y&muxMsgData=Y&stitched=Y&clr=Y&sourceSys={sys}"
#         else:
#             url = f"{url}id={cid}&circuitAttr=Y&cust=Y&diversity=Y&firstLvlRiderLst=Y&CircuitAliasLst=" \
#                 f"Y&muxMsgData=Y&stitched=Y&clr=Y"