# %%
import requests

url = "http://localhost:5000/generateCategories"  # replace with your API endpoint URL
data = {"query": "What is the capital of France?"}  # replace with your query data

response = requests.post(url, json=data)

if response.status_code == 200:
    result = response.json()
    print(result["Result"])
else:
    print("Error:", response.status_code)
# %%
import requests
import json

# Set the API endpoint URLs
generate_categories_url = "http://localhost:5000/generateCategories"
get_articles_url = "http://localhost:5000/getArticles"
generate_result_url = "http://localhost:5000/generateResult"

# Set the query for the first endpoint
query = "What is the impact of climate change on the environment?"

# Make the first POST request to /generateCategories
response = requests.post(generate_categories_url, json={"query": query})

# Get the response from the first endpoint
categories = response.json()["Result"]

print("Intermediate result 1: Categories")
print(json.dumps(categories, indent=4))

# Make the second POST request to /getArticles
response = requests.post(get_articles_url, json={"Result": categories})

# Get the response from the second endpoint
articles_with_categories = response.json()["Result"]

print("Intermediate result 2: Articles with categories")
print(json.dumps(articles_with_categories, indent=4))

# Make the third POST request to /generateResult
response = requests.post(generate_result_url, json={"query": query, "Result": articles_with_categories})

# Get the final response from the third endpoint
final_response = response.json()["Result"]

print("Final result:")
print(final_response)
# %%
[row.split(",") for row in "".split("\n")]
# %%
