#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import atexit
import os
import os.path
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata
import time

import requests
import json
import traceback
from utils.create_dataset import create_dataset_from_eaf_files

import PySimpleGUI as sg
import webbrowser
from urllib.parse import urlparse


sg.theme("SystemDefaultForReal")

AUTH_TOKEN_FILE = os.path.join(os.path.expanduser("~"), ".cmulab_elan")


def show_error_and_exit(msg):
    sg.Popup(msg, title="ERROR")
    sys.stderr.write("ERROR: " + msg + "\n")
    print('RESULT: FAILED. ' + msg, flush = True)
    sys.exit(1)


def ping_server(server_url):
    status_check = None
    try:
        status_check = requests.get(server_url.rstrip('/') + "/annotator")
    except:
        traceback.print_exc()
    return status_check


def get_server_url(server_url):
    status_check = ping_server(server_url)
    while not status_check:
        err_msg = "Error connecting to CMULAB server " + server_url
        layout = [[sg.Text(err_msg + "\nPlease enter new CMULAB server URL")], [sg.Input()], [sg.Button('OK')]]
        window = sg.Window('CMULAB server URL', layout)
        event, values = window.read()
        server_url = values[0].strip().rstrip('/')
        if not server_url.startswith("http"):
            server_url = "http://" + server_url
        window.close()
        status_check = ping_server(server_url)
    return server_url


def get_params():
    # The parameters provided by the user via the ELAN recognizer interface
    # (specified in CMDI).
    params = {}
    # Read in all of the parameters that ELAN passes to this local recognizer on
    # standard input.
    for line in sys.stdin:
        match = re.search(r'<param name="(.*?)".*?>(.*?)</param>', line)
        if match:
            params[match.group(1)] = match.group(2).strip()
    return params


def check_auth_token(auth_token, server_url):
    try:
        headers = {"Authorization": auth_token.strip()}
        status_check = requests.get(server_url.rstrip('/') + "/annotator/check_auth_token/", headers=headers)
        return True if status_check else False
    except:
        traceback.print_exc()
        return False



def get_auth_token(server_url):
    netloc = urlparse(server_url).netloc
    auth_token = ""
    if os.path.exists(AUTH_TOKEN_FILE):
        # token file valid only if it was created within the last 1 hour
        if (time.time() - os.path.getmtime(AUTH_TOKEN_FILE)) < 3600:
            with open(AUTH_TOKEN_FILE) as fin:
                # format: netloc <TAB> auth_token
                columns = fin.readline().strip().split('\t')
                if len(columns) == 2 and columns[0].strip() == netloc:
                    auth_token = columns[1].strip()
                if not check_auth_token(auth_token, server_url):
                    auth_token = ""
    if not auth_token:
        layout = [[sg.Text('Click link below to get your access token')],
                  [sg.Text(server_url + "/annotator/get_auth_token/", text_color='blue', enable_events=True, key='-LINK-')],
                  [sg.Text("Please enter your access token here")], [sg.Input()], [sg.Button('OK')]]
        window = sg.Window('Authorization required!', layout, finalize=True)
        window['-LINK-'].set_cursor(cursor='hand1')
        while True:
            event, values = window.read()
            if event in (sg.WIN_CLOSED, 'Exit'):
                sys.exit(1)
            elif event == '-LINK-':
                webbrowser.open(window['-LINK-'].DisplayText, new=1)
            auth_token = values[0].strip()
            if auth_token and check_auth_token(auth_token, server_url):
                break
        window.close()
        with open(AUTH_TOKEN_FILE, 'w') as fout:
            fout.write(netloc + '\t' + auth_token)
    return auth_token


def get_input_annotations(input_tier):
    # grab the 'input_tier' parameter, open that
    # XML document, and read in all of the annotation start times, end times,
    # and values.
    # Note: Tiers for the recognizers are in the AVATech tier format, not EAF
    annotations = []
    if os.path.exists(input_tier):
        with open(input_tier, 'r', encoding = 'utf-8') as input_tier_file:
            for line in input_tier_file:
                match = re.search(r'<span start="(.*?)" end="(.*?)"><v>(.*?)</v>', line)
                if match:
                    annotation = { \
                        'start': int(float(match.group(1)) * 1000.0), \
                        'end' : int(float(match.group(2)) * 1000.0), \
                        'value' : match.group(3) }
                    annotations.append(annotation)
    return annotations



def phone_transcription(server_url, auth_token, input_audio, annotations, output_tier):
    layout = [[sg.Text("Language code"), sg.Input(default_text="eng", key='lang_code')],
              [sg.Text("Pretrained model"), sg.Input(default_text="uni2005", key='pretrained_model')],
              [sg.Text('Click link below to view available models and languages:')],
              [sg.Text(server_url + "/annotator/get_allosaurus_models/", text_color='blue', enable_events=True, key='-LINK-')],
              [sg.OK()]]
    window = sg.Window('Allosaurus parameters', layout)
    while True:
        event, values = window.read()
        if event in (sg.WIN_CLOSED, 'Exit'):
            sys.exit(1)
        elif event == '-LINK-':
            webbrowser.open(window['-LINK-'].DisplayText, new=1)
        elif event == 'OK':
            lang_code = values["lang_code"].strip().lower()
            pretrained_model = values["pretrained_model"].strip().lower()
            break
    window.close()

    with open(input_audio,'rb') as audio_file:
        files = {'file': audio_file}
        url = server_url + "/annotator/segment/1/annotate/2/"
        try:
            headers = {}
            if auth_token:
                headers["Authorization"] = auth_token
            allosaurus_params = {"service": "phone_transcription", "lang": lang_code, "model": pretrained_model}
            print("PROGRESS: 0.5 Waiting for response from server", flush = True)
            r = requests.post(url, files=files, data={"segments": json.dumps(annotations), "params": json.dumps(allosaurus_params)}, headers=headers)
        except:
            traceback.print_exc()
            show_error_and_exit("Error connecting to CMULAB server " + server_url)
        print("Response from CMULAB server " + server_url + ": " + r.text)
        if not r.ok:
            show_error_and_exit("Server error. Status code: " + str(r.status_code))
        transcribed_annotations = json.loads(r.text)
        for annotation in transcribed_annotations:
            annotation["value"] = annotation["transcription"].replace(' ', '')
        write_output(output_tier, transcribed_annotations, "Allosaurus")


def finetune_allosaurus(server_url, auth_token, input_audio, annotations, output_tier):
    layout = [[sg.Text('List of available models and languages:')],
              [sg.Text(server_url + "/annotator/get_allosaurus_models/", text_color='blue', enable_events=True, key='-LINK-')],
              [sg.Text("Language code"), sg.Input(default_text="eng", key='lang_code')],
              [sg.Text("Pretrained model"), sg.Input(default_text="uni2005", key='pretrained_model')],
              [sg.Text("Number of training epochs"), sg.Slider((0, 10), orientation='h', resolution=1, default_value=2, key='nepochs')],
              [sg.Text("Select EAF files containing phone transcriptions for fine-tuning")],
              [sg.LBox([], size=(100,10), key='-FILESLB-')],
              [sg.Input(visible=False, enable_events=True, key='-IN-'), sg.FilesBrowse(file_types=(("EAF files", "*.eaf"),)), sg.Button('Clear')],
              [sg.Text("Tier name (leave blank to use all tiers)"), sg.Input(key='tier_name')],
              [sg.Text("Annotator (leave blank to use all tiers)"), sg.Input(key='annotator')],
              [sg.Button('Go'), sg.Button('Exit')]]

    window = sg.Window('Finetune Allosaurus', layout)

    eaf_files = []
    while True:             # Event Loop
        event, values = window.read()
        # When choice has been made, then fill in the listbox with the choices
        if event == '-IN-':
            eaf_files = values['-IN-'].split(';')
            window['-FILESLB-'].Update(eaf_files)
        if event == 'Clear':
            eaf_files = []
            window['-FILESLB-'].Update([])
        if event == '-LINK-':
            webbrowser.open(window['-LINK-'].DisplayText, new=1)
        if event == 'Go':
            lang_code = values["lang_code"].strip().lower()
            pretrained_model = values["pretrained_model"].strip().lower()
            tier_name = values["tier_name"].strip()
            annotator = values["annotator"].strip()
            nepochs = int(values["nepochs"])
            break
        if event in (sg.WIN_CLOSED, 'Exit'):
            sys.exit(1)
    window.close()
    print(' '.join([lang_code, pretrained_model, tier_name, annotator]))
    print('\n'.join(eaf_files))

    if not eaf_files:
        show_error_and_exit("No EAF files selected for finetuning!")
    if lang_code == "ipa":
        show_error_and_exit("'ipa' lang code is not supported by allosaurus for fine-tuning!")
    print("PROGRESS: 0.1 Generating dataset...", flush = True)
    tmpdirname = tempfile.TemporaryDirectory()
    print('creating temporary directory', tmpdirname)
    dataset_dir = os.path.join(tmpdirname.name, "dataset")
    train_dir = os.path.join(dataset_dir, "train")
    validate_dir = os.path.join(dataset_dir, "validate")

    tier_names = [t.strip() for t in tier_name.split(',') if t.strip()]
    annotators = [a.strip() for a in annotator.split(',') if a.strip()]
    result = create_dataset_from_eaf_files(eaf_files, train_dir, tier_names, annotators)
    if not result:
        show_error_and_exit("Couldn't create dataset for fine-tuning. Please check the selected EAF files.")
    # shutil.copytree(train_dir, validate_dir)
    dataset_archive = shutil.make_archive(dataset_dir, 'zip', dataset_dir)
    # shutil.copytree(tmpdirname.name, tmpdirname.name + "_copy")
    print("PROGRESS: 0.5 Fine-tuning allosaurus...", flush = True)
    print(dataset_archive)
    with open(dataset_archive,'rb') as zip_file:
        files = {'file': zip_file}
        url = server_url + "/annotator/segment/1/annotate/4/"
        try:
            allosaurus_params = {"service": "batch_finetune", "lang": lang_code, "epoch": nepochs, "pretrained_model": pretrained_model}
            headers = {}
            if auth_token:
                headers["Authorization"] = auth_token.strip()
                print("Auth token: " + auth_token)
            print("PROGRESS: 0.5 Waiting for response from server", flush = True)
            r = requests.post(url, files=files, data={"params": json.dumps(allosaurus_params)}, headers=headers)
        except:
            traceback.print_exc()
            show_error_and_exit("Error connecting to CMULAB server " + server_url)
        print("Response from CMULAB server " + server_url + ": " + r.text)
        if not r.ok:
            show_error_and_exit("Server error. Status code: " + str(r.status_code))
        json_response = json.loads(r.text)
        model_id = json_response[0]["new_model_id"]
        print("New model ID:")
        print(model_id)
        # sg.Popup("Allosaurus fine-tuning finished successfully! Please click the 'Report' button to view logs and the new model ID")
        webbrowser.open(server_url + json_response[0]["status_url"], new=1)
        webbrowser.open(server_url + "/annotator/models")
        print("Please visit " + json_response[0]["models_url"] + " to see list of all fine-tuned models.")
        time.sleep(2)



def speaker_diarization(server_url, auth_token, input_audio, annotations, output_tier):
    if not annotations:
        show_error_and_exit("In the parameters section, please choose an input tier containing a few speaker annotations.\n"
                            "The model will learn from these example annotations and annotate the rest of the audio.")
    layout = [[sg.Text("Threshold"), sg.Slider((0, 1), orientation='h', resolution=0.01, default_value=0.45)],
              [sg.Button('OK')]]
    window = sg.Window('Diarization parameters', layout)
    event, values = window.read()
    threshold = float(values[0])
    window.close()
    print("PROGRESS: 0.5 Running speaker diarization...", flush = True)
    with open(input_audio,'rb') as audio_file:
        files = {'file': audio_file}
        url = server_url + "/annotator/segment/1/annotate/2/"
        try:
            headers = {}
            if auth_token:
                headers["Authorization"] = auth_token
            request_params = {"service": "diarization", "threshold": threshold}
            print(url)
            print(input_audio)
            print(json.dumps(annotations, indent=4))
            print(json.dumps(request_params, indent=4))
            print(json.dumps(headers, indent=4))
            print("PROGRESS: 0.5 Waiting for response from server", flush = True)
            r = requests.post(url, files=files,
                              data={"segments": json.dumps(annotations), "params": json.dumps(request_params)},
                              headers=headers)
        except:
            traceback.print_exc()
            show_error_and_exit("Error connecting to CMULAB server " + server_url)
        print("Response from CMULAB server " + server_url + ": " + r.text)
        if not r.ok:
            show_error_and_exit("Server error. Status code: " + str(r.status_code))
        response_data = json.loads(r.text)
        transcribed_annotations = []
        for item in response_data:
            transcribed_annotations.append({
                "start": item[1],
                "end": item[2],
                "value": item[0]
            })
        write_output(output_tier, transcribed_annotations, "Speaker-diarization")


def write_output(output_tier_file, annotations, tier_name):
    print("PROGRESS: 0.95 Preparing output tier", flush = True)
    with open(output_tier_file, 'w', encoding = 'utf-8') as output_tier:
        # Write document header.
        output_tier.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        output_tier.write('<TIER xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" ' +
                          'xsi:noNamespaceSchemaLocation="file:avatech-tier.xsd" columns="' + tier_name + '">\n')
        for annotation in annotations:
            output_tier.write('    <span start="%s" end="%s"><v>%s</v></span>\n' %
                              (annotation['start'], annotation['end'], annotation['value']))
        output_tier.write('</TIER>\n')


def main():
    print("PROGRESS: 0.1 Reading parameters", flush = True)
    params = get_params()

    input_audio = params.get('source')
    input_tier = params.get('input_tier', 'none specified')
    output_tier = params.get('output_tier')
    cmulab_service = params.get('cmulab_service', 'run-phone-transcription')
    print("input_tier: " + input_tier)
    print("cmulab_service: " + cmulab_service)

    server_url = params.get("server_url", "http://localhost:8088").strip().rstrip('/')
    print("PROGRESS: 0.2 Connecting to CMULAB server", flush = True)
    server_url = get_server_url(server_url)

    print("PROGRESS: 0.3 Getting authorization token", flush = True)
    auth_token = get_auth_token(server_url)

    print("PROGRESS: 0.4 Loading annotations from input tier", flush = True)
    annotations = get_input_annotations(input_tier)

    if cmulab_service == "run-phone-transcription":
        phone_transcription(server_url, auth_token, input_audio, annotations, output_tier)
    elif cmulab_service == "train-phone-transcription":
        finetune_allosaurus(server_url, auth_token, input_audio, annotations, output_tier)
    elif cmulab_service == "run-speaker-diarization":
        speaker_diarization(server_url, auth_token, input_audio, annotations, output_tier)
    else:
        print("RESULT: FAILED. Not supported!", flush = True)
        sys.exit(1)

    print('RESULT: DONE.', flush = True)


if __name__ == '__main__':
    main()
