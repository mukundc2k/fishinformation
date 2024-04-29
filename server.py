import pathlib
import textwrap
import requests
import json

from sumy.parsers.html import HtmlParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer

import google.generativeai as genai

from googleapiclient.discovery import build

from flask import Flask, request
import pandas as pd

import re
import nltk
nltk.download('punkt')

GEMINI_API_KEY = "AIzaSyB8S2mzKjNLtWRdTVi7FAkeld5eXo1bpGE"
SEARCH_API_KEY = 'AIzaSyAREEAMxi9KoVhG-yeE2JM8puR6WCAE--k'
CX = '70aad34f181724ec4'
NUM = 3

genai.configure(api_key=GEMINI_API_KEY)

model = genai.GenerativeModel('gemini-pro')

app = Flask(__name__)

def google_search(query):
    # Base URL for Google Custom Search API
    base_url = 'https://www.googleapis.com/customsearch/v1?fields=items(title,link)'

    # Parameters for the API request
    params = {
        'key': SEARCH_API_KEY,
        'cx': CX,
        'q': query,
        'num': NUM,
        'lr': 'lang_en'
    }

    # Make the API request
    response = requests.get(base_url, params=params)

    # Check if the request was successful
    if response.status_code == 200:
        data = response.json()
        return [{key: x[key] for key in ['title','link']} for x in data['items']]
    else:
        return [f"return code: {response.status_code} | response: {response}"]

def google_search_multiQ(questions):
    QnA = {}
    for q in questions:
        QnA[q] = google_search(q)
        print(q, QnA[q])
    return QnA

def get_website_summary(url):
    try:
        # Parse the HTML content of the page using sumy's HtmlParser
        parser = HtmlParser.from_url(url, Tokenizer('english'))
        # Initialize the LsaSummarizer
        summarizer = LsaSummarizer()
        # Summarize the content using the LSA algorithm
        summary = summarizer(parser.document, 3)  # Change the number for desired summary length
        # Join the sentences of the summary
        return ' '.join(map(str, summary))
    except Exception as e:
        return f"An error occurred: {str(e)}"

def markdown_to_dict(markdown_text):

  # Remove the leading '> ' from each line.
  lines = markdown_text.split('\n')
  lines = [line[2:] for line in lines]
  # print(lines)

  # Split the lines into headings and queries.
  headings = []
  queries = []
  headings_pointer = -1
  result = {}
  for line in lines:
    if line.endswith('**'):
      headings_pointer += 1
      headings.append(line[:-2])
      result[headings[headings_pointer]] = []
    elif len(line) > 1:
      result[headings[headings_pointer]].append(line)

  return result

@app.route('/generateCategories', methods=['POST'])
def generateCategories():
    req = request.get_json()

    question = req['query']

    response = model.generate_content(f"Paraphrase the following question in different ways that preserve the core meaning but are different from each other in point of view, ideology etc: '{question}'")
    
    dict_of_lists = markdown_to_dict(response.text)

    return {'Result': dict_of_lists}

@app.route('/getArticles', methods = ['POST'])
def getArticles():
    req = request.get_json()

    queries_with_categories = req['Result']
    articles_with_categories = {}
    summaries_with_categories = {}

    for category in queries_with_categories:
        summaries_with_categories[category] = []
        #articles_with_queries = google_search_multiQ(queries_with_categories[category])
        articles_with_categories[category] = google_search_multiQ(queries_with_categories[category])
        #print(articles_with_queries)
    with open('output.json', 'w') as w:
        w.write(json.dumps(articles_with_categories, indent=4))
        
    for category in articles_with_categories:
        for question in articles_with_categories[category]:
            for article in articles_with_categories[category][question]:
                summary = get_website_summary(article['link'])
                summaries_with_categories[category].append({'title': article['title'], 'link': article['link'], 'summary': summary})

    # df = pd.read_csv('expanded_df.csv')
    # for i in range(len(df)):
    #     category = df.iloc[i]["category"]
    #     title = df.iloc[i]["title"]
    #     link = df.iloc[i]["link"]
    #     summary = df.iloc[i]["summary"]

    #     if category not in summaries_with_categories:
    #         summaries_with_categories[category] = []

    #     summaries_with_categories[category].append({'title': title, 'link': link, 'summary': summary})

    return {'Result': summaries_with_categories}


@app.route('/generateResult', methods=["POST"])
def generateResult():
    req = request.get_json()

    question = req['query']
    summaries_with_categories = req['Result']

    summary_stuff = ""
    for category in summaries_with_categories:
        for article in summaries_with_categories[category]:
            summary_stuff += f"{category}:\t{article['summary']}\n"

    final_response = model.generate_content(f"{summary_stuff}\n\nYou are an expert at answering questions with a balanced perspective. Above are some perspectives and their respective content to answer the question: {question}. Please closely analyse all the different viewpoints and crisply answer the question: {question} directly, but add the crisp information obtained from each alternative perspective to provide a more unbiased answer, representative of all perspectives but crisp and caters to the original question.")
    with open('out.txt', 'w') as w:
        print(w.write(final_response.text))

    return {'Result': final_response.text}

if __name__ == '__main__':
    app.run(port=5000)
