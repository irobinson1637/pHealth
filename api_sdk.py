# from google.cloud import storage
import requests
import time
import matplotlib.pyplot as plt
import numpy as np
import wave
import os
import sys
from IPython.core.display import HTML
# import interactiveVis
import getpass
import boto3
import json

def submit_text(text, functions, user_name="", password=""):
    url = "https://api-v1.bartleby.predictionhealth.com/processAudio"
    myobj = {
        "text": text,
        "functions" : functions
    }
    if user_name == "":
        user_name = input("Enter username: ")
    if password == "":
        password = getpass.getpass("Enter password: ")
    return requests.post(url, json = myobj, auth=(user_name, password)).text

def submit_uri(uri, functions, user_name="", password=""):
    #url = "http://localhost:8080/processAudio"
    url = "https://api-v1.bartleby.predictionhealth.com/processAudio"
    myobj = {
        "uri": uri,
        "functions" : functions
    }
    if user_name == "":
        user_name = input("Enter username: ")
    if password == "":
        password = getpass.getpass("Enter password: ")
    return requests.post(url, json = myobj, auth=(user_name, password)).text

def submit_uris(uris, functions, user_name, password):
    #url = "http://localhost:8080/processAudio"
    url = "https://api-v1.bartleby.predictionhealth.com/processAudio"
    myobj = {
        "uris": uris,
        "functions" : functions
    }
    if user_name == "":
        user_name = input("Enter username: ")
    if password == "":
        password = getpass.getpass("Enter password: ")
    return requests.post(url, json = myobj, auth=(user_name, password)).text


def check_job(job_num, user_name="", password=""):
    #url = "http://localhost:8080/checkStatus"
    url = "https://api-v1.bartleby.predictionhealth.com/checkStatus"
    myobj = {
        "id": job_num,
    }
    if user_name == "":
        user_name = input("Enter username: ")
    if password == "":
        password = getpass.getpass("Enter password: ")
    return requests.post(url, json = myobj, auth=(user_name, password)).json()

def run_text_job(uri, functions, visu_functions=None):
    user_name = input("Enter username: ")
    password = getpass.getpass("Enter password: ")

    job_num = submit_text(uri, functions, user_name, password)
    print("job id is " + str(job_num))
    response = check_job(job_num, user_name, password)

    while response["status"] != "Completed":
        response = check_job(job_num, user_name, password)
        time.sleep(.1)

    if visu_functions is None:
        return response
    #interactiveVis.visualize_encounter(response, "PT", visu_functions)
    interactiveVis.visualize_encounter_interactive(response, 'PT', visu_functions)
    return response

def run_uris_job(uris, functions, visu_functions=None):

    new_arr = []
    for uri in uris:
        to_add = {"uri" : uri}
        new_arr.append(to_add)

    user_name = input("Enter username: ")
    password = getpass.getpass("Enter password: ")

    job_num = submit_uris(new_arr, functions, user_name, password)
    print("job id is " + str(job_num))
    response = check_job(job_num, user_name, password)

    if len(uris) > 0 and uris[0] == "gs://ph-test-storage-audio/demo.wav" or uris[0] == "s3://ph-audio-files/demo.wav":
        display_waveform("./demo.wav")
        wavPlayer("./demo.wav")

    while response["status"] != "Completed":
        response = check_job(job_num, user_name, password)
        time.sleep(.1)

    ### Temporary Fix For SpeakerTag
    for sent in response['sentences']:
        for token in sent['tokens']:
            token['speakerTag'] = "clinician" if token['speakerTag'] == "patient" else "patient"
            
            
    if visu_functions is None:
        return response
    #interactiveVis.visualize_encounter(response, "PT", visu_functions)
    interactiveVis.visualize_encounter_interactive(response, 'PT', visu_functions)
    return response

def run_uri_job(uri, functions, visu_functions=None):
    user_name = input("Enter username: ")
    password = getpass.getpass("Enter password: ")

    job_num = submit_uri(uri, functions, user_name, password)
    print("job id is " + str(job_num))
    response = check_job(job_num, user_name, password)

    if uri == "gs://ph-test-storage-audio/demo.wav" or uri == "s3://ph-audio-files/demo.wav" :
        display_waveform("./demo.wav")
        wavPlayer("./demo.wav")

    while response["status"] != "Completed":
        response = check_job(job_num, user_name, password)
        time.sleep(.1)

    if visu_functions is None:
        return response
    #interactiveVis.visualize_encounter(response, "PT", visu_functions)
    interactiveVis.visualize_encounter_interactive(response, 'PT', visu_functions)
    return response

def upload_blob_aws(bucket_name, source_file_name):
    BUCKET_NAME = bucket_name
    KEY = source_file_name

    s3 = boto3.client('s3')
    s3.upload_file(source_file_name, BUCKET_NAME, KEY)

def upload_wav_file(bucket_name, source_file_name):
    """Uploads a file to the bucket."""
    destination_blob_name = source_file_name

    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    blob.upload_from_filename(source_file_name)

def display_waveform(file_name):

    spf = wave.open(file_name, "r")

    # Extract Raw Audio from Wav File
    signal = spf.readframes(-1)
    signal = np.fromstring(signal, "Int16")
    fs = spf.getframerate()
    plt.ylabel("Amplitude")

    Time = np.linspace(0, len(signal) / (fs * 60), num=len(signal))
    if Time[-1] < 1:
        plt.xlabel("Seconds")
        Time = np.linspace(0, len(signal) / (fs), num=len(signal))
    else:
        plt.xlabel("Minutes")
    plt.figure(1)
    plt.title("Audio Waveform")
    plt.plot(Time, signal)
    plt.show()

def pull_and_visualize(visu_functions=None):
    json_file = open("example_data.json", "r")
    response = json.load(json_file)
    json_file.close()

    if "uri" in response and response["uri"] == "s3://test-transcribe-bartleby/demo.wav":
        display_waveform("./demo.wav")
        wavPlayer("./demo.wav")
    elif "uris" in response and len(response["uris"]) > 0 and response["uris"][0] == "s3://test-transcribe-bartleby/demo.wav":
        display_waveform("./demo.wav")
        wavPlayer("./demo.wav")

    if visu_functions is None:
        return response
    #interactiveVis.visualize_encounter(response, "PT", visu_functions)
    interactiveVis.visualize_encounter_interactive(response, 'PT', visu_functions)
    return response

def upload_and_submit(recorder, functions, visu_functions=None):
    recorder.save("my_recording")
    #os.system("rm my_recording.wav")
    os.system("ffmpeg -i my_recording.webm my_recording_temp.wav")
    os.system("sox my_recording_temp.wav -r 44100 -c 1 my_recording.wav")
    os.remove("my_recording_temp.wav")
    os.remove("my_recording.webm")
    #upload_wav_file("ph-test-storage-audio", "my_recording.wav")
    upload_blob_aws("ph-audio-files", "my_recording.wav")
    display_waveform("my_recording.wav")
    run_uri_job("s3://ph-audio-files/my_recording.wav", functions, visu_functions)
    #return "my_recording.wav"

def wavPlayer(filepath):
    """ will display html 5 player for compatible browser

    Parameters :
    ------------
    filepath : relative filepath with respect to the notebook directory ( where the .ipynb are not cwd)
               of the file to play

    The browser need to know how to play wav through html5.

    there is no autoplay to prevent file playing when the browser opens
    """

    src = """
    <head>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
    <title>Simple Test</title>
    </head>

    <body>
    <audio controls="controls" style="width:600px" >
      <source src="files/%s" type="audio/wav" />
      Your browser does not support the audio element.
    </audio>
    </body>
    """%(filepath)
    display(HTML(src))

def print_conversation(job):
    sents = job["sentences"]
    curr_speaker = None
    for sent in sents:
        tokens = sent["tokens"]
        for token in tokens:
            new_speaker = token["speakerTag"]
            if new_speaker != curr_speaker:
                print("\n")
                print("Speaker " + new_speaker)
                print()
                curr_speaker = new_speaker
            if token["isPunctuation"]:
                print(token["originalString"], end="")
            else:
                print(" " + token["originalString"], end="")
