import argparse
import json
import requests
import re
from utils import write_to_json

def get_args():
    '''
    This function parses and return arguments passed in
    '''
    parser = argparse.ArgumentParser(prog='token_classifier_batch.py',
                                     description='Token FLASK BERT Classififer Application ')
    parser.add_argument('--data', help="Serialized json string")
    parser.add_argument('--out_dir', help="output folder")
    args = parser.parse_args()

    return(args)

def request(sentences):
    r = requests.post(url = "http://localhost:4998/queries", json={'sentences':sentences})
    return json.loads(r.text)

if __name__ == "__main__":
    args = get_args()
    jsons = eval(re.sub(r"\[QUOTE\]", r"'", args.data))

    rtext = request(str([data["sentences"] for data in jsons]))
    all_tokens = rtext["tokens"]
    all_token_labels = rtext["output"]

    output_data = list()
    for i,data in enumerate(jsons):
        data["tokens"] = all_tokens[i]
        data["token_labels"] = all_token_labels[i]
        write_to_json(data, data["id"], extension="json", out_dir=args.out_dir)
