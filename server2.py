import pathlib
import textwrap
import requests
import json
import re

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

GEMINI_API_KEY = "YOUR_GEMINI_API_KEY"
SEARCH_API_KEY = 'YOUR_CUSTOM_SEARCH_ENGINE_API_KEY'
CX = 'YOUR_SEARCH_ENGINE_ID'
NUM = 2

genai.configure(api_key=GEMINI_API_KEY)

model = genai.GenerativeModel('gemini-pro')

df = pd.DataFrame()  # Define a global DataFrame

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
        summary = summarizer(parser.document, 1)  # Change the number for desired summary length
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

    response = model.generate_content(f"Paraphrase the following question in different have the same core meaning but are different from each other in terms of like positive, negative, neutral, left leaning, right leaning, critical, supportive, etc. basically come up with different point of views that is relevant to the question, ideologies etc: '{question}'. Consider maximum of four points of view")
    
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
                # summaries_with_categories[category].append({'title': article['title'], 'link': article['link'], 'summary': summary})
                summaries_with_categories[category].append({'category': category, 'question': question, 'title': article['title'], 'link': article['link'], 'summary': summary})


    return {'Result': summaries_with_categories}


@app.route('/generateResult', methods=["POST"])
def generateResult():
    req = request.get_json()

    question = req['query']
    summaries_with_categories = req['Result']

    summary_stuff = ""
    counter = 0
    for category in summaries_with_categories:
        for article in summaries_with_categories[category]:
            counter+=1
            summary_stuff += f"{counter} {category}:\t{article['summary']}\n"


    final_response = model.generate_content(f"{summary_stuff}\nYou are a kind, humane but critical, and factual expert at answering questions with a balanced perspective that is inclusive and comprehensive of all views. Above are some perspectives and their respective content to closely analyze and crisply answer the main question: {question}. To answer like the balanced, humane, critical but exhaustive expert, add the crisp information obtained from each alternative perspective to provide a more unbiased answer, representative of all perspectives but not long, in a normal sounding sentence or max a paragraph and caters to the original question. Additionally, provide citations in hyperlink format that is [1]({{link}}) , indicating the line number in square brackets.")
    print(final_response)
    data_rows = [item for sublist in summaries_with_categories.values() for item in sublist]

    # Create the DataFrame
    df = pd.DataFrame(data_rows, columns=['category', 'question', 'title', 'link', 'summary'])
    print(df)
    numbers = [x - 1 for x in [int(x) for sublist in [re.findall(r'\d+', x) for x in re.findall(r'\[(\d+(?:,\s*\d+)*)]', final_response.text)] for x in sublist]]

    sentence = final_response.text

    links_list = []
    for link_num in [x+1 for x in numbers]:
        link = df['link'][link_num - 1]
        links_list.append(f"{link_num}: {link}")

    links_str = '\n'.join(links_list)
    modified_sentence = f"{sentence}\n\n{links_str}"

    with open('out.txt', 'w') as w:
        print(w.write(modified_sentence))

    return {'Result': modified_sentence}

if __name__ == '__main__':
    app.run(port=5000)
