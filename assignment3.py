import re
from bs4 import BeautifulSoup
import os
from collections import defaultdict
import json
from pprint import pprint
import math
import sys

global num_docs
num_docs = 0
global wordDict
wordDict = dict()
tfidfDict = dict()
tags_list = ["title", "h1", "h2", "h3", "b", "strong", "body"]

def tfidf_calculator():
    for words in wordDict:
        # Example of wordDict:  wordDict = {"sheila": {doc1:2}}   doc1 = k, 2 = v
        for k, v in wordDict[words].items():
            if 'important' in wordDict[words]:
                for doc_num in set(wordDict[words]['important']):
                    tfidf = ((1 + math.log(wordDict[words][doc_num])) * math.log(num_docs / len(wordDict[words]))) * 5
                    if words not in tfidfDict:
                        tfidfDict[words] = dict()
                        tfidfDict[words][doc_num] = tfidf
                    else:
                        tfidfDict[words][doc_num] = tfidf
            else:
                tfidf = ((1 + math.log(wordDict[words][k])) * math.log(num_docs / len(wordDict[words])))
                if words not in tfidfDict:
                    tfidfDict[words] = dict()
                    tfidfDict[words][k] = tfidf
                else:
                    tfidfDict[words][k] = tfidf
                            
def foldersAndFiles():
    global num_docs
    dir_path = os.path.dirname(os.path.realpath(__file__))
    for rootdir, folders, files in os.walk(dir_path):
        for file in files:
            if not file.endswith(".py") and not file.endswith(".json") and not file.endswith(".tsv") and file != ".DS_Store" and not file.endswith(".pyc"):
                file_path = os.path.join(rootdir,file)
                num_docs = num_docs + 1
                grab_file_content(file_path)
                
def grab_file_content(file : str):
    global wordDict
    with open(file, encoding = "utf-8") as file_object:
        file_name = file.split("/")[-2] + "/" + file.split("/")[-1]
        content = BeautifulSoup(file_object, "html.parser")

        prettyContent = content.get_text().split('\n')
        for line in prettyContent:
            split = re.findall(r'[a-zA-Z0-9\']+', line.lower())
            for word in split:
                if word not in wordDict:
                    wordDict[word] = dict()
                    wordDict[word][file_name] = 1
                else:
                    if file_name in wordDict[word]:
                        wordDict[word][file_name] = wordDict[word][file_name] + 1
                    else:
                        wordDict[word][file_name] = 1 
            
        # in the event there is an h1, h2, h3, or bold tag, we need to mark that as important    
        if content.findAll("h1") or content.findAll("h2") or content.findAll("h3") or content.findAll("b"):
            for line in content.findAll("h1") + content.findAll("h2") + content.findAll("h3") + content.findAll("b"):
                split = re.findall(r'[a-zA-Z0-9\']+', line.get_text().lower())
                for words in split:
                    if words != "" and words in wordDict:
                        if "important" in wordDict[words]:
                            wordDict[words]['important'].append(file_name)
                        else:
                            wordDict[words]['important'] = []
                            wordDict[words]['important'].append(file_name)
 
def search_term():
    # this function handles statistics of what should be included in Deliverables
    while True:
        docDict = dict()

        url_count = 0

        user_key = input("Enter the token you would like to search for, or enter 'quit' to quit: ")
        
        multiple_words = user_key.lower().split(" ")
        if len(multiple_words) > 1:
            count_array = []
            
            for words in multiple_words:
                try:
                    for key, value in wordDict[words].items():
                        count_array.append(key)
                except Exception:
                    # if the word doesn't exist in the dictionary, we need to use recurion to jump back up
                    # to the beginning of the search_term function to ask for the user's next input
                    print('Error. User input is not in the dictionary.')
                    search_term()
                    
            # common_doc is used to store all of the document numbers that each of the words have in common
            common_doc = set()                             
            for doc_num in count_array:
                # if the number of times a document appears in count_array is equal to the length of the user's search,
                # we know that each word that the user enters appears in that specific document.
                if count_array.count(doc_num) == len(multiple_words) and doc_num not in common_doc:
                    for words in multiple_words:
                        if doc_num in docDict:
                            docDict[doc_num] = docDict[doc_num] + tfidfDict[words][doc_num]
                        else:
                            docDict[doc_num] = tfidfDict[words][doc_num]
                    
                    common_doc.add(doc_num)

            print("Searching the dictionary for " + user_key + " and building urls.txt")

            docDict = sorted(docDict.items(), key = lambda x: (-x[1], x[0]))

            # write the top 10 URLs into "urls.txt"
            with open('urls.txt', 'a') as url_file:
                title = "\nURLs for " + user_key + "\n"
                url_file.write(title)
                # if length of docDict is >= 10 we only return the top 10
                if len(docDict) >= 10:
                    for doc_num in range(10):                   
                        try:
                            with open("bookkeeping.json", encoding = "utf-8") as json_object:
                                json_content = json.load(json_object)
                                url_file.write(json_content[docDict[doc_num][0]] + "\n")
                                
                        except Exception:
                            print('Error. User input is not in the dictionary.')
                            search_term()
                else:
                    # if the length of docDict is < 10, we just for loop through it and write all URLs into "urls.txt"
                    for doc_num in range(len(docDict)):                   
                        try:
                            with open("bookkeeping.json", encoding = "utf-8") as json_object:
                                json_content = json.load(json_object)
                                url_file.write(json_content[docDict[doc_num][0]] + "\n")
                                
                        except Exception:
                            print('Error. User input is not in the dictionary.')
                            search_term()                   

            print("Finished searching for " + user_key + ".")


        # if user enters quit, terminate the program
        elif user_key == "quit":
            sys.exit()

        # if the user enters only one search word
        elif len(multiple_words) == 1:          
            user_key = user_key.lower()

            try:
                # we want docDict to contain just the document number and the name of the word since we are sorting docDict at the end to
                # display the top 10 results
                for k, v in tfidfDict[user_key].items():
                    docDict[k] = v
            except Exception:
                # if the word doesn't exist in the dictionary, we need to use recurion to jump back up
                # to the beginning of the search_term function to ask for the user's next input
                print('Error. User input is not in the dictionary.')
                search_term()
                
                
            print("Searching the dictionary for " + user_key + " and building urls.txt")

            # sort docDict by values, then by keys alphabetically
            docDict = sorted(docDict.items(), key = lambda x: (-x[1], x[0]))
            with open('urls.txt', 'a') as url_file:
                title = "\nURLs for " + user_key + "\n"
                url_file.write(title)

                if len(docDict) >= 10:
                    for doc_num in range(10):
                        try:
                            with open("bookkeeping.json", encoding = "utf-8") as json_object:
                                json_content = json.load(json_object)
                                url_file.write(json_content[docDict[doc_num][0]] + "\n")                                   
                        except Exception:
                            print('Error. User input is not in the dictionary.')
                            search_term()
                else:
                    for doc_num in range(len(docDict)):
                        try:
                            with open("bookkeeping.json", encoding = "utf-8") as json_object:
                                json_content = json.load(json_object)
                                url_file.write(json_content[docDict[doc_num][0]] + "\n")
                        except Exception:
                            print('Error. User input is not in the dictionary.')
                            search_term()

            print("Finished searching for " + user_key + ".")

if __name__ == "__main__":
    print("Building dictionary and calculating tf-idf. Please wait...")
    foldersAndFiles()
    print("Finished building dictionary.")
    print("Finished calculating tf-idf")
    tfidf_calculator()
    json.dump(wordDict, open("dictionary.txt", "w"))
    json.dump(tfidfDict, open("tfidf.txt", "w"))
    search_term()
