import os
import numpy
from pathlib import Path
import torch
from pytorch_pretrained_bert.tokenization import BertTokenizer
from pytorch_pretrained_bert.modeling import BertForTokenClassification
from nltk import word_tokenize

# Import the framework
from flask import Flask, g
from flask_restful import Resource, Api, reqparse
# Create an instance of Flask
app = Flask(__name__)

# Create the API
api = Api(app)

PYTORCH_PRETRAINED_BERT_CACHE = Path(os.getenv('PYTORCH_PRETRAINED_BERT_CACHE',
                                               Path.home() / '.pytorch_pretrained_bert'))

@app.route("/")
def index():
    # Open the README file
    #with open(os.path.dirname(app.root_path) + '/README.md', 'r') as markdown_file:
    # Read the content of the file
    #content = str("\n ".join(main(file)))

    # Convert to HTML
    if classifer is not None :
        # return markdown.markdown("classifier is loaded")
        return "<html><body><p>classifier is loaded</p></body></html>"
    else :
        return "<html><body><p>classifier is not loaded</p></body></html>"
        # return markdown.markdown("classifier is not loaded")

def prepare_input(lines):
    # examples = []
    words = []
    for (i, line) in enumerate(lines):
        line = line.strip()
        if line == "SAMPLE_START":
            words.append("[CLS]")
        elif line == "[SEP]":
            continue
        elif line == "":
            tokens = []
            for (j, word) in enumerate(words):
                if word == "[CLS]":
                    tokens.append("[CLS]")
                    continue

                tokenized = tokenizer.tokenize(word)
                if tokenized:
                    tokens.append(tokenized[0])
                else:
                    tokens.append("[UNK]")


            if len(tokens) > max_seq_length - 1:
                tokens = tokens[0:(max_seq_length - 1)]

            tokens.append("[SEP]") # For BERT
            tokens = tokenizer.convert_tokens_to_ids(tokens)

            segment_ids = [0] * len(tokens)
            input_mask = [1] * len(tokens)

            while len(tokens) < max_seq_length:
                tokens.append(0)
                segment_ids.append(0)
                input_mask.append(0)

            # examples.append((tokens, input_mask, segment_ids))
            words = []
            continue
        elif line in ["\x91", "\x92", "\x97"]:
            continue
        else:
            words.append(line)

    return tokens, input_mask, segment_ids

def predict(tokens):
    input_ids, input_mask, segment_ids = prepare_input(tokens)

    org_input_mask = input_mask
    org_input_mask = [x for x in org_input_mask if x != 0]

    input_ids = torch.tensor(input_ids, dtype=torch.long).unsqueeze(0).to(device)
    input_mask = torch.tensor(input_mask, dtype=torch.long).unsqueeze(0).to(device)
    segment_ids = torch.tensor(segment_ids, dtype=torch.long).unsqueeze(0).to(device)

    logits = model(input_ids, segment_ids, input_mask)
    logits = logits.detach().cpu().numpy()
    labels = numpy.argmax(logits, axis=-1).reshape(-1)

    labels = labels[0:len(org_input_mask)]

    all_labels = []
    j = 0
    count = 0
    for (i, line) in enumerate(tokens):
        line = line.strip()
        if line == "SAMPLE_START":
            count += 1
            all_labels.append("O")
            j += 1
        elif line == "[SEP]":
            all_labels.append("O")
        elif line == "\x91":
            all_labels.append("O")
        elif line == "\x92":
            all_labels.append("O")
        elif line == "\x97":
            all_labels.append("O")
        elif line == "": # We only have one sample, so doesn't actually matter
            count = 0
            j += 1 # We have a SEP at the end for BERT
        else:
            count += 1
            if count < max_seq_length:
                all_labels.append(label_map[labels[j]])
                j += 1
            else: # if we cut sequences longer than max_seq_length
                all_labels.append("O")

    all_labels.append("O") # for "" at the end
    return all_labels

class queryList(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('sentences', required=False, type=str, action='append', default=[])
        parser.add_argument('output', required=False)
        args = parser.parse_args()

        tokens = ["SAMPLE_START"]
        for sentence in args["sentences"]:
            words = word_tokenize(sentence)
            tokens.extend(words)
            tokens.append("[SEP]")

        tokens.pop() # Pop last [SEP]
        tokens.append("")
        args["tokens"] = tokens
        output = predict(tokens)
        args["output"] = output

        return args, 201


max_seq_length = 512

model_path = "/scratch/users/omutlu/.pytorch_pretrained_bert/token_model.pt"
bert_model = "/scratch/users/omutlu/.pytorch_pretrained_bert/bert-base-uncased.tar.gz"
bert_vocab = "/scratch/users/omutlu/.pytorch_pretrained_bert/bert-base-uncased-vocab.txt"

device = torch.device("cuda:3" if torch.cuda.is_available() else "cpu")
tokenizer = BertTokenizer.from_pretrained(bert_vocab)
label_list = ["B-etime", "B-fname", "B-organizer", "B-participant", "B-place", "B-target", "B-trigger", "I-etime", "I-fname", "I-organizer", "I-participant", "I-place", "I-target", "I-trigger", "O"]
label_map = {}
for (i, label) in enumerate(label_list):
    label_map[i] = label

model = BertForTokenClassification.from_pretrained(bert_model, PYTORCH_PRETRAINED_BERT_CACHE, num_labels=len(label_list))

if torch.cuda.is_available():
    model.load_state_dict(torch.load(model_path))
else:
    model.load_state_dict(torch.load(model_path, map_location='cpu'))

model.to(device)

api.add_resource(queryList, '/queries')
app.run(host='0.0.0.0', port=4998, debug=True)
