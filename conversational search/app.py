from openai import OpenAI
import requests
import streamlit as st
from qdrant_client import QdrantClient

from sentence_transformers import SentenceTransformer


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

        # Specify the file path where you want to save the JSON content
        return json_content
    else:
        print(response.status_code)
        return " "

class NeuralSearcher:
    def __init__(self, collection_name):
        self.collection_name = collection_name
        # Initialize encoder model
        self.model = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")
        # initialize Qdrant client
         # self.qdrant_client = QdrantClient("http://localhost:6333")
        self.qdrant_client = QdrantClient(
            url="https://ed55d75f-bb54-4c09-8907-8d112e6278a1.us-east4-0.gcp.cloud.qdrant.io",
            api_key=st.secrets["QDRANT_API_KEY"],
        )

    def search(self, text: str):
        # Convert text query into vector
        vector = self.model.encode(text).tolist()

        # Use `vector` for search for closest vectors in the collection
        search_result = self.qdrant_client.search(
            collection_name=self.collection_name,
            query_vector=vector,
            query_filter=None,  # If you don't want any filters for now
            limit=3,  # 5 the most closest results is enough
        )
        # `search_result` contains found vector ids with similarity scores along with the stored payload
        # In this function you are interested in payload only
        payloads = [hit.payload for hit in search_result]
        return payloads


def initializeClient():
    return OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

def decode(hotel_description, query):
    client = initializeClient();
    prompt = f"""
    this is the hotel description:

    \"{hotel_description}\"

     and these are my requirements

    \"{query}\"

    now tell me why the hotel might be a good fit for me given the requirements, make it consise.
    """

    stream = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        stream=True,
    )
    str = ""
    for chunk in stream:
        if chunk.choices[0].delta.content is not None:
            str += (chunk.choices[0].delta.content)
    return str
    



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
    


def home_page():
    # st.title("TraverGo")

    st.markdown("<h1 style='text-align: center; color: white;'>TraverGo</h1>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center; color: white;'>Find any type of Hotel you want !</h2>", unsafe_allow_html=True)


    if "chat" not in st.session_state:
        st.session_state["chat"] = False;
    def search_hotels():
        query = st.text_input("Enter your hotel preferences:", placeholder ="clean and cheap hotel with good food and gym")

        if "load_state" not in st.session_state:
            st.session_state.load_state = False;

        # Perform semantic search when user submits query
        if query or st.session_state.load_state:
            # if query:
            #     st.session_state['decoder'] = [0];
            st.session_state.load_state=True;
            neural_searcher = NeuralSearcher(collection_name="hotel_descriptions")
            results = sorted(neural_searcher.search(query), key=lambda d: d['sentiment_rate_average'])
            st.subheader("Hotels")
            for hotel in results:
                explore_hotel(hotel, query)  # Call a separate function for each hotel

    def explore_hotel(hotel, query):
        if "decoder" not in st.session_state:
            st.session_state['decoder'] = [0];

        button = st.button(hotel['hotel_name'])


        if button or st.session_state.chat:
            if button and st.session_state.chat:
                st.session_state.chat = False;
                del st.session_state["messages"];

            else:
                if button:
                    st.session_state["value"] = hotel;
                st.session_state.chat = True;

        else:
            st.session_state["value"] = None;


        if st.session_state.decoder == [0]:
            x = (decode(hotel['hotel_description'][:1000], query))
            st.session_state['value_1'] = x
            st.session_state.decoder = [st.session_state.decoder[0] + 1]
            st.write(x)

        elif (st.session_state.decoder == [1]):
            x = (decode(hotel['hotel_description'][:1000], query))
            st.session_state['value_2'] = x

            st.session_state.decoder = [st.session_state.decoder[0] + 1];
            st.write(x);

        elif st.session_state.decoder == [2]:
            x = (decode(hotel['hotel_description'][:1000], query))
            st.session_state['value_3'] = x;
            st.session_state.decoder = [st.session_state.decoder[0] + 1];
            st.write(x);


        if (st.session_state.decoder[0] >= 3):
            i = st.session_state.decoder[0] % 3
            l = ['value_1', 'value_2', 'value_3']
            st.session_state[l[i - 1]];
            st.session_state.decoder = [st.session_state.decoder[0] + 1];



        question = st.text_input(f"Enter a question about {hotel['hotel_name']}:");
            
        if question:
            st.write(ares_api(question + " - " + hotel['hotel_name'] + "located in" + hotel['country']))






    search_hotels()
    if (st.session_state.chat):
        chat_page()


def ares_api(query):
    response_json = getResponse(query);
    # if response_json is not json:
    #     return "Could not find information"
    return (response_json['data']['response_text'])
def chat_page():
    hotel = st.session_state["value"]
    # st.session_state.value = None
    if (hotel == None):
        return;

    st.write(hotel['hotel_name']);
    st.title("Conversation")

    # Set OpenAI API key from Streamlit secrets
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

    # st.session_state.pop("messages")
    # Set a default model
    if "openai_model" not in st.session_state:
        st.session_state["openai_model"] = "gpt-4"

    prompt = f"{hotel['hotel_description'][:1500]}\n\n everything before this point is the hotel description and reveiws. now you as a hotel advisor now, should give the best answerws based on the above text.  Now wait for my questions."
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "user", "content": prompt}]



    for message in st.session_state.messages[1:]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Accept user input
    if prompt := st.chat_input("What is up?"):
        # Display user message in chat message container
        with st.chat_message("user"):
            st.markdown(prompt)
        if (not canAnswer(hotel['hotel_description'][:2000], prompt)):
            st.write("GOING TO ARES API")
            print("GOING TO TRAVERSE API")
            x = ares_api(prompt + "for" + hotel['hotel_name'] + "located in" + hotel['country'])
            print(x)
            st.write("RECEIVED INFORMATION FROM ARES API")
            st.session_state.messages[0]['content'] = x + "\n" + st.session_state.messages[0]['content'];
        st.session_state.messages.append({"role": "user", "content": prompt})

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
home_page()

