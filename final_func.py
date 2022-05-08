#imports
import requests
from requests.exceptions import Timeout
import requests_cache
import time
#imports initial step
from get_NER import *
from translation_cands import *
from query_selection import *

#Imports second part
from doc_retrieval import *
from crawler import *
from information_retri import *
from ner_es import *
from cands_miner import *
#Imports
from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline


'''
Initial process: Get_NER, translation_cands, query_selection.
'''
#NER
#start_time = time.time()

#data= ["Opsins are a group of proteins made light-sensitive via the chromophore retinal (or a variant) found in photoreceptor cells of the retina.", 
#"Five classical groups of opsins are involved in vision, mediating the conversion of a photon of light into an electrochemical signal, the first step in the visual transduction cascade.",
#"Another opsin found in the mammalian retina, melanopsin, is involved in circadian rhythms and pupillary reflex but not in vision."] 
# this should be populated by the input of the user

def run_experiment(input_text):
  start_time = time.time()
  #Instanciating the NER system and creating pipelines
  PATH= "roberta-base-biomedical-clinical-es-finetuned-ner-CRAFT_AugmentedTransfer_ES/"
  print("loading the transformers")

  tokenizer_mbert_mul = AutoTokenizer.from_pretrained(PATH, local_files_only=True)

  model_mbert_mul = AutoModelForTokenClassification.from_pretrained(PATH, local_files_only=True)
  ner = pipeline('ner', aggregation_strategy="max", model=model_mbert_mul, tokenizer=tokenizer_mbert_mul)
  print("loaded the transformers : ")
  nes_en= ner(input_text)
  print(nes_en)
  new_nes= unique_nes(nes_en)
  print("finished new_nes")
  n_nes= len(new_nes)
  dictionary_results, left_nes= dic_lookup(new_nes)
  print("finish dict results")
  #Translation Candidates
  context= get_context(left_nes, nes_en, input_text)
  nmt, context_sens, wiki_first= thread_cands(left_nes, context)
  nmt_expanded= NMT_expansion(left_nes, dic_tags,nmt)
  triplets= trio_cand(wiki_first, nmt_expanded, context_sens)
  #Query Selection
  queries_cosine=cosine_queries(triplets)

  '''
  Second Part:
  It should: for each triplet find the documents in google and parse them. Then get the best documents, tokenize everything. Process NER for these documents. 
  then process all the mining and scoring functions. finally score the candidates and get the best one.
  '''

  requests_session = requests_cache.CachedSession('demo_cache')
  finallya=[] 
  #Get all links at once (faster)
  new_links= get_links(triplets)
  #Loop to get each set of links for each NE and start parsing and extracting
  for i in range(len(queries_cosine)):
        print(" Start of new NE: ", left_nes[i], "\n")
        temp=[]
        idx= i
          
        final= get_parse_new(triplets[i], requests_session, new_links[i], left_nes[i][0])
        clean_docs= cleanse_docs(final)
        if len(clean_docs)>0:
          best_docs=semantic_search(triplets[i][2], clean_docs) 

          #ner
          nes_es= ner_es(best_docs)
          list_es= list_nes_es(nes_es)

          #preprocessing the docs
          tokenized_sentence= tok_es(best_docs)
          tokenized_nes= token_nes(list_es)
          retokenized_article= retoken_doc(tokenized_nes, tokenized_sentence)

          #get candidates
          final_cands=trans_candidates_thread(best_docs, nes_es, queries_cosine[i], triplets[i], queries_cosine, retokenized_article,left_nes,nmt[i], left_nes[i][0], list_es)
            
          #final candidate
          final_result= last_simil_test(final_cands, queries_cosine[i])
          winner= weight(final_result,nmt[i])

          #List including original NE and the winner.

          finallya.append([left_nes[i][0],left_nes[i][3], winner])

        #If no document was retrieved then use the NMT output
        else:
          finallya.append([left_nes[i][0], left_nes[i][3] , nmt[i]])

  #time measurement
  time_final= (time.time() - start_time)/60
  list_nes_final= dictionary_results + finallya

  return list_nes_final, n_nes, time_final

#list_nes_final, n_nes, time_final= run_experiment(data)
#print(list_nes_final)
#print(n_nes)
#print(time_final)