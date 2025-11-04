from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv
import os

load_dotenv()

project = AIProjectClient(
    endpoint=os.getenv("MODEL_INFERENCE_ENDPOINT"),
    credential=DefaultAzureCredential(),
)

models = project.get_openai_client(api_version=os.getenv("INFERENCE_API_VERSION"))
response = models.chat.completions.create(
    model=os.getenv("MODEL_DEPLOYMENT_NAME"),
    messages=[
        {"role": "system", "content": "You are a helpful writing assistant"},
        {"role": "user", "content": "Write me a poem about flowers"},
    ],
)

print(response.choices[0].message.content)