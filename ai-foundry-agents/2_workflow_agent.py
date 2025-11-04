from dotenv import load_dotenv
import os
import asyncio
import sys
from uuid import uuid4
from collections.abc import Awaitable, Callable
from contextlib import AsyncExitStack
from typing import Any

from agent_framework import AgentRunUpdateEvent, WorkflowBuilder, WorkflowOutputEvent
from agent_framework.azure import AzureAIAgentClient
from azure.identity.aio import AzureCliCredential
from azure.ai.documentintelligence.aio import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential

load_dotenv()

async def extract_text_from_pdf(filename: str) -> str:
    """
    Tool function to extract text from a PDF file using Azure Document Intelligence.
    
    Args:
        filename: Path to the PDF file to process
        
    Returns:
        Extracted text content as a string
    """
    try:
        # Get Document Intelligence endpoint and key from environment
        doc_intel_endpoint = os.getenv("DOCUMENT_INTELLIGENCE_ENDPOINT")
        doc_intel_key = os.getenv("DOCUMENT_INTELLIGENCE_KEY")
        
        if not doc_intel_endpoint or not doc_intel_key:
            return "Error: Document Intelligence endpoint and key must be set in environment variables"
        
        # Check if file exists
        if not os.path.exists(filename):
            return f"Error: File '{filename}' not found"
        
        # Read PDF file
        with open(filename, "rb") as pdf_file:
            pdf_bytes = pdf_file.read()
        
        # Create Document Intelligence client
        credential = AzureKeyCredential(doc_intel_key)
        async with DocumentIntelligenceClient(
            endpoint=doc_intel_endpoint, 
            credential=credential
        ) as client:
            
            # Analyze document using the prebuilt-read model
            poller = await client.begin_analyze_document(
                model_id="prebuilt-read",
                body=pdf_bytes,
                content_type="application/octet-stream"
            )
            
            # Wait for analysis to complete
            result = await poller.result()
            
            # Extract text content
            extracted_text = ""
            if result.content:
                extracted_text = result.content
            else:
                # Fallback: extract from paragraphs if content is not available
                if result.paragraphs:
                    extracted_text = "\n".join([paragraph.content for paragraph in result.paragraphs])
            
            return extracted_text if extracted_text else "No text found in the PDF"
            
    except Exception as e:
        return f"Error extracting text from PDF: {str(e)}"

async def create_azure_ai_agent() -> tuple[Callable[..., Awaitable[Any]], Callable[[], Awaitable[None]]]:
    """Helper method to create an Azure AI agent factory and a close function.

    This makes sure the async context managers are properly handled.
    """
    stack = AsyncExitStack()
    cred = await stack.enter_async_context(AzureCliCredential())

    client = await stack.enter_async_context(AzureAIAgentClient(
        project_endpoint=os.getenv("PROJECT_CONNECTION_STRING"), 
        model_deployment_name=os.getenv("MODEL_DEPLOYMENT_NAME"), 
        inference_api_version=os.getenv("INFERENCE_API_VERSION"),
        async_credential=cred))
    
    async def agent(**kwargs: Any) -> Any:
        kwargs.setdefault("store", True)  # service-managed thread
        return await stack.enter_async_context(client.create_agent(**kwargs))

    async def close() -> None:
        await stack.aclose()

    return agent, close

async def main(pdf_filename: str = None) -> None:
    agent, close = await create_azure_ai_agent()
    try:
        # Create tool for PDF text extraction
        async def pdf_extraction_tool(filename: str) -> str:
            """Extract text from a PDF file using Document Intelligence."""
            return await extract_text_from_pdf(filename)

        # Create a PDF Reader agent that can extract text from PDFs
        # Note: Waiting for fix https://github.com/microsoft/agent-framework/pull/1769 to be 
        # released for tool called form workflow agent to work correctly
        # (fix merge was 10/30/25, latest version this date is 10/28/25 so should be soon)
        pdf_reader = await agent(
            name="PDF Reader",
            instructions=(
                "You are an excellent content writer. You have access to a tool that can extract text from PDF files. "
                "When given a PDF filename, use the pdf_extraction_tool to extract the text content, "
                "then pass that extracted text to the next agent for review and analysis."
            ),
            tools=[pdf_extraction_tool],
            store=True
        )

        # Create a Reviewer agent that provides feedback
        resume_reviewer = await agent(
            name="Reviewer",
            instructions=(
                "You are an excellent content reviewer. "
                "Provide a brief summary of the candidate qualifications for an Azure AI Engineer role based on the provided content. "
                "Further, list bullets of key skills and experiences that stand out."
            ),
            store=True
        )

        # Build the workflow with agents as executors
        workflow = WorkflowBuilder().set_start_executor(pdf_reader).add_edge(pdf_reader, resume_reviewer).build()

        last_executor_id: str | None = None

        input_message = f"Please extract text from the PDF file: {pdf_filename}, and review the content."

        events = workflow.run_stream(input_message)
        async for event in events:
            if isinstance(event, AgentRunUpdateEvent):
                # Handle streaming updates from agents
                eid = event.executor_id
                if eid != last_executor_id:
                    if last_executor_id is not None:
                        print()
                    print(f"{eid}:", end=" ", flush=True)
                    last_executor_id = eid
                print(event.data, end="", flush=True)
            elif isinstance(event, WorkflowOutputEvent):
                print("\n===== Final output =====")
                print(event.data)
    finally:
        await close()

if __name__ == "__main__":
    # Check if a PDF filename was provided as a command line argument
    pdf_filename = sys.argv[1] if len(sys.argv) > 1 else None

    if pdf_filename is None:
        pdf_filename = "resume.pdf"
    
    if pdf_filename:
        print(f"Processing PDF file: {pdf_filename}")
    else:
        print("No PDF file provided. Running with default content generation.")
    
    asyncio.run(main(pdf_filename))