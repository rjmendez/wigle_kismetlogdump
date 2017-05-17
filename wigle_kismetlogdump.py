#!/usr/bin/env python
import sys
import os
import tarfile
import shutil
import requests
from time import gmtime, strftime, sleep
from subprocess import call

# Set variables

API_success=None
CAPDIR="/var/kismet/KismetTemp/"
STODIR="/var/kismet/Kismet/"
D=strftime("%Y-%m-%d-%H.%M.%S", gmtime())

AUTH_Encoded='<Go to https://wigle.net/account click "Show my token" and include the value from "Encoded for use:" here>'
# example
#AUTH_Encoded='SGFzaHRhZyBjaGlsbHdhdmUga2l0c2NoLCB3YXlmYXJlcnMgcG9rIHBvayBjYXJkaWdhbiBsdW1iZXJzZXh1YWwgaXMK'

# Define copy function

def copy_netxml_storage(CAPDIR, STODIR):
    for file in os.listdir(CAPDIR):
        if file.endswith(".netxml"):
            full_cap_file_name = os.path.join(CAPDIR, file)
            full_sto_file_name = os.path.join(STODIR, file)
            if (os.path.isfile(full_cap_file_name)):
                print("Saving file: " + full_sto_file_name)
                shutil.copy(full_cap_file_name, STODIR)
            else:
                print( full_cap_file_name + " Is not a file.")
    return

# Define cleanup function

def delete_netxml_temp(CAPDIR):
    for file in os.listdir(CAPDIR):
        if file.endswith(".netxml"):
            full_cap_file_name = os.path.join(CAPDIR, file)
            if (os.path.isfile(full_cap_file_name)):
                print("Deleting file: " + full_cap_file_name)
                os.remove(full_cap_file_name)
            else:
                print( full_cap_file_name + " Is not a file.")
        if file.endswith(".tar.gz"):
            full_cap_file_name = os.path.join(CAPDIR, file)
            if (os.path.isfile(full_cap_file_name)):
                print("Deleting file: " + full_cap_file_name)
                os.remove(full_cap_file_name)
            else:
                print( full_cap_file_name + " Is not a file.")
    return

# Define dataset packing function

def compress_dataset(output_dataset, input_folder):
    tar = tarfile.open(output_dataset, "w:gz")
    for file in os.listdir(input_folder):
        if file.endswith(".netxml"):
            full_file_name = os.path.join(input_folder, file)
            if (os.path.isfile(full_file_name)):
                tar.add(full_file_name)
    tar.close()
    return

# Define dataset upload function

def upload(dataset, file):
    files = {'file': (file, open(dataset, 'rb'), 'multipart/form-data', {'Expires': '0'})}

    url = 'https://api.wigle.net/api/v2/file/upload'

    response = requests.post(url, files=files, headers={'Authorization':'Basic ' + AUTH_Encoded})
    #print(response)
    #print(response.text)
    print("\n")
    if '200' in str(response):
        API_success=True
        print('Got ' + str(response) + ' from wigle.net API, dataset uploaded.')
        return True
    else:
        API_success=False
        print('Recieved ' + str(response) + ' from API, upload failed.')
        return False

# Define API checking function

def check_api():

    url = 'https://api.wigle.net/api/v2/profile/user'

    response = requests.get(url, headers={'Authorization':'Basic ' + AUTH_Encoded})
    #print(response)
    #print(response.text)
    if '200' in str(response):
        API_success=True
        print('Got ' + str(response) + ' from wigle.net API seems to be working!')
        return True
    else:
        API_success=False
        print('Recieved ' + str(response) + ' from API.')
        return False

# Define kismet service stop

def Stop_kismet():
    call(["systemctl", "stop", "kismet.service"])
    sleep(5)
    call(["killall", "kismet_server"]) # Making sure
    call(["killall", "kismet_capture"]) # Making sure?
    sleep(5)
    return

# Run
# Lets make sure we can talk to the wigle.net API
if check_api():
    print("Starting the log dump, stopping kismet before backing up files.")
    Stop_kismet()
    print("Backing up files to " + STODIR)
    copy_netxml_storage(CAPDIR, STODIR)
    output_dataset=os.path.join(CAPDIR, D + ".tar.gz")
    compress_dataset(output_dataset, CAPDIR)
    print("Starting wigle.net upload.")
    for file in os.listdir(CAPDIR):
        if file.endswith(".tar.gz"):
            print('Sending: ' + os.path.join(CAPDIR, file))
            Upload_failed=False
            if upload(os.path.join(CAPDIR, file), file):
                print('Upload of ' + os.path.join(CAPDIR, file) + ' successful!')
            else:
                print('Upload of ' + os.path.join(CAPDIR, file) + ' failed!')
                Upload_failed=True
    if not Upload_failed:
        print('All files uploaded successfully, cleaning up!')
        delete_netxml_temp(CAPDIR) # clean up the capture directory
    else:
        print('One or more files failed to upload, not cleaning up!')
else:
    print("API not available to upload, however we are restarting kismet to keep logs fresh.")
    Stop_kismet()


# Restart kismet
call(["systemctl", "start", "kismet.service"])
print("Done!")
