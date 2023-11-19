import streamlit as st
import openai, os, requests, json

openai.api_type = "azure"
openai.api_version = "2023-08-01-preview"

# Azure OpenAI setup
openai.api_base = "https://<openai service name>.openai.azure.com/" 
openai.api_key = os.getenv("AZURE_OPENAI_KEY") 
deployment_id = "turbo-35-16k" 

# Azure AI Search setup
search_endpoint = "https://robkerrai-demo.search.windows.net"
search_key = os.getenv("AZURE_SEARCH_KEY")
search_index_name = "<index name>" 
document_library = "https://<storage account name>.blob.core.windows.net/<storage account container>"

# Add the text embedding RAG middleware to the OpenAI session used to retrieve LLM responses
def setup_byod(deployment_id: str) -> None:
    class BringYourOwnDataAdapter(requests.adapters.HTTPAdapter):

        def send(self, request, **kwargs):
            request.url = f"{openai.api_base}/openai/deployments/{deployment_id}/extensions/chat/completions?api-version={openai.api_version}"
            return super().send(request, **kwargs)

    session = requests.Session()

    # Mount a custom adapter which will use the extensions endpoint for any call using the given `deployment_id`
    session.mount(
        prefix=f"{openai.api_base}/openai/deployments/{deployment_id}",
        adapter=BringYourOwnDataAdapter()
    )

    openai.requestssession = session

setup_byod(deployment_id)

st.title('Generative AI using Azure AI Search Vector Embeddings')

@st.cache_data
def fetch_response(prompt_text):
  completion = openai.ChatCompletion.create(
    messages=prompt_text,
    deployment_id=deployment_id,
    dataSources=[ 
        {
            "type": "AzureCognitiveSearch",
            "parameters": {
                "endpoint": search_endpoint,
                "key": search_key,
                "indexName": search_index_name,
            }
        }
    ])
  
  return completion

# this is the text box where the user enters their question
# Example questions:
#    What models does directive 2019-25-55 affect? Format as a bulleted list.
#    What is the aviation authority for Israel?
#    what is cirrus design's contact information?
prompt = st.text_area("I'm an expert in FAA Airworthiness Directives. What do you want to know?")

# Present an button the user can click to send the prompt to the OpenAI LLM for a response
# Azure AI Search will:
#   1. create a vector embedding of the prompt
#   2. Search the index for vectors close to the prompt
#   3. Extract chunks from the vector index and add them to the prompt as context
#   4. Forward the updated prompt to the OpenAI LLM for a response
if st.button("Ask"):
    data_load_state = st.text('Loading Response...')
    message_text = [{"role": "user", "content": prompt}]
    completion = fetch_response(message_text)
    
    # Write LLM Response to output
    data_load_state.text("Done!")
    st.write(completion.choices[0].message.content)
    
    # Present a button to read the original PDF document 
    context_json_string = completion.choices[0].message.context.messages[0].content
    context_json = json.loads(context_json_string)
    doc_url = f"{document_library}/{context_json['citations'][0]['title']}"
    st.link_button("Read Source Document", doc_url)
