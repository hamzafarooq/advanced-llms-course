---
title: Harnessing the Power of Ares API for Real-Time Insights in TraverGo’s Chatbot
author_profile: true
permalink: /projects/travergo_article
---
{% include base_path %}

TraverGo is the 1st place winning hackalytics project at Georgia Tech project for the Traversaal AI challenge. TraverGo's hotel search platform is an innovative way to help users find the perfect accommodations. Our platform offers powerful features like Neural Search and Sentiment Analysis to help users find their perfect hotel. One of its standout features is the seamless integration of a chatbot with the Ares API, ensuring users can get both hotel-specific answers and access real-time information about the surrounding area.  Let's dive into how this integration works.

# Why the Ares API?

While your chatbot has a solid knowledge base of hotel descriptions and reviews, there will be times when a user's query goes beyond those confines. The Ares API acts as a powerful bridge between our chatbot and the vast knowledge base of Google. For instance some questions that a chatbot might find hard to answer are based on:

1. "Are there any good Italian restaurants near the hotel?"
2. "What's the nearest subway station?"
3. "Is there a museum within walking distance?"

These types of questions fall outside the scope of our hotel-specific dataset.  Ares API allows us to tap into Google's real-time data, providing accurate and up-to-date answers for our users.

# Implementation Logic
The following will be our flow of logic in dealing with a specific user question. 
1. Dependency: We start by importing the ares library, granting us access to the Ares API.

2. Intent Detection: Our chatbot needs a way to distinguish when a user wants to utilize the Ares integration. We use a dedicated prompt to distinguish between instanecs where we know the answer.

3. Query Extraction: We isolate the actual question the user intends to ask Google.

4. Ares Search: The core of the integration. Relevent code is in the next section

5. Chatbot Response: Our chatbot delivers the formatted Ares API results to the user.

# Integrating the Ares API into our chatbot

## Setting up the API
To get started, you'll need:

1. Ares API Key: Sign up with the Ares API provider to get your API key.
2. Python Libraries: Install the requests and openai libraries (pip install requests openai).

```python
import requests
import openai
import streamlit as st  # If using Streamlit

def getResponse(query):
    url = "https://api-ares.traversaal.ai/live/predict"
    payload = { "query": [query] }
    headers = {
      "x-api-key": st.secrets["TRAVERSAAL"],
      "content-type": "application/json"
    }
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        # Get the JSON content from the response
        json_content = response.json()
        return json_content
    else:
        return ""
```
`getResponse`: This function handles sending a query to the Ares API endpoint, managing authentication, and processing the returned JSON response.


You will need to get your own Ares API key in order to use this function. If the response from the GET request is 200 it means that it was successfull and hence will return the relevent data else it would return an empty string.

We user another function `ares_api` to wrap the call to getResponse(), this makes it easier to get the relevent text from the API's response.

```python
def ares_api(query):
    response_json = getResponse(query);
    return (response_json['data']['response_text'])
```


## Delegation of tasks
To ensure that we only delegate the relevent user question to the Ares API when we are unable to find the answer within our text corpus we use another decoder model which will tell us if the specific answer to the user question already exists within our code. To implement this we use the following function `canAnswer()`
```python
def canAnswer(description, q):
    client = initializeClient();

    prompt = f"""
    \"{description}\"
    \n
    is there information about the following in the above text, make sure you will be able to enaswer the following question prcisely: {q}
    \n
    answer in one word, "yes" or "no"
    """
    stream = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        stream=True,
    )
    strr = ""
    for chunk in stream:
        if chunk.choices[0].delta.content is not None:
            strr += (chunk.choices[0].delta.content)
    return strr.lower() == "yes";
```
`canAnswer`: This function leverages OpenAI's language models to intelligently determine if a question can be answered confidently based on a given description.


## Chatbot Integration
This is the main integration of the Ares API with our chatbot. After initializing streamlit session states, we first append the hotel description to the message history of our chatbot as follows. We also include the relevent prompt to get the chatbot ready to answer our questions.
```python

def chat_page():
    hotel = st.session_state["value"]
    # st.session_state.value = None
    if (hotel == None):
        return;

    st.title("Conversation")

    # Set OpenAI API key from Streamlit secrets
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

    # st.session_state.pop("messages")
    # Set a default model
    if "openai_model" not in st.session_state:
        st.session_state["openai_model"] = "gpt-4"

    prompt = f"{hotel['hotel_description'][:1500]}\n\n everything before this point is the hotel description and reveiws. now you as a hotel advisor now, should give the best answerws based on the above text. Now wait for my questions."
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "user", "content": prompt}]

    for message in st.session_state.messages[1:]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

```

In the above code we create our prompt with the hotel description and prepare our chatbot to answer our questions. We append this to the start of the message history every time the chatbot retrieves its message history from the streamlit session state.


Now we imlement our logic of delegating the questions to the API if and when we cannot find them in our text.
```python
def chat_page():
    # ... (Code for initializing session states and appending description) ...
    # Accept user input
    if prompt := st.chat_input("What is up?"):
        # Display user message in chat message container
        with st.chat_message("user"):
            st.markdown(prompt)
        if (not canAnswer(hotel['hotel_description'][:2000], prompt)):
            x = ares_api(prompt + "for" + hotel['hotel_name'] + "located in" + hotel['country'])
            st.session_state.messages[0]['content'] = x + "\n" + st.session_state.messages[0]['content'];
        st.session_state.messages.append({"role": "user", "content": prompt})
```

The relevent code bits are, 
```python
if (not canAnswer(hotel['hotel_description'][:2000], prompt)):
    x = ares_api(prompt + "for" + hotel['hotel_name'] + "located in" + hotel['country'])
    st.session_state.messages[0]['content'] = x + "\n" + st.session_state.messages[0]['content'];
```

In this code we first call our `canAnswer` function which uses our gpt-4 decoder model in order to determine if we can answer the question or not given our text. If `canAnswer` return true we continue as normal and let our chatbot answer the question. However if it returns false it implies that we cannot find the answer in our text.

In this case we create a prompt to give to the API and receive the new information. Now that we have this information we append this to our hotel description and reviews that we already have. In this way our chatbot has access to both the new information from Google that we previously did not have access to and also have access to the hotel description and reviews that was in our dataset.

```python
    #Display assistant response in chat message container
    with st.chat_message("assistant"):
        stream = client.chat.completions.create(
            model=st.session_state["openai_model"],
            messages=[
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.messages
            ],
            stream=True,
        )
        response = st.write_stream(stream)
    st.session_state.messages.append({"role": "assistant", "content": response})
```

The above code finally creates the response from gpt-4 using the client that we initialized.


