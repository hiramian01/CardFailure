import json
import time
from datetime import datetime, timedelta
import requests
import getpass
from collections import defaultdict

from creds2 import nautilus_creds, optools_creds

#creds for api call
usernameAPI = nautilus_creds["user"]
passwordAPI = nautilus_creds["pass"]

usernameOT = optools_creds["user"]
passwordOT = optools_creds["pass"]


def fetch_circuit(payload):
    """Post request to fetch circuit info"""
    response = requests.post(
        url = 'https://nautilus-services.verizon.com/trail-clr/trail/circuitInformation', 
        json=payload, 
        timeout = (30, 200), 
        auth = (usernameAPI, passwordAPI)
    )
    return response.json()


def endpoint_info(endpoint):
    try:
        aTID = endpoint.get("aEquipmentTid")
        zTID = endpoint.get("zEquipmentTid")
        aIP = endpoint.get("aIpAddress")
        zIP = endpoint.get("zIpAddress")

        # a_result = aIP if aIP else aTID
        # z_result = zIP if zIP else zTID
        
        # if aIP is None:
        aFetchedIP = fetch_ip(aTID)

        # if zIP is None:
        zFetchedIP = fetch_ip(zTID)

        return {
            "aEnd_name": aTID,
            "aEnd_portAID": endpoint.get("aPortAid"),
            "aEnd_shelfNumber": endpoint.get("aEquipmentLogShelfNo"),
            "aEnd_slotNumber": endpoint.get("aCardSlot"),
            "aEnd_portNumber": endpoint.get("aPortName"),
            "aEnd_ipAddress": aIP,
            "zEnd_name": zTID,
            "zEnd_portAID": endpoint.get("zPortAid"),
            "zEnd_shelfNumber": endpoint.get("zEquipmentLogShelfNo"),
            "zEnd_slotNumber": endpoint.get("zCardSlot"),
            "zEnd_portNumber": endpoint.get("zPortName"),
            "zEnd_ipAddress": zIP,
            "aEnd_result": aFetchedIP,
            "zEnd_result": zFetchedIP,
        }
    

    #null values for missing fields
    except Exception as e:
        print(f"Error getting info: {e}")
        return {
            "aEnd_name": None,
            "aEnd_portAID": None,
            "aEnd_shelfNumber": None,
            "aEnd_slotNumber": None,
            "aEnd_portNumber": None,
            "aEnd_ipAddress": None,
            "zEnd_name": None,
            "zEnd_portAID": None,
            "zEnd_shelfNumber": None,
            "zEnd_slotNumber": None,
            "zEnd_portNumber": None,
            "zEnd_ipAddress": None            
        }


def fetch_ip(tid):
    #if retrieved IP from Nautilus API returns None for either endpoint, utilize the Optools API to retrieve IP
    """Sends POST request to retrieve endpoint details for a given circuit_id (name, AID, slot, shelf, IP)"""

    
    response = requests.get(
        url='https://optools-inventory1.vzbi.com/api/v1.0/populate?tid=' + tid, 
        timeout = (30, 200), 
        auth = (usernameOT, passwordOT)
        )
    
    data = response.json()

    ip = data["IP"]

    return ip


def build_circuit_tree(trail_name, seen_trail_ids=None, level=0):
    
    if seen_trail_ids is None:
        seen_trail_ids = set()

    indent = "  " * level
    if trail_name in seen_trail_ids:
        return None         #avoid duplicate 
    seen_trail_ids.add(trail_name)

    payload = {"trailName": trail_name}
    try:
        response = fetch_circuit(payload)
        trail_data = response.get("trail", {})
        riders = response.get("riderInformation", [])

        circuit = {
            "circuit_id": trail_name,
            "endpoint_info": endpoint_info(trail_data),
            "riders": []
        }


        for rider in riders:
            rider_name = rider.get("trailName")
            if rider_name:
                nested = build_circuit_tree(rider_name, seen_trail_ids, level + 1)
                if nested:
                    circuit["riders"].append(nested)

        return circuit


    except Exception as e:
        print(f"{indent}Error fetching circuit {trail_name}: {e}")
        return {
            "circuit_id":trail_name,
            "endpoint_info": None,
            "riders": [],
            "error": str(e)
        }


def main():

    #Fetch all circuit data
    cktID = "I1002/GE100/CNCPOHIQ/CNCTOHCI"

    circuit_tree = build_circuit_tree(cktID)
    return [circuit_tree] if circuit_tree else []


if __name__ == '__main__':
    result = main()
    print(json.dumps(result, indent=2))
