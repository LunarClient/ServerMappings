import requests
import os
import json

SERVERS_FILE_URL = "https://raw.githubusercontent.com/LunarClient/ServerMappings/master/servers.json"
MAIN_TEXT = """
 _      _____    _____ __  __   _______          _ 
| |    / ____|  / ____|  \/  | |__   __|        | |
| |   | |      | (___ | \  / |    | | ___   ___ | |
| |   | |       \___ \| |\/| |    | |/ _ \ / _ \| |
| |___| |____   ____) | |  | |    | | (_) | (_) | |
|______\_____| |_____/|_|  |_|    |_|\___/ \___/|_|
                                                   
    Lunar Client Server Mappings Tool by Radi0o/Zffu         
"""




    

def Menu_1_Input():
    os.system("cls")
    t = MAIN_TEXT + """
    
    
    
    """
    print(t)
    INPUT_NAME = input("Server Name:  ")
    INPUT_ID = INPUT_NAME.lower()
    INPUT_MAINADDRESS = input("Server Main Address:  ")
    addresses = input("Server Addresses (Please add an ; at the end of every address):  ")
    INPUT_ADDRESSES = addresses.split(";")
    INPUT_MAINVERSION = input("Server Main Version:  ")
    v = input("Server Versions (Please add an ; at the end of every address):  ")
    INPUT_VERSIONS = v.split(";")
    os.system("cls")
    print(t)
    print("Server Name -> " + INPUT_NAME)
    print("Server Id -> " + INPUT_ID)
    print("Server Main Address -> " + INPUT_MAINADDRESS)
    print("Server Addresses -> " + str(INPUT_ADDRESSES))
    print("Server Main Version -> " + INPUT_MAINVERSION)
    print("Server Versions -> " + str(INPUT_VERSIONS))
    print("""
    
    Enter y to continue
    
    """)
    conf = input("")
    if conf.lower() == "y":
        f1 = open("servers.json")
        data = json.load(f1)
        f1.close()
        data.append({"id": INPUT_ID, "name": INPUT_NAME, "primaryAddress": INPUT_MAINADDRESS, "versions": INPUT_VERSIONS, "addresses": INPUT_ADDRESSES})
        f = open("servers.json", "w")
        f.write(str(data))
        f.close()
    

def Menu_1_Fetch():
    os.system("cls")
    print(MAIN_TEXT + """
    
    Fetching the Servers.json file...
    
    """)
    r = requests.get(SERVERS_FILE_URL)
    SERVERS_FILE = r.text
    f = open("servers.json", "w")
    f.write(str(SERVERS_FILE))
    f.close()
    Menu_1_Input()
    

def Menu_Main():
    os.system("cls")
    print(MAIN_TEXT + """
                                       
    Requirements:
        - You need a 512x512 logo
    Actions:
    1 -> Generate the servers.json file
    
    """)
    action = input(">  ")
    if action == str(1):
        Menu_1_Fetch()

Menu_Main()
