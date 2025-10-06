import json
import time
import re
import requests
from datetime import datetime, timedelta
from collections import defaultdict
import json
import getpass
import cf_manager


from Nautilus import build_circuit_tree
from CollectAlarms import main_alarms, login_alarms, all_lo_alarms
from creds2 import UTS_creds

#creds for api call
usernameAPI = UTS_creds["user"]
passwordAPI = UTS_creds["pass"]



#-----UTS API------

def get_main_circuits(tid, slotNum):
    """
    Fetches all main circuits from a failed card using UTS API
    """

    # tid = "BATVOHBT-0110101B"

    payload = {
        "system": "GNMOA",
        "sourceSys":"NAUTILUS"
        }

    response = requests.get(
        url='https://uts-prod.verizon.com/equipmentdetailms/api/v2/equipment/hierarchy/GNMOA/b1?tid=' + tid + '&inputControl=NETWORK_ELEMENT&outputControl=CHANNEL', 
        json=payload, 
        timeout = (30, 200), 
        auth = (usernameAPI, passwordAPI)
        )

    data = response.json()

    """
    finds all of the circuits that are on a pktotn card for 6500 T. Depending on the card type the database uses different verbage for slots cards and ports
    NEED TO: add some sort of type model or device verification/pathing
    BLLVWAHV-0110109A fails name = name": "CI / FIM TYPE 3 (NTK504CC)

    """
    if data["status"] == "SUCCESS":
        found = False
        cirlist = []
        slots = data["equipmentDtlData"]["equipmentLst"][0]["equipmentContainer"][0]["virtualNE"][0]["rack"][0]["shelf"][0]["slot"]
        for slot in slots:
            #change slotName out for a variable
            if slot["slotName"] == slotNum:
                if slot["card"][0]["cardType"] not in ("WL3n", "5x100G/12x40G QSFP28/QSFP+"):
                    print("Wrong type of card")
                    return None
                    
                    
                print("Circuits on this card:")
                #WL3n Card Type
                if "slot" in slot:
                    subslots = slot["slot"]
                    for subslot in subslots:
                        if "card" in subslot:
                            if "channel" in subslot["card"][0]["port"][0]:
                                found = True
                                ckt1 = subslot["card"][0]["port"][0]["channel"][0]["circuit"][0]["circuitName"]
                                cirlist.append(ckt1)
                                print(ckt1)
                                
                #5x100G/12x40G QSFP28/QSFP+ Card Type
                else:
                    ports = slot["card"][0]["port"]
                    for port in ports:
                        if "port" in port:
                            subports = port["port"]
                            for subport in subports:
                                if "circuit" in subport:
                                    ckt2 = subport["circuit"][0]["circuitName"]
                                    cirlist.append(ckt2)
                                    print(ckt2)
                                    found  = True

                        elif "circuit" in port:
                            found = True
                            ckt3 = port["circuit"][0]["circuitName"]
                            cirlist.append(ckt3)
                            print(ckt3)

                if not found:
                    print("No circuits found")
                    return None
                

        return cirlist 


def process_alarm(ip, aid, label=""):
  if ip:
    try:
      is_connected, output = login_alarms(ip)
      if is_connected:
        alarm_list = output.splitlines()
        lo_alarm, loss_al, match = all_lo_alarms(alarm_list, aid)
        print(f"{label} - {ip}")
        print(lo_alarm)
        print(loss_al)
        print(match)
        
    except Exception as e:
      print(f"unable to perform. {e}")
  else:
    print("No IP found for {label} end")

    
def alarm_check(circuit):
  endpoint = circuit.get("endpoint_info", {})
  aIP = endpoint.get("aEnd_result")
  zIP = endpoint.get("zEnd_result")
  
  aAID = endpoint.get("aEnd_portAID")
  zAID = endpoint.get("zEnd_portAID")  
  
  process_alarm(aIP, aAID, label="A End")
  process_alarm(zIP, zAID, label="Z End")
  
  for rider in circuit.get("riders", []):
    #recurse on rider circuits if any
    alarm_check(rider)
  
  


def main():
    mgr = cf_manager.get_manager()
    params = mgr.script_metadata.parameters
    

    tid = params["tid"]
    slotNum = params["slot"]
  
    ckt_list = get_main_circuits(tid, slotNum)
    print("all circuits on this card: ", ckt_list)

    all_tree = []
    for ckt in ckt_list:
        ckt_tree = build_circuit_tree(ckt)
        if ckt_tree:
            all_tree.append(ckt_tree)
            alarm_check(ckt_tree)
            
    return all_tree
    
  

if __name__ == '__main__':
    result = main()
    print(json.dumps(result, indent=2))


