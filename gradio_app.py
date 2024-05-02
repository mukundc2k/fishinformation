import gradio as gr
import requests
import ast
import pandas as pd

# Set the API endpoint URLs
generate_categories_url = "http://localhost:5000/generateCategories"
get_articles_url = "http://localhost:5000/getArticles"
generate_result_url = "http://localhost:5000/generateResult"

def format_categories(categories):
    data = []
    for key, value in categories.items():
        dic = {"Perspective": key}
        dic["Example Query"] = value[0]
        data.append(dic)
    return pd.DataFrame(data)

def generate_categories(query):
    response = requests.post(generate_categories_url, json={"query": query})
    res = response.json()["Result"]
    return res, format_categories(res)

def format_articles(articles):
    data = []
    for key in articles:
        for art in articles[key]:
            data.append({
                "Perspective": key,
                "Title": art["title"],
                "Link": art["link"]
            })
    return pd.DataFrame(data)

def get_articles(categories):
    response = requests.post(get_articles_url, json={"Result": categories})
    # print(categories)
    # print(response)
    res = response.json()["Result"]
    return res, format_articles(res)

def generate_result(query, articles):
    response = requests.post(generate_result_url, json={"query": query, "Result": articles})
    res = response.json()["Result"]
    return res

with gr.Blocks() as demo:
    with gr.Row():
        query_input = gr.Textbox(label="Enter your query")
        run_button = gr.Button("Run")

    # intermediate_result1 = gr.Textbox(label="Intermediate Result 1: Categories")
    intermediate_result1 = gr.DataFrame(label="Interediate Output 1: Perspectives and exempler queries", value=pd.DataFrame([["", ""]], columns=["Perspective", "Queries"]))
    intermediate_result2 = gr.DataFrame(label="Intermediate Output 2: Articles", column_widths=["20%", "40%", "40%"],value=pd.DataFrame([["", "", ""]], columns=["Perspective", "Title", "Link"]))
    final_result = gr.Textbox(label="Final Result")
    hidden_value1 = gr.State(value="initial value")
    hidden_value2 = gr.State(value="initial value")
    run_button.click(
        fn=generate_categories,
        inputs=query_input,
        outputs=[hidden_value1, intermediate_result1]
    ).success(
        fn=get_articles,
        inputs=hidden_value1,
        outputs=[hidden_value2, intermediate_result2],
    ).success(
        fn=generate_result,
        inputs=[hidden_value1, hidden_value2],
        outputs=final_result,
    )

demo.launch()