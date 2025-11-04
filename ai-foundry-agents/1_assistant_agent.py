from dotenv import load_dotenv
import os
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.ai.agents.models import ListSortOrder, FilePurpose

load_dotenv()

project = AIProjectClient(
    endpoint=os.getenv("PROJECT_CONNECTION_STRING"),
    credential=DefaultAzureCredential(),
)

agent = project.agents.create_agent(
    model=os.getenv("MODEL_DEPLOYMENT_NAME"),
    name="1-assistant-agent",
    instructions=
    """
        You are a helpful assistant that likes to answer questions in a way that 
        sounds like the character Doc Brown from Back to the Future.
    """
    )

thread = project.agents.threads.create()

print("Chat with Doc Brown! (Press Enter with no input to exit)")
print("-" * 50)

try:
    while True:
        # Prompt user for input
        user_input = input("\nYou: ").strip()
        
        # If user presses enter with no input, exit
        if not user_input:
            break
        
        # Create message with user input
        message = project.agents.messages.create(
            thread_id=thread.id, 
            role="user", 
            content=user_input
        )
        
        # Run the agent
        run = project.agents.runs.create_and_process(thread_id=thread.id, agent_id=agent.id)
        
        if run.status == "failed":
            print(f"Run failed: {run.last_error}")
            continue
        
        # Get and display the agent's response
        messages = project.agents.messages.list(thread_id=thread.id, order=ListSortOrder.ASCENDING)
        for message in messages:
            if message.run_id == run.id and message.text_messages:
                print(f"Doc Brown: {message.text_messages[-1].text.value}")

except KeyboardInterrupt:
    print("\n\nExiting...")

# Delete the agent once done
project.agents.delete_agent(agent.id)
print("Great Scott! The agent has been deleted. Goodbye!")