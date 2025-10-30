import sys
import os
import tempfile
import subprocess
# from datasets import ClassLabel, load_dataset, load_metric, DownloadMode
from transformers import AutoModelForTokenClassification, AutoConfig, AutoTokenizer, TrainingArguments, Trainer, DataCollatorForTokenClassification, EarlyStoppingCallback, IntervalStrategy
import numpy as np
import torch
import pickle
import argparse


def _ensure_gdown():
    try:
        import gdown  # noqa: F401
        return True
    except Exception:
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "gdown"], check=True)
            import gdown  # noqa: F401
            return True
        except Exception:
            return False


def _download_drive_path(url_or_id, dest_dir):
    if not _ensure_gdown():
        raise RuntimeError("gdown is required to download from Google Drive. Please install it: pip install gdown")

    if 'drive.google.com' in url_or_id and '/folders/' in url_or_id:
        cmd = ["gdown", "--folder", url_or_id, "-O", dest_dir]
        subprocess.run(cmd, check=True)
        return dest_dir
    else:
        cmd = ["gdown", url_or_id, "-O", dest_dir]
        subprocess.run(cmd, check=True)
        # return the downloaded file or directory
        for root, _, files in os.walk(dest_dir):
            for fn in files:
                return os.path.join(root, fn)
        return dest_dir


def _is_drive_url(s):
    return isinstance(s, str) and 'drive.google.com' in s


def _prepare_path(path_arg, expect_dir=False):
    """If path_arg is a local path return it, otherwise if it's a Drive URL download to a temp dir and return local path.

    If expect_dir is True, for Drive folders return the downloaded folder path; otherwise return a file path when possible.
    """
    if os.path.exists(path_arg):
        return path_arg
    if _is_drive_url(path_arg):
        tmp = tempfile.mkdtemp(prefix='run_pos_')
        downloaded = _download_drive_path(path_arg, tmp)
        # If folder was downloaded and expect_dir True, return the folder
        if expect_dir and os.path.isdir(downloaded):
            return downloaded
        # If a folder was downloaded but expect_dir False, try to find a sensible file
        if os.path.isdir(downloaded):
            # try to find model folder (contains config.json or pytorch_model.bin) or first .txt/.conll
            for root, dirs, files in os.walk(downloaded):
                if 'config.json' in files or 'pytorch_model.bin' in files:
                    return root
            for root, _, files in os.walk(downloaded):
                for fn in files:
                    if fn.lower().endswith(('.txt', '.conll', '.xml')):
                        return os.path.join(root, fn)
            return downloaded
        return downloaded
    raise FileNotFoundError(f"Path not found and not a Drive URL: {path_arg}")


# Parse command-line arguments
parser = argparse.ArgumentParser(description="Token Classification")
parser.add_argument("--input", type=str, help="Input file path")
parser.add_argument("--output", type=str, help="Output file path")
parser.add_argument("--model", type=str, help="Model path")
#parser.add_argument("--path", type=str, help="path")
args = parser.parse_args()

#dict_path = args.path

with open(f"encoding_dict.pickle","rb") as f:
    encoding_dict = pickle.load(f)

# If model is a Drive URL or non-local path, download it and use the local folder
tokenizer_path = _prepare_path(args.model, expect_dir=True) if args.model else None
model_path = tokenizer_path

# Load the tokenizer from the saved folder
tokenizer = AutoTokenizer.from_pretrained(tokenizer_path)

# Load the model from the saved folder
model = AutoModelForTokenClassification.from_pretrained(model_path)

sentence_data = []
# Prepare input file - supports local path or Drive URL
conll_file = _prepare_path(args.input, expect_dir=False) if args.input else None

with open(conll_file, "r", encoding='utf-8') as f:
    data = f.readlines()

sent = []
for i in range(len(data)):
	if data[i] != "\n":
		sent.append(data[i].strip())
	else:
		sentence_data.append(sent)
		sent = []
cnt = 0
def get_predictions( sentence, tokenizer, model ):
  # Let us first tokenize the sentence - split words into subwords
  tok_sentence = tokenizer(sentence, return_tensors='pt')
  global cnt
  #print(tok_sentence)

  with torch.no_grad():
    # we will send the tokenized sentence to the model to get predictions
    logits = model(**tok_sentence).logits.argmax(-1)
    
    # We will map the maximum predicted class id with the class label
    predicted_tokens_classes = [model.config.id2label[t.item()] for t in logits[0]]
    
    #print(f"Predicted token class\n{predicted_tokens_classes}")
    
    predicted_labels = []
    
    previous_token_id = 0
    # we need to assign the named entity label to the head word and not the following sub-words
    word_ids = tok_sentence.word_ids()
    cnt+=1
    print(f"{cnt}-->Word IDs\n{word_ids}")
    for word_index in range(len(word_ids)):
        if word_ids[word_index] == None:
            previous_token_id = word_ids[word_index]
        elif word_ids[word_index] == previous_token_id:
            previous_token_id = word_ids[word_index]
        else:
            predicted_labels.append( predicted_tokens_classes[ word_index ] )
            previous_token_id = word_ids[word_index]
    
    print(len(predicted_labels))
    print(sentence)
    print(predicted_labels)
    return predicted_labels


predicted_pos_tags = []
for i in range(len(sentence_data)):
    d = sentence_data[i]
    print(len(d))
    sentence = " ".join(d)
    if "\u200c" in sentence:
        print("200c",sentence)
    if "\u200b" in sentence:
        print("200b",sentence)
    if "\u200d" in sentence:
        print("200d",sentence)

    sentence = sentence.replace("\u200b","")
    sentence = sentence.replace("\u200c","")
    sentence = sentence.replace("\u200d","")    

    predicted_labels = get_predictions(sentence=sentence, 
                                   tokenizer=tokenizer,
                                   model=model
                                   )
    pos = []
    #print(len(sentence.split(" ")))
    #print(len(predicted_labels))

    for index in range(len(sentence.split(' '))):
        #print(f"Label : {predicted_labels[index]}")
        tag_id = int(predicted_labels[index].split("_")[1])
        tag = encoding_dict[tag_id]
        pos.append(tag)
        
    predicted_pos_tags.append(pos)

outfile = args.output

with open(outfile,"w",encoding='utf-8') as outf:
    for i in range(len(sentence_data)):
        s = sentence_data[i]
        #t = [i.replace("__","_") for i in predicted_pos_tags[i]]
        t = [i for i in predicted_pos_tags[i]]
        outf.write(f"<Sentence id='{i+1}'>\n")
        for j in range(len(s)):
            outf.write(f"{j+1}\t{s[j]}\t{t[j]}\n")
        outf.write("</Sentence>\n")
        if i != (len(sentence_data)-1):
            outf.write("\n")

