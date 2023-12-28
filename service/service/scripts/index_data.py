from pathlib import Path
import argparse
import requests
import tempfile
import os

def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--file', help='Specify a file name', required=True)
    args = parser.parse_args()
    return args


if __name__ == "__main__":
    args = parse_arguments()
    filename = args.file
    if not filename:
        filename = "data/tana_dump.json"

    print("Sending data to Tana Helper Mistral Preload API...")

    # throw Tana json export at the topic dumper API
    url = "http://localhost:8000/mistral/preload"

    headers = {'Content-type': 'application/json'}
    with open(filename, 'rb') as f:
        response = requests.post(url, data=f, headers=headers)

    if response.status_code != 200:
        print("Error sending data to preload API:")
        print(response.text)
        exit(1)

    # query the index to test liveness
    url = "http://localhost:8000/mistral/preload"
    question = { 'query': "What do you know about Tana?"}
    print(question)
    response = requests.post(url, data=question, headers=headers)
    print(response)
