import json
import time
from datetime import datetime, timedelta
import requests
import getpass
import re
from collections import defaultdict

#STEPS:
# 1. use the UTS API to log into a node, extract all the circuits on a card
# 2. then use nautilus API to extract all a end a z end info
# 3. extract all rider info

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
    return {
        "aEnd_name": endpoint.get("aEquipmentTid"),
        "aEnd_portAID": endpoint.get("aPortAid"),
        "aEnd_shelfNumber": endpoint.get("aEquipmentPhyShelfNo"),
        "aEnd_slotNumber": endpoint.get("aCardSlot"),
        "aEnd_portNumber": endpoint.get("aPortName"),
        "aEnd_ipAddress": endpoint.get("aIpAddress"),
        "zEnd_name": endpoint.get("zEquipmentTid"),
        "zEnd_portAID": endpoint.get("zPortAid"),
        "zEnd_shelfNumber": endpoint.get("zEquipmentPhyShelfNo"),
        "zEnd_slotNumber": endpoint.get("zCardSlot"),
        "zEnd_portNumber": endpoint.get("zPortName"),
        "zEnd_ipAddress": endpoint.get("zIpAddress")
    }



def rider_info(riders):
    if not riders:
        print("No rider circuits found.")
        return
    
    print("\n==== Rider Circuits ====")
    seen_trail_ids = set()

    for rider in riders:
        # print(rider)
        trail_id = rider.get("trailId")
        if trail_id and trail_id not in seen_trail_ids:
            seen_trail_ids.add(trail_id)

            trail_name = rider.get("trailName")
            parent_name = rider.get("parentCircuitName")

            print(f"\nRider trailID: {trail_id}")
            print(f"Rider CircuitID: {trail_name}")
            print(f"Parent CircuitID: {parent_name}\n")


def main():
    #Step 1: Get login 
    username, password = get_credentials()

    #Step 2: Fetch all circuit data
    payload = {
    "trailName": "I1001/OTU4/ITHCNYIH/WTRLNYWT"
    }

    response = fetch_circuit(username, password, payload)
    # print(json.dumps(response, indent=2))


    trail_data = response.get("trail", {})

    endp_info = endpoint_info(trail_data)

    #Circuit ID
    circuitID= payload["trailName"]
    print(f"\n=== Circuit ID: {circuitID} ====")

    #Endpoint Info
    print("\nA-End Info:")
    for k, v in endp_info.items():
        if k.startswith("aEnd"):
            print(f"  {k}:  {v}")

    print("Z-End Info:")
    for k, v in endp_info.items():
        if k.startswith("zEnd"):
            print(f"  {k}:  {v}") 

    
    #Rider Info
    rider_data = response.get("riderInformation", [])
    rider_info(rider_data)

if __name__ == '__main__':
    main()