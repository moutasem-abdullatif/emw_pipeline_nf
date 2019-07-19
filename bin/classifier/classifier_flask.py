#!/usr/bin/env python3
import os
import shelve
from nltk import sent_tokenize
import numpy
from pathlib import Path
import torch
from pytorch_pretrained_bert.tokenization import BertTokenizer
from pytorch_pretrained_bert.modeling import BertForSequenceClassification

# Import the framework
from flask import Flask, g
from flask_restful import Resource, Api, reqparse
# Create an instance of Flask
app = Flask(__name__)

# Create the API
api = Api(app)

PYTORCH_PRETRAINED_BERT_CACHE = Path(os.getenv('PYTORCH_PRETRAINED_BERT_CACHE',
                                               Path.home() / '.pytorch_pretrained_bert'))

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = shelve.open("classifier.db")
    return db

@app.teardown_appcontext
def teardown_db(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

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

# def predict (input):
#    return  classifer.predict([input])[0]

def convert_text_to_features(text, label_list, max_seq_length, tokenizer):
    label_map = {}
    for (i, label) in enumerate(label_list):
        label_map[label] = i

    tokens_a = tokenizer.tokenize(text)
    if len(tokens_a) > max_seq_length - 2:
        tokens_a = tokens_a[0:(max_seq_length - 2)]

    tokens = []
    segment_ids = []
    tokens.append("[CLS]")
    segment_ids.append(0)

    for token in tokens_a:
        tokens.append(token)
        segment_ids.append(0)

    tokens.append("[SEP]")
    segment_ids.append(0)

    input_ids = tokenizer.convert_tokens_to_ids(tokens)
    input_mask = [1] * len(input_ids)

    while len(input_ids) < max_seq_length:
        input_ids.append(0)
        input_mask.append(0)
        segment_ids.append(0)

    assert len(input_ids) == max_seq_length
    assert len(input_mask) == max_seq_length
    assert len(segment_ids) == max_seq_length

    return input_ids, input_mask, segment_ids

def predict(text):
    input_ids, input_mask, segment_ids = convert_text_to_features(text, label_list, max_seq_length, tokenizer)
    input_ids = torch.tensor(input_ids, dtype=torch.long).unsqueeze(0).to(device)
    input_mask = torch.tensor(input_mask, dtype=torch.long).unsqueeze(0).to(device)
    segment_ids = torch.tensor(segment_ids, dtype=torch.long).unsqueeze(0).to(device)

    logits = model(input_ids, segment_ids, input_mask)
    logits = logits.detach().cpu().numpy()
    labels = numpy.argmax(logits, axis=1)

    return int(labels[0])

class queryList(Resource):
    def get(self):
        shelf = get_db()
        keys = list(shelf.keys())

        queries = []

        for key in keys:
            queries.append(shelf[key])

        return  queries, 200

    def post(self):
        parser = reqparse.RequestParser()

        parser.add_argument('identifier', required=True)
        parser.add_argument('text', required=True)
        parser.add_argument('output', required=False)
        parser.add_argument('event_sentences', required=False)
        # Parse the arguments into an object
        args = parser.parse_args()
        output = predict(args['text'])
        shelf = get_db()
        shelf[args['identifier']] = args
        args["output"] = str(output)
        if args["output"] == "1":
            args["event_sentences"] = sent_tokenize(args['text'])
        #return {'message': 'Query registered', 'data': args,'output':a_str }, 201
        return args, 201


class Device(Resource):
    def get(self, identifier):
        shelf = get_db()

        # If the key does not exist in the data store, return a 404 error.
        if not (identifier in shelf):
            return {'message': 'Device not found', 'data': {}}, 404

        return {'message': 'Device found', 'data': shelf[identifier]}, 200

    def delete(self, identifier):
        shelf = get_db()

        # If the key does not exist in the data store, return a 404 error.
        if not (identifier in shelf):
            return {'message': 'Device not found', 'data': {}}, 404

        del shelf[identifier]
        return '', 204


# file = '/emw_pipeline_nf/bin/classifier/20180919_protest_classifier-Matthews-70onTest29onChina.pickle'
# global classifer
# with open(file,"rb") as f :
#     classifer= pickle.load(f)

label_list = ["0", "1"]
max_seq_length = 256
bert_model = "/.pytorch_pretrained_bert/bert-base-uncased.tar.gz"
bert_vocab = "/.pytorch_pretrained_bert/bert-base-uncased-vocab.txt"
model_path = "/.pytorch_pretrained_bert/doc_model.pt"
num_labels = len(label_list)
#device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
device = "cpu"

tokenizer = BertTokenizer.from_pretrained(bert_vocab)
model = BertForSequenceClassification.from_pretrained(bert_model, PYTORCH_PRETRAINED_BERT_CACHE, num_labels=num_labels)
if device == "cpu":
    model.load_state_dict(torch.load(model_path, map_location='cpu'))
else:
    model.load_state_dict(torch.load(model_path))

model.to(device)

api.add_resource(queryList, '/queries')
api.add_resource(Device, '/query/<string:identifier>')
app.run(host='0.0.0.0', port=5000, debug=True)
