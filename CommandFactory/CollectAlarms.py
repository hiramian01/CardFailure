import pexpect 
import json
import time
import re
import cf_manager

from creds import machine_creds

#m2m creds for device log in
username = machine_creds["user"].strip()
password = machine_creds["pass"].strip()

pw = f"\"{password}\""



def login_alarms(ip):
    
    """
    SSH login to a Ciena 6500
    Returns tuple: (is_connected: bool, alarms: string, tid: string)
    """
    try:
        #Create SSH session
        session = pexpect.spawn(
          f'ssh -oKexAlgorithms=+diffie-hellman-group14-sha1,diffie-hellman-group1-sha1 {ip}',
          timeout = 60, 
          encoding = "utf-8"
          ) 
        
        #session.logfile = sys.stdout
        session.expect(["Starting Interactive TL1 Command Mode.", pexpect.EOF, pexpect.TIMEOUT])
        session.expect(["<", pexpect.EOF, pexpect.TIMEOUT])
        
        time.sleep(1)
        
                
        cmd = f"ACT-USER::{username}:CTAG::{pw};"
        session.send(cmd)
        session.expect(["<", pexpect.EOF, pexpect.TIMEOUT])
        output = session.before
        print(output)
    
        time.sleep(1)
        
        session.expect([";", "<", pexpect.EOF, pexpect.TIMEOUT])
        output1 = session.before
        print(output1)
        
        session.send("RTRV-COND-ALL:::CTAG;")
        session.expect([";\r\n<", pexpect.EOF, pexpect.TIMEOUT], timeout=60)  #wait for tl1 end of output ; then < on newline
        output2 = session.before + session.after
        print(output2)
        
        session.send("RTRV-COND-ALL:::CTAG:::ALRMSTAT=DISABLED;")
        session.expect([";\r\n<", pexpect.EOF, pexpect.TIMEOUT], timeout=60)  #wait for tl1 end of output ; then < on newline
        output3 = session.before + session.after
        print(output3)
        
        # pattern = r'\nM  CTAG COMPLD(.*);\r\n<.*?ALRMSTAT=DISABLED;\r?\n\s+([A-Z]+-[0-9A-Z]+).*M  CTAG COMPLD(.*);\r\n<'
        
        # pattern2 = r'M\s+CTAG COMPLD([\s\S]*?);'
        # active_match = re.search(pattern2, output2, re.DOTALL)
        # disabled_match = re.search(pattern2, output3, re.DOTALL)
        
        # active2 = active_match.group(1).strip() if active_match else ""
        # disabled2 = disabled_match.group(1).strip() if disabled_match else ""

        # total = active2 + disabled2
        # active = ""
        # tid = ""
        # disabled = ""
        
        # match = re.search(pattern, output2 + output3, re.DOTALL)
        # if match:
        #     active = match.group(1).strip()
        #     print("active", active)
        #     tid = match.group(2).strip()
        #     print("tid", tid)
        #     disabled = match.group(3).strip()
        #     print("disabled", disabled)
        # else:
        #     print("\nError: pattern not found\n")
            
            
        # out = active + '\r\n' + disabled + '\n\n'
        out2 = output2 + output3
        
        return True, out2
      
    except Exception as e:
        print(f"[ERROR] SSH login failed: {e}")
        return False, None, None
    
    
    
def all_lo_alarms(all_alarms, aid):
    """
    Finds and processes alarms for a specific aid.

    Args:
        all_alarms (list): A list of alarm strings.
        aid (str): The specific aid to search for.
    """
    print("all alarms", all_alarms)
    found_alarms = []
    matched_alarm = []
    loss_of_alarm_present = False
    #Isolate our endpoint alarms
    for alarm in all_alarms:
      alarm =str(alarm).strip()
      
      
      if "loss of" in alarm.lower():
        found_alarms.append(alarm)
        
        if aid in alarm:
          loss_of_alarm_present = True
          matched_alarm.append(alarm)
            
          
    print("found lo alarms:\n" + "\n".join(found_alarms))
    print("found matched aid alarm:\n" + "\n".join(matched_alarm))


    # Print the results if no loss alarm
    if not loss_of_alarm_present:
      print("\n***No 'loss of' condition was found among these alarms for the circuit endpoint.***")
        
    return loss_of_alarm_present, found_alarms, matched_alarm
    
    

    
def main_alarms():
  mgr = cf_manager.get_manager()
  params = mgr.script_metadata.parameters
  
  ip = params["ip"]
  aid = params["aid"]
  
  try:
    is_connected, output = login_alarms(ip)
    if is_connected:
      
      alarm_list = output.splitlines()
      lo_alarm, loss_al, match = all_lo_alarms(alarm_list, aid)
      print(lo_alarm)
      print(loss_al)
      print(match)
      
  except Exception as e:
    print(f"unable to perform Intercard Suspected Eval. {e}")
  
  
  
if __name__ == '__main__':
  main_alarms()
  
