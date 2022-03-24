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
from utils.create_dataset import create_dataset_from_eaf

import PySimpleGUI as sg
import webbrowser


AUTH_TOKEN_FILE = os.path.join(os.path.expanduser("~"), ".cmulab_elan")
CMULAB_SERVER = "http://miami.lti.cs.cmu.edu:8088"


def ping_server(server_url):
    status_check = None
    try:
        status_check = requests.get(server_url.rstrip('/') + "/annotator")
    except:
        traceback.print_exc()
    return status_check


def get_server_url():
    server_url = CMULAB_SERVER
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


def browser_login(server_url):
    webbrowser.open(server_url + "/annotator/get_auth_token/")


def get_auth_token(server_url):
    if os.path.exists(AUTH_TOKEN_FILE):
        with open(AUTH_TOKEN_FILE) as fin:
            auth_token = fin.read().strip()
    else:
        # browser_login(server_url)
        layout = [[sg.Text('Click link below to get your access token')],
                  [sg.Text(server_url + "/annotator/get_auth_token/", text_color='blue', enable_events=True, key='-LINK-')],
                  [sg.Text("Please enter your access token here")], [sg.Input()], [sg.Button('OK')]]
        window = sg.Window('Authorization required!', layout, finalize=True)
        window['-LINK-'].set_cursor(cursor='hand1')
        while True:
            event, values = window.read()
            if event in (sg.WIN_CLOSED, 'Exit'):
                break
            elif event == '-LINK-':
                webbrowser.open(window['-LINK-'].DisplayText)
            auth_token = values[0].strip()
            if auth_token:
                break
        window.close()
    with open(AUTH_TOKEN_FILE, 'w') as fout:
        fout.write(auth_token)
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



def phone_transcription(server_url, auth_token, input_audio, annotations):
    layout = [[sg.Text("Language code"), sg.Input(default_text="eng", key='lang_code')],
              [sg.Text("Pretrained model"), sg.Input(default_text="eng2102", key='pretrained_model')],
              [sg.Button('OK')]]
    window = sg.Window('Allosaurus parameters', layout)
    event, values = window.read()
    lang_code = values["lang_code"].strip().lower()
    pretrained_model = values["pretrained_model"].strip().lower()
    window.close()

    with open(input_audio,'rb') as audio_file:
        files = {'file': audio_file}
        url = server_url + "/annotator/segment/1/annotate/2/"
        try:
            headers = {}
            if auth_token:
                headers["Authorization"] = auth_token
            allosaurus_params = {"lang": lang_code, "model": pretrained_model}
            r = requests.post(url, files=files, data={"segments": json.dumps(annotations), "params": json.dumps(allosaurus_params)}, headers=headers)
        except:
            err_msg = "Error connecting to CMULAB server " + server_url
            sys.stderr.write(err_msg + "\n")
            traceback.print_exc()
            sg.Popup(err_msg, title="ERROR")
            print('RESULT: FAILED.', flush = True)
            sys.exit(1)
        print("Response from CMULAB server " + server_url + ": " + r.text)
        if not r.ok:
            sg.Popup("Server error, click the report button to view logs.", title="ERROR")
            print('RESULT: FAILED.', flush = True)
            sys.exit(1)
        transcribed_annotations = json.loads(r.text)
        for annotation in transcribed_annotations:
            annotation["value"] = annotation["transcription"].replace(' ', '')
        return transcribed_annotations


def finetune_allosaurus(server_url, auth_token, input_audio, annotations):
    layout = [[sg.Text(err_msg + "\nPlease enter new CMULAB server URL")], [sg.Input()], [sg.Button('OK')]]
    window = sg.Window('CMULAB server URL', layout)
    event, values = window.read()
    server_url = values[0].strip().rstrip('/')
    window.close()


def speaker_diarization(server_url, auth_token, input_audio, annotations):
    if not annotations:
        sg.Popup("Please select an input tier containing a few sample annotations for each speaker", title="ERROR")
        print('RESULT: FAILED.', flush = True)
        sys.exit(1)
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
            r = requests.post(url, files=files,
                              data={"segments": json.dumps(annotations), "params": json.dumps(request_params)},
                              headers=headers)
        except:
            err_msg = "Error connecting to CMULAB server " + server_url
            sys.stderr.write(err_msg + "\n")
            traceback.print_exc()
            sg.Popup(err_msg, title="ERROR")
            print('RESULT: FAILED.', flush = True)
            sys.exit(1)
        print("Response from CMULAB server " + server_url + ": " + r.text)
        if not r.ok:
            sg.Popup("Server error, click the report button to view logs.", title="ERROR")
            print('RESULT: FAILED.', flush = True)
            sys.exit(1)
        response_data = json.loads(r.text)
        transcribed_annotations = []
        for item in response_data:
            transcribed_annotations.append({
                "start": item[1],
                "end": item[2],
                "value": item[0]
            })
        return transcribed_annotations


def write_output(output_tier_file, annotations):
    with open(output_tier_file, 'w', encoding = 'utf-8') as output_tier:
        # Write document header.
        output_tier.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        output_tier.write('<TIER xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" ' +
                          'xsi:noNamespaceSchemaLocation="file:avatech-tier.xsd" columns="Allosaurus">\n')
        for annotation in annotations:
            output_tier.write('    <span start="%s" end="%s"><v>%s</v></span>\n' %
                              (annotation['start'], annotation['end'], annotation['value']))
        output_tier.write('</TIER>\n')


def main():
    params = get_params()

    input_audio = params.get('source')
    input_tier = params.get('input_tier', 'none specified')
    output_tier = params.get('output_tier')
    cmulab_service = params.get('cmulab_service', 'Phone-transcription')
    print("input_tier: " + input_tier)
    print("cmulab_service: " + cmulab_service)

    server_url = get_server_url()

    auth_token = get_auth_token(server_url)

    print("PROGRESS: 0.1 Loading annotations from input tier", flush = True)
    annotations = get_input_annotations(input_tier)

    if cmulab_service == "Phone-transcription":
        output_annotations = phone_transcription(server_url, auth_token, input_audio, annotations)
    elif cmulab_service == "Finetune-allosaurus":
        output_annotations = finetune_allosaurus(server_url, auth_token, input_audio, annotations)
    elif cmulab_service == "Speaker-diarization":
        output_annotations = speaker_diarization(server_url, auth_token, input_audio, annotations)
    else:
        print("RESULT: FAILED. Not supported!", flush = True)
        sys.exit(1)

    print("PROGRESS: 0.95 Preparing output tier", flush = True)
    write_output(output_tier, output_annotations)
    print('RESULT: DONE.', flush = True)


if __name__ == '__main__':
    main()
