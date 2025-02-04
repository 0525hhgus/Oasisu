import os
import pathlib
import torch.nn as nn
import numpy as np
import torch
from chatbot.model.kogpt2 import DialogKoGPT2
from kogpt2_transformers import get_kogpt2_tokenizer
from flask import Flask, jsonify

from transformers import (
  ElectraConfig,
  ElectraTokenizer
)
from chatbot.model.koelectra import koElectraForSequenceClassification,koelectra_input

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

@app.route('/')
def hello_world():
  return 'Hello, World!'

@app.route('/chatbotqa/<Question>')
def chatbot_qa(Question):
  # root_path='drive/My Drive/Colab Notebooks/dialogLM'
  root_path = str(pathlib.Path(__file__).parent.absolute())
  data_path = f"{root_path}\data\wellness_dialog_for_autoregressive_train.txt"
  checkpoint_path = f"{root_path}\checkpoint"
  # save_ckpt_path = f"{checkpoint_path}/kogpt2-wellness-auto-regressive.pth"
  # save_ckpt_path = f"D:\KNHANES_7\WEB_Ask_06devbros\ai\chatbot\checkpoint\kogpt2-wellness-auto-regressive.pth"

  ctx = "cuda" if torch.cuda.is_available() else "cpu"
  device = torch.device(ctx)

  # 저장한 Checkpoint 불러오기
  # checkpoint = torch.load(save_ckpt_path, map_location=device)
  checkpoint = torch.load("../checkpoint/kogpt2-wellness-auto-regressive.pth", map_location=device)

  model = DialogKoGPT2()
  model.load_state_dict(checkpoint['model_state_dict'])

  model.eval()

  tokenizer = get_kogpt2_tokenizer()

  count = 0
  output_size = 200  # 출력하고자 하는 토큰 갯수

  sent = Question
  tokenized_indexs = tokenizer.encode(sent)

  input_ids = torch.tensor([tokenizer.bos_token_id, ] + tokenized_indexs + [tokenizer.eos_token_id]).unsqueeze(0)
  # set top_k to 50
  sample_output = model.generate(input_ids=input_ids)
  print(
    "Answer: " + tokenizer.decode(sample_output[0].tolist()[len(tokenized_indexs) + 1:], skip_special_tokens=True))
  print(100 * '-')
  chatbot_answer = str(
    tokenizer.decode(sample_output[0].tolist()[len(tokenized_indexs) + 1:], skip_special_tokens=True))

  return chatbot_answer
  # return jsonify({"chatbot_answer": chatbot_answer})

# for s in kss.split_sentences(sent):
#     print(s)

@app.route('/chatbotqa/tag/<diary>')
def chatbot_tag(diary):
  root_path = str(pathlib.Path(__file__).parent.absolute())
  checkpoint_path = f"{root_path}/checkpoint"
  save_ckpt_path = f"{checkpoint_path}/koelectra-wellness-text-classification.pth"
  model_name_or_path = "monologg/koelectra-base-discriminator"

  # 답변과 카테고리 불러오기
  category = []
  idx = -1
  # with open(root_path+'/data/wellness_data_for_text_classification.txt', 'r') as f:
  with open('..\data\wellness_data_for_text_classification.txt', 'r', encoding="UTF-8") as f:
    while True:
      line = f.readline()
      if not line:
        break
      datas = line.strip().split("\t")
      if datas[1] != str(idx):
        category.append(datas[2])
        idx += 1

  ctx = "cuda" if torch.cuda.is_available() else "cpu"
  device = torch.device(ctx)

  # 저장한 Checkpoint 불러오기
  # checkpoint = torch.load(save_ckpt_path, map_location=device)
  checkpoint = torch.load("../checkpoint/koelectra-wellness-text-classification.pth", map_location=device)

  # Electra Tokenizer
  tokenizer = ElectraTokenizer.from_pretrained(model_name_or_path)

  electra_config = ElectraConfig.from_pretrained(model_name_or_path)
  model = koElectraForSequenceClassification.from_pretrained(pretrained_model_name_or_path=model_name_or_path,
                                                             config=electra_config,
                                                             num_labels=359)
  model.load_state_dict(checkpoint['model_state_dict'])
  model.to(device)
  model.eval()

  sent = diary  # '요즘 기분이 우울한 느낌이에요'
  data = koelectra_input(tokenizer, sent, device, 512)
  # print(data)

  output = model(**data)

  logit = output
  softmax_logit = nn.Softmax(logit).dim
  softmax_logit = softmax_logit[0].squeeze()

  max_index = torch.argmax(softmax_logit).item()
  max_index_value = softmax_logit[torch.argmax(softmax_logit)].item()

  print(f'index: {category[max_index]}, value: {max_index_value}')
  print('-' * 50)

  emotion_tag = f'{category[max_index]}'

  # return jsonify({"emotion_tag": emotion_tag})
  return emotion_tag

if __name__ == "__main__":
  app.run(host="192.168.56.1", port=5000)