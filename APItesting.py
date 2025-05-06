import json
import time
from datetime import datetime, timedelta
import requests
import getpass
import keyboard



def get_credentials():
    username = ""
    password = ""
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
        parent_array = parent_list.get("circuitName")

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


def extract_endpoint_info(endpoint):
    """Extracts endpoint details (from portRef). Returns cleaned and extracted endpoint data"""

    try:
        #print("inside extract:")
        #print(json.dumps(endpoint, indent=2))
        return {
            "name": endpoint["neName"],
            "portAID": endpoint["portAID"],
            "portNumber": endpoint["portNumber"],
            "slotNumber": endpoint["slotNumber"],
            "shelfNumber": endpoint["shelfNumber"],
            "ipAddress": endpoint["ipAddressLst"][0]["ipAddresses"][0]["ipAddress"]
        }
    
    except (KeyError, IndexError):
        #return None for missing fields
        return {
            "name": None,
            "portAID": None,
            "portNumber": None,
            "slotNumber": None,
            "shelfNumber": None,
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
        print(aEnd)
        print(zEnd)
        #extract details using helper function
        aEndInfo = extract_endpoint_info(aEnd)
        zEndInfo = extract_endpoint_info(zEnd)
        print(aEndInfo)
        print(zEndInfo)

        print(f"\nCircuit ID: {circuit_id}")

        print("A-End Info:")
        for k, v in aEndInfo.items():
            print(f"  {k}:  {v}")

        print("Z-End Info:")
        for k, v in zEndInfo.items():
            print(f"  {k}:  {v}")

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
        "tid": "DNVSMAHI-0000413A",
        "shelfName": "21",
        "slotName": "7",
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
    print("\nEndpoint details for top circuits:")
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
