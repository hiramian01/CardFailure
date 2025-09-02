import json
import time
from datetime import datetime, timedelta
import requests
import getpass
import re
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
            "aEnd_shelfNumber": endpoint.get("aEquipmentPhyShelfNo"),
            "aEnd_slotNumber": endpoint.get("aCardSlot"),
            "aEnd_portNumber": endpoint.get("aPortName"),
            "aEnd_ipAddress": aIP,
            "zEnd_name": zTID,
            "zEnd_portAID": endpoint.get("zPortAid"),
            "zEnd_shelfNumber": endpoint.get("zEquipmentPhyShelfNo"),
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



def rider_info(riders, username, password, seen_trail_ids=None, level=1):
    if not riders:
        print("No rider circuits found.")
        return
    
    if seen_trail_ids is None:
        seen_trail_ids = set()

    indent = "  " * level
    print(f"\n{indent}==== Rider Level {level} =====")


    for rider in riders:
        # print(rider)
        trail_id = rider.get("trailId")
        trail_name = rider.get("trailName")
        parent_name = rider.get("parentCircuitName")

        if trail_id and trail_id not in seen_trail_ids:
            seen_trail_ids.add(trail_id)

            print(f"\nRider trailID: {trail_id}")
            print(f"Rider CircuitID: {trail_name}")
            print(f"Parent CircuitID: {parent_name}\n")

            #fetch this riders own circuit info
            payload = {"trailName": trail_name}
            try:
                rider_response = fetch_circuit(username, password, payload)
                rider_trail_data = rider_response.get("trail", {})
                rider_endpoint_info = endpoint_info(rider_trail_data)

                print(f"{indent}-> Rider A-End: {rider_endpoint_info.get('aEnd_result')}")
                print(f"{indent}-> Rider Z-End: {rider_endpoint_info.get('zEnd_result')}")

                #recursive call for nested riders
                sub_riders = rider_response.get("riderInformation", [])
                if sub_riders:
                    rider_info(sub_riders, username, password, seen_trail_ids, level + 1)

            except Exception as e:
                print(f"{indent}Error fetching rider circuit {trail_name}: {e}")


def main():
    #Step 1: Get login 
    username, password = get_credentials()

    #Step 2: Fetch all circuit data
    payload = {
    "trailName": "I1002/OTU4/LNCSNYLC/WSVLNYNC"
    }

    response = fetch_circuit(username, password, payload)
    # print(json.dumps(response, indent=2))


    trail_data = response.get("trail", {})

    endp_info = endpoint_info(trail_data)

    print(f"\n=== Parent Circuit ID: {payload['trailName']} ===")

    #Step 3: Extract endpoint Info
    print("\nA-End Info:")
    for k, v in endp_info.items():
        if k.startswith("aEnd"):
            print(f"  {k}:  {v}")

    print("Z-End Info:")
    for k, v in endp_info.items():
        if k.startswith("zEnd"):
            print(f"  {k}:  {v}") 

    
    #Step 4: Recursive rider chain
    rider_data = response.get("riderInformation", [])
    rider_info(rider_data, username, password)

if __name__ == '__main__':
    main()