#Imports
import spacy
nlp = spacy.load("en_core_sci_md")

'''
Function to calculare the cosine similarity
'''

def cosine(sen1,sen2):
  
  search_doc = nlp(sen1)
  main_doc = nlp(sen2)

  search_doc_no_stop_words = nlp(' '.join([str(t) for t in search_doc if not t.is_stop]))
  main_doc_no_stop_words = nlp(' '.join([str(t) for t in main_doc if not t.is_stop]))

  return search_doc_no_stop_words.similarity(main_doc_no_stop_words)

'''
Function to select the highest score given some rules. It is expected that the NMT is the best translation of a term,
However, some times NMT mistranslates the NE and the NMT with context could provide better results.
'''

def cosine_queries(triplets):

  candis=[]
  for t in triplets:
    temp=[]
    zero= cosine(t[0], t[1])
    first= cosine(t[1], t[2])
    second= cosine(t[0], t[2])
    temp.append([zero, first, second])
    tempe=max(temp[0])
    inx= temp[0].index(tempe)
    if inx == 0:
      candis.append(t[1])
    elif inx== 1:
      candis.append(t[1])
    elif inx == 2:
      candis.append(t[2])
  return candis

#queries_cosine=cosine_queries(triplets)