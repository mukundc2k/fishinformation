import requests

# API key
API_KEY = 'AIzaSyCZ2z9E7DFGGIKBUW4X7AaANHXaBEE6V_M'
CX = 'c1805c89867d149c3'

def google_search(query):
    # Base URL for Google Custom Search API
    base_url = 'https://www.googleapis.com/customsearch/v1'

    # Parameters for the API request
    params = {
        'key': API_KEY,
        'cx': CX,
        'q': query,
        'num': 5,
        'lr': 'lang_en'
    }

    # Make the API request
    response = requests.get(base_url, params=params)

    # Check if the request was successful
    if response.status_code == 200:
        data = response.json()
        return [{key: x[key] for key in ['title','link', 'snippet']} for x in data['items']]
    else: 
        return []
    
def google_search_multiQ(questions):
    QnA = {}
    for q in questions:
        QnA[q] = google_search(q)
    return QnA

# Example
query =['is cinnamon good?', 'is cinnamon a bad?', 'is cinnamon not conncted to health?']
search = google_search_multiQ(query)


# Outputs
# --> search.keys()
#   --> dict_keys(['is cinnamon good?', 'is cinnamon a bad?', 'is cinnamon not conncted to health?'])
# --> search['is cinnamon a bad?'][2]   #2 is the 2nd question
#   -->dict of size 3. with title, link and snippet(description)
'''{'title': 'Cinnamon: The Good, the Bad, and the Tasty - Gastrointestinal Society',
 'link': 'https://badgut.org/information-centre/health-nutrition/cinnamon/',
 'snippet': 'Mar 11, 2020 ... Do You Need to Worry? Cinnamon is a common, enjoyable spice with a wide range of health benefits, but remember that it is not an adequate\xa0...'}'''
