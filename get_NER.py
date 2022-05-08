
#import requests
import json
import nltk
nltk.download("punkt")
nltk.download("stopwords")
from nltk.corpus import stopwords
stopWords = set(stopwords.words('english'))




#Instanciating the NER system and creating pipelines
#PATH= "roberta-base-biomedical-clinical-es-finetuned-ner-CRAFT_AugmentedTransfer_ES/"
#print("loading the transformers")

#tokenizer_mbert_mul = AutoTokenizer.from_pretrained(PATH, local_files_only=True)

#model_mbert_mul = AutoModelForTokenClassification.from_pretrained(PATH, local_files_only=True)

#print("finished with one")

#tokenizer_mbert_es = AutoTokenizer.from_pretrained(PATH, local_files_only=True)

#model_mbert_es = AutoModelForTokenClassification.from_pretrained(PATH, local_files_only=True)



#ner = pipeline('ner', aggregation_strategy="max", model=model_mbert_mul, tokenizer=tokenizer_mbert_mul)
#ner_sp = pipeline('ner', aggregation_strategy="max", model=model_mbert_es, tokenizer=tokenizer_mbert_es)


#nes_en= ner(data)

#remove duplicates, low scoring NEs, stopwords, and spacing.

def unique_nes(nes_en):
  new_nes=[]
  count=0
  for i,ne in enumerate(nes_en):
    lista_test=[]
    for ii,n in enumerate(ne):
      if n["word"].lower().strip() not in [l[0].lower() for l in new_nes] and n["word"].lower().strip() not in stopWords and n["score"]>0.80 and n["word"].strip().isspace() == False:
        new_nes+=[[n["word"].strip(), i,ii, n["entity_group"]]]
  return new_nes

#new_nes= unique_nes(nes_en)


def dic_lookup(new_nes):

  with open('dictionary/dic_final_lower.json') as f:
    data_dic = json.load(f)#, encoding= "UTF-8" removed in python 3.9

  dictionary_results=[]
  left_nes=[]
  for i in range(len(new_nes)):
    try:
      if data_dic[new_nes[i][0].lower().strip()] or data_dic[new_nes[i][0].lower().strip()+ "s"] :
        dictionary_results.append([new_nes[i][0],new_nes[i][3], data_dic[new_nes[i][0]]["translation"]])
    except:
      left_nes.append(new_nes[i])
  return dictionary_results, left_nes

#dictionary_results, left_nes= dic_lookup(new_nes)