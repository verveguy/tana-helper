import json
from pathlib import Path
import argparse
import requests
import tempfile
import os

def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--file', help='Specify a file name', required=True)
    parser.add_argument('-m', '--model', help='Specify a model name', required=False)
    args = parser.parse_args()
    return args


if __name__ == "__main__":
    args = parse_arguments()
    filename = args.file
    if not filename:
        filename = "data/tana_dump.json"

    model = args.model
    if not model:
        model = "openai"

    print("Sending data to Tana Helper Preload API...")

    # throw Tana json export at the topic dumper API
    url = f"http://localhost:8000/llamaindex/preload?model={model}"

    headers = {'Content-type': 'application/json'}
    with open(filename, 'rb') as f:
        response = requests.post(url, data=f, headers=headers)

    if response.status_code != 204:
        print("Error sending data to preload API:")
        print(response.text)
        exit(1)

    print("Testing /llamaindex/ask endpoint ...")

    # query the index to test liveness
    url = f"http://localhost:8000/llamaindex/ask?model={model}"
    question = { "query": "What do you know about Tana?"}
    print(question)
    response = requests.post(url, json=question, headers=headers)
    print(response.text)
