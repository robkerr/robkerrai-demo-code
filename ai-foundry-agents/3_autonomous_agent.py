import os, json, asyncio
from typing import Dict, Any
from azure.identity.aio import AzureCliCredential

# --- Agent Framework (Azure) ---
from agent_framework.azure import AzureAIAgentClient  # Foundry-backed agents (threads/runs)

# --- (Example) external SDKs / stubs ---
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence.aio import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeDocumentRequest

# --------------------------
# Tool implementations
# --------------------------

async def tool_extract_invoice(args: Dict[str, Any]) -> Dict[str, Any]:
    """Extract text/fields from a PDF using Azure Document Intelligence."""
    filename = args.get("filename")
    if not filename or not os.path.exists(filename):
        return {"ok": False, "error": f"file not found: {filename}"}

    endpoint = os.environ["DOCUMENT_INTELLIGENCE_ENDPOINT"]
    key = os.environ["DOCUMENT_INTELLIGENCE_KEY"]
    client = DocumentIntelligenceClient(endpoint=endpoint, credential=AzureKeyCredential(key))

    # Use prebuilt-document to keep sample simple; swap to prebuilt-invoice if you prefer
    with open(filename, "rb") as f:
        pdf = f.read()
    poller = await client.begin_analyze_document(
        model_id="prebuilt-invoice",
        analyze_request=AnalyzeDocumentRequest(bytes_source=pdf)
    )
    result = await poller.result()

    # Minimal mapping for demo
    out = {
        "vendor_name": getattr(result.documents[0].fields.get("VendorName"), "content", None) if result.documents else None,
        "invoice_id": getattr(result.documents[0].fields.get("InvoiceId"), "content", None) if result.documents else None,
        "purchase_order": getattr(result.documents[0].fields.get("PurchaseOrder"), "content", None) if result.documents else None,
        "invoice_total": getattr(result.documents[0].fields.get("InvoiceTotal"), "content", None) if result.documents else None,
        "raw": result.as_dict(),
    }
    return {"ok": True, "data": out}

# In-memory “ERP” stubs for demo
_FAKE_PO = {
    "PO-1001": {"vendor": "Contoso Ltd", "amount": 1250.00, "status": "Open"},
    "PO-1002": {"vendor": "Fabrikam Inc", "amount": 980.75, "status": "Open"},
}

async def tool_validate_against_po(args: Dict[str, Any]) -> Dict[str, Any]:
    po = args.get("po")
    total = float(args.get("total") or 0)
    vendor = args.get("vendor")
    po_row = _FAKE_PO.get(po)
    if not po_row:
        return {"ok": False, "delta": {"reason": "PO not found"}}
    deltas = {}
    if abs(po_row["amount"] - total) > 0.01:
        deltas["amount_mismatch"] = {"po_amount": po_row["amount"], "inv_amount": total}
    if vendor and po_row["vendor"].lower() != vendor.lower():
        deltas["vendor_mismatch"] = {"po_vendor": po_row["vendor"], "inv_vendor": vendor}
    return {"ok": len(deltas) == 0, "delta": deltas}

async def tool_post_to_erp(args: Dict[str, Any]) -> Dict[str, Any]:
    # pretend to post; return a voucher id
    return {"ok": True, "voucher_id": f"VCHR-{args.get('invoice_id','NA')}-001"}

# --------------------------
# Tool schemas (for function calling)
# --------------------------
EXTRACT_TOOL = {
    "name": "extract_invoice",
    "description": "Extracts fields from a vendor invoice PDF.",
    "parameters": {
        "type": "object",
        "properties": {"filename": {"type": "string", "description": "Path to the PDF on disk"}},
        "required": ["filename"],
    },
    "handler": tool_extract_invoice,
}

VALIDATE_TOOL = {
    "name": "validate_against_po",
    "description": "Validate invoice fields against a PO repository.",
    "parameters": {
        "type": "object",
        "properties": {
            "po": {"type": "string"},
            "vendor": {"type": "string"},
            "total": {"type": "number"},
        },
        "required": ["po", "total"],
    },
    "handler": tool_validate_against_po,
}

POST_TOOL = {
    "name": "post_to_erp",
    "description": "Post a validated invoice into ERP and return a voucher id.",
    "parameters": {
        "type": "object",
        "properties": {"invoice_id": {"type": "string"}},
        "required": ["invoice_id"],
    },
    "handler": tool_post_to_erp,
}

# --------------------------
# Agents
# --------------------------

AGENT_SYSTEMS = {
    "orchestrator": (
        "You are Mission Control. Your goal is to take an invoice PDF from zero to 'posted'. "
        "Plan the next best step. Call tools indirectly by asking the specialized agents to do the work. "
        "When validation has no deltas, instruct the Poster agent to post. Keep messages crisp and include the exact next call."
    ),
    "extractor": (
        "You extract invoice fields from PDFs using the extract_invoice tool. "
        "Return a compact JSON summary with vendor, invoice_id, purchase_order, invoice_total."
    ),
    "validator": (
        "You validate invoice fields against the PO system using validate_against_po. "
        "If deltas exist, explain briefly; otherwise confirm 'ready_to_post=true'."
    ),
    "poster": (
        "You post validated invoices using post_to_erp and return the voucher_id."
    ),
}

async def main():
    cred = AzureCliCredential()

    client = AzureAIAgentClient(
        credential=cred,
        project_endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
        model_deployment_name=os.environ["AZURE_AI_MODEL_DEPLOYMENT_NAME"],
    )

    # Create or attach to a single Foundry thread so all agents share state
    thread = await client.threads.create()
    print("Thread:", thread.id)

    # Create four agents (Foundry-backed). Toolsets are bound per agent.
    orchestrator = await client.agents.create(
        name="orchestrator",
        instructions=AGENT_SYSTEMS["orchestrator"],
        toolset=[],  # Orchestrator delegates; no direct tools
    )
    extractor = await client.agents.create(
        name="extractor",
        instructions=AGENT_SYSTEMS["extractor"],
        toolset=[EXTRACT_TOOL],     # function calling
    )
    validator = await client.agents.create(
        name="validator",
        instructions=AGENT_SYSTEMS["validator"],
        toolset=[VALIDATE_TOOL],
    )
    poster = await client.agents.create(
        name="poster",
        instructions=AGENT_SYSTEMS["poster"],
        toolset=[POST_TOOL],
    )

    # Seed the thread with a goal
    await client.messages.create(
        thread_id=thread.id,
        role="user",
        content="Goal: Process invoice ./samples/invoices/contoso_invoice.pdf end-to-end."
    )

    # --- Autonomous loop (orchestrator decides the next agent) ---
    # In a production app you might add guards/timeouts; this is a small demo loop.
    for _ in range(8):
        # Let orchestrator think about the next step based on the thread so far
        orch_run = await client.runs.create_and_process(thread_id=thread.id, 
                                                        agent_id=orchestrator.id)

        # Pull the latest assistant message to decide whom to call next (simple heuristic)
        messages = await client.messages.list(thread_id=thread.id, limit=1)
        last = messages.data[0].content[0].text if messages.data else ""
        text = last.strip().lower()

        if "extract" in text or "extractor" in text:
            await client.runs.create_and_process(thread_id=thread.id, agent_id=extractor.id)
        elif "validate" in text or "validator" in text:
            await client.runs.create_and_process(thread_id=thread.id, agent_id=validator.id)
        elif "post" in text or "poster" in text or "ready_to_post" in text:
            await client.runs.create_and_process(thread_id=thread.id, agent_id=poster.id)
            break
        else:
            # If the orchestrator didn’t specify, nudge it
            await client.messages.create(thread_id=thread.id, role="user",
                                         content="Which agent should run next: extractor, validator, or poster? Reply with one word.")
    # Show final thread transcript
    final_messages = await client.messages.list(thread_id=thread.id, limit=50)
    print("\n=== Transcript ===")
    for m in reversed(final_messages.data):
        role = m.role
        text = (m.content[0].text if m.content else "").strip()
        print(f"[{role}] {text[:300]}")

if __name__ == "__main__":
    asyncio.run(main())