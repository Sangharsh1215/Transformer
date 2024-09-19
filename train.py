import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader, random_split
from dataset import BillingualDataset, casual_mask
from datasets import load_dataset
from tokenizers import Tokenizer
from tokenizers.models import WordLevel
from tokenizers.trainers import WordLevelTrainer
from tokenizers.pre_tokenizers import Whitespace
from pathlib import Path

def get_all_sentences(ds,lang):
  for item in ds:
    yield item['translation'][lang]

def get_tokenizer(config, ds, lang):
  tokenizer_path = Path(config['tokenizer_file'].format(lang))
  if not Path.exists(tokenizer_path):
    tokenizer = Tokenizer(WordLevel(unk_token='[UNK]'))
    tokenizer.pre_tokenizer = Whitespace()
    trainer = WordLevelTrainer(special_tokens=["[UNK]", "[PAD]", "[SOS]", "[EOS]"], min_frequency=2)
    tokenizer.train_from_iterator(get_all_sentences(ds,lang), trainer = trainer)
    tokenizer.save(str(tokenizer_path))

  else:
    tokenizer = Tokenizer.from_file(str(tokenizer_path))
    return tokenizer
  


def get_ds(config):
  ds_raw = load_dataset('opus_books', f'{config["lang_src"]}-{config["lang_tgt"]}', splits = 'train')

  tokenizer_src = get_tokenizer(config, ds_raw, config['lang_src'])
  tokenizer_tgt = get_tokenizer(config, ds_raw, config['lang_tgt'])

  train_ds_size = int(0.9 + len(ds_raw))
  val_ds_size = len(ds_raw) - train_ds_size
  train_ds_raw, val_ds_raw = random_split(ds_raw, [train_ds_size, ])


train_ds = BillingualDataset(train_ds_raw, tokenizer_src, tokenizer_tgt, config['lang_src'], config['lang_tgt'], config['seq_len'])
val_ds = BillingualDataset(val_ds_raw, tokenizer_src, tokenizer_tgt, config['lang_src'], config['lang_tgt'], config['seq_len'])


max_len_src = 0 
max_len_tgt = 0

for item in ds_raw:
    src_ids = tokenizer_src.encode