
#imports
from sentence_transformers import SentenceTransformer, CrossEncoder, util
import torch



'''
Clean new documents. Preprocessing to avoid as much as possible the noise and Split documents into sentences,
so that the system will select best sentences and not whole documents 
'''
def cleanse_docs(docs):
  clean=[]
  repla=["\n","\xa0", "\u200b", "\xad", "\ufeff", "\t", "\r", "\t\t", "\n\n"]
  for d in docs:
    for re in repla:
      if re in d:
        d= d.replace(re, "") 
        clean.append(d)
  new_docs=[]
  for t in clean:
    if len(t)<1 or t.isspace() and t in new_docs:
      continue
    else:
      new_docs.append(t)
  for new in new_docs:
    if new.isspace():
      new_docs.remove(new)
  return new_docs

'''
First option. Sentence transformer
'''
model_ir = SentenceTransformer("distiluse-base-multilingual-cased-v1")
'''
Function to rank the best docs out of the gotten ones from before.
It is also used to comput similarities in other functions while mining the translations.
'''


def ir_scores(query, docs):
  

  #Encode query and documents
  query_emb = model_ir.encode(query)
  doc_emb = model_ir.encode(docs)

  #Compute dot score between query and all document embeddings
  scores = util.dot_score(query_emb, doc_emb)[0].cpu().tolist()

  #Combine docs & scores
  doc_score_pairs = list(zip(docs, scores))

  #Sort by decreasing score
  doc_score_pairs = sorted(doc_score_pairs, key=lambda x: x[1], reverse=True)
  list_scores=[]
  i=0
  #Output passages & scores
  for doc, score in doc_score_pairs:
      list_scores.append([i, score, doc])
      i+=1
  best_docs=[]
  for doc in list_scores[:5]:
    best_docs.append(doc[2])
  return best_docs

'''
Compute similarity score using the sentence transformer.
This is for words and not paragraphs
'''
def similarity_score(word1, word2):
  list_final=[]

  word1= word1.lower()
  word2= [w.lower() for w in word2]
  query_emb = model_ir.encode(word1)#query
  doc_emb = model_ir.encode(word2)

     #Compute dot score between query and all document embeddings
  scores = util.dot_score(query_emb, doc_emb)[0].cpu().tolist()

      #Combine docs & scores
  doc_score_pairs = list(zip(word2, scores))

      #Sort by decreasing score
  doc_score_pairs = sorted(doc_score_pairs, key=lambda x: x[1], reverse=True)

  list_scores=[]
  i=0
  #Output passages & scores
  for doc, score in doc_score_pairs:
      list_scores.append([i, score, str.title(doc)])
      i+=1
  best_docs=[]
  for doc in list_scores[:10]:
    best_docs.append(doc[1:])
  return best_docs


'''
Second option for Semantic search using a biencoder and then a cross encoder.
Adapted from https://github.com/UKPLab/sentence-transformers/tree/master/examples/applications/retrieve_rerank
'''

#Semantic search and re ranking together. Below is only semantic text similarity.

#We use the Bi-Encoder to encode all passages, so that we can use it with sematic search
bi_encoder = SentenceTransformer('multi-qa-MiniLM-L6-cos-v1')
bi_encoder.max_seq_length = 256     
top_k = 32                          

#The bi-encoder will retrieve 10 documents. We use a cross-encoder, to re-rank the results list to improve the quality
cross_encoder = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')



def semantic_search(query, corpus):
    corpus_embeddings = bi_encoder.encode(corpus, convert_to_tensor=True, show_progress_bar=True)
    ##### Sematic Search #####
    # Encode the query using the bi-encoder and find potentially relevant passages
    question_embedding = bi_encoder.encode(query, convert_to_tensor=True)
    if torch.cuda.is_available():
      question_embedding = question_embedding.cuda()

    hits = util.semantic_search(question_embedding, corpus_embeddings, top_k=top_k)
    hits = hits[0]  # Get the hits for the first query

    ##### Re-Ranking #####
    # Now, score all retrieved passages with the cross_encoder
    cross_inp = [[query, corpus[hit['corpus_id']]] for hit in hits]
    cross_scores = cross_encoder.predict(cross_inp)

    # Sort results by the cross-encoder scores
    for idx in range(len(cross_scores)):
        hits[idx]['cross-score'] = cross_scores[idx]

    hits = sorted(hits, key=lambda x: x['cross-score'], reverse=True)
    new_best_docs= []
    for hit in hits[0:4]:#Get the best 4 docs
      new_best_docs.append(corpus[hit['corpus_id']].replace("\n", " "))
    return new_best_docs


def semantic_score(query, corpus):
    corpus_embeddings = bi_encoder.encode(corpus, convert_to_tensor=True, show_progress_bar=True)
    ##### Sematic Search #####
    # Encode the query using the bi-encoder and find potentially relevant passages
    question_embedding = bi_encoder.encode(query, convert_to_tensor=True)
    if torch.cuda.is_available():
      question_embedding = question_embedding.cuda()

    hits = util.semantic_search(question_embedding, corpus_embeddings, top_k=top_k)
    hits = hits[0]  # Get the hits for the first query

    ##### Re-Ranking #####
    # Now, score all retrieved passages with the cross_encoder
    cross_inp = [[query, corpus[hit['corpus_id']]] for hit in hits]
    cross_scores = cross_encoder.predict(cross_inp)

    # Sort results by the cross-encoder scores
    for idx in range(len(cross_scores)):
        hits[idx]['cross-score'] = cross_scores[idx]

    hits = sorted(hits, key=lambda x: x['cross-score'], reverse=True)
    new_best_docs= []
    #new_best_docs.append([hits[0]["score"],corpus[hits[0]["corpus_id"]].replace("\n", " ")])

    for hit in hits[0:7]:#Get the best 4 docs
      new_best_docs.append([hit["score"], corpus[hit['corpus_id']].replace("\n", " ")])
    #return new_best_docs

    return new_best_docs