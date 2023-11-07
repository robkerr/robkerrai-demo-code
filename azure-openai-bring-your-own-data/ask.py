import openai, os, requests, sys

openai.api_type = "azure"

# Azure OpenAI on your own data is only supported by the 2023-08-01-preview API version
openai.api_version = "2023-08-01-preview"

# Azure OpenAI setup
openai.api_base = "" # Add your endpoint here
openai.api_key = "" 
deployment_id = "" 
# Azure Cognitive Search setup

search_endpoint = ""; 
search_key = ""
search_index_name = ""; # Add your Azure Cognitive Search index name here

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
    
if __name__ == "__main__":
    question = sys.argv[1]
    
    setup_byod(deployment_id)

    completion = openai.ChatCompletion.create(
        messages=[{"role": "user", "content": question}],
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
        ]
    )
        
    response = completion["choices"][0]["message"]["content"]
    print(response)
