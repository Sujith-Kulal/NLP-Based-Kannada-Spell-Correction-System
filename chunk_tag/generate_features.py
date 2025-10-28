import sys
# from datasets import ClassLabel, load_dataset, load_metric, DownloadMode
from transformers import AutoModelForTokenClassification, AutoConfig, AutoTokenizer, TrainingArguments, Trainer, DataCollatorForTokenClassification, EarlyStoppingCallback, IntervalStrategy
import numpy as np
import torch
import pickle
import argparse

with open("chunk_encoding_dict.pickle","rb") as f:
	encoding_dict = pickle.load(f)

# Parse command-line arguments
parser = argparse.ArgumentParser(description="Token Classification")
parser.add_argument("--input", type=str, help="Input file path")
parser.add_argument("--output", type=str, help="Output file path")
parser.add_argument("--model", type=str, help="Model path")
args = parser.parse_args()

tokenizer_path = args.model
model_path = args.model

# Load the tokenizer from the saved folder
tokenizer = AutoTokenizer.from_pretrained(tokenizer_path)

# Load the model from the saved folder
model = AutoModelForTokenClassification.from_pretrained(model_path)

pos_data = []
sentence_data = []
pos_file = args.input

with open(pos_file,"r",encoding='utf-8') as f:
	data = f.readlines()

sent = []
tok = []
#print(f"len of data : {len(data)}")
for i in range(len(data)):
    #print(f"line -->{i}")
    if (data[i] != "\n") and ("<Sentence" not in data[i]) and ("</Sentence>" not in data[i]):
        pos = data[i].split("\t")[2].strip()
        token = data[i].split("\t")[1].strip()
        sent.append(pos)
        tok.append(token)
    elif data[i]=="\n" or i == (len(data)-1):
        pos_data.append(sent)
        sentence_data.append(tok)
        sent = []
        tok = []
#print(f"Len of sentence_data: {len(sentence_data)}")
def get_predictions( sentence, tokenizer, model ):
  # Let us first tokenize the sentence - split words into subwords
  tok_sentence = tokenizer(sentence, return_tensors='pt')
  #print(f"Tokenized sentence tensor size: {tok_sentence['input_ids'].size()}")

  with torch.no_grad():
    # we will send the tokenized sentence to the model to get predictions
    #print(sentence)
    logits = model(**tok_sentence).logits.argmax(-1)
    
    # We will map the maximum predicted class id with the class label
    predicted_tokens_classes = [model.config.id2label[t.item()] for t in logits[0]]
    
    #print(f"Predicted token class\n{predicted_tokens_classes}")
    
    predicted_labels = []
    
    previous_token_id = 0
    # we need to assign the named entity label to the head word and not the following sub-words
    word_ids = tok_sentence.word_ids()
    #print(f"Word IDs\n{word_ids}")
    for word_index in range(len(word_ids)):
        if word_ids[word_index] == None:
            previous_token_id = word_ids[word_index]
        elif word_ids[word_index] == previous_token_id:
            previous_token_id = word_ids[word_index]
        else:
            predicted_labels.append( predicted_tokens_classes[ word_index ] )
            previous_token_id = word_ids[word_index]
    
    return predicted_labels


predicted_chunk_tags = []
print(f"Len of pos tags:{len(pos_data)}")
print(f"Len of Sentence :{len(sentence_data)}")

print(sentence_data,pos_data)
for i in range(len(sentence_data)):
    d = sentence_data[i]
    sentence = " ".join(d)
    sentence = sentence.replace("\u200c","")
    

    predicted_labels = get_predictions(sentence=sentence, 
                                   tokenizer=tokenizer,
                                   model=model
                                   )
    chunk = []
    print(i,len(sentence.split(" ")),len(predicted_labels))

    for index in range(len(sentence.split(' '))):
        #print(f"Label : {predicted_labels[index]}")
        tag_id = int(predicted_labels[index].split("_")[1])
        tag = encoding_dict[tag_id]
        chunk.append(tag)
        
    predicted_chunk_tags.append(chunk)

outfile = args.output

with open(outfile,"w",encoding='utf-8') as outf:
    for i in range(len(sentence_data)):
        s = sentence_data[i]
        p = pos_data[i]
        c = predicted_chunk_tags[i]
        for j in range(len(s)):
            outf.write(f"{s[j]}\t{p[j]}\t{c[j]}\n")
        outf.write("\n")
