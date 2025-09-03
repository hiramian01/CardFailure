import json
import time
from datetime import datetime, timedelta
import requests
import getpass
from collections import defaultdict



def get_credentials():
    username = "SVC-UTCF-NTLS-PR"
    password = "6S6IkWadwVq45nZ6Z6DurHxoIUH"
    return username, password


def fetch_circuit(username, password, payload):
    """Post request to fetch circuit info"""
    response = requests.post(
        url = 'https://nautilus-services.verizon.com/trail-clr/trail/circuitInformation', 
        json=payload, 
        timeout = (30, 200), 
        auth = (username, password)
    )
    return response.json()


def endpoint_info(endpoint):
    try:
        aTID = endpoint.get("aEquipmentTid")
        zTID = endpoint.get("zEquipmentTid")
        aIP = endpoint.get("aIpAddress")
        zIP = endpoint.get("zIpAddress")

        a_result = aIP if aIP else aTID
        z_result = zIP if zIP else zTID

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
            "aEnd_result": a_result,
            "zEnd_result": z_result,
        }
    

    #null values for missing fields
    except:
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



def build_circuit_tree(trail_name, username, password, seen_trail_ids=None, level=0):
    
    if seen_trail_ids is None:
        seen_trail_ids = set()

    indent = "  " * level
    if trail_name in seen_trail_ids:
        return None #avoid duplicate 
    seen_trail_ids.add(trail_name)

    payload = {"trailName": trail_name}
    try:
        response = fetch_circuit(username, password, payload)
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
                nested = build_circuit_tree(rider_name, username, password, seen_trail_ids, level + 1)
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
    #Step 1: Get login 
    username, password = get_credentials()

    #Step 2: Fetch all circuit data
    cktID = "I1002/OTU4/LNCSNYLC/WSVLNYNC"

    circuit_tree = build_circuit_tree(cktID, username, password)
    return [circuit_tree] if circuit_tree else []


if __name__ == '__main__':
    result = main()
    print(json.dumps(result, indent=2))