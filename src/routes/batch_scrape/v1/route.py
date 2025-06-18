from workflows_cdk import Response, Request
from flask import request as flask_request
from main import router
from firecrawl import FirecrawlApp, JsonConfig
import os
import json
import traceback


# batch_scrape_jobs = {
#     "jobs": []  
# }
webhook_storage = {}
# Initialize the Firecrawl client using the API key from environment variables
firecrawl_client = FirecrawlApp(api_key=os.getenv("FIRECRAWL_API_KEY"))


@router.route("/execute", methods=["GET", "POST"])
def execute():
    request = Request(flask_request)
    data = request.data

    selected_page = data.get("batch_scrape_results")
    print("selected_page", selected_page)
    selected_id = selected_page.get("id") if isinstance(selected_page, dict) else None
    print("selected_data", selected_page)
    # Case 1: User selects existing job_id|url to check status
            
    if selected_id and "|" in selected_id:
        job_id, selected_url = selected_id.split("|", 1)

        print("Looking for key:", f"{job_id}|{selected_url}")
        print("Available keys in webhook_storage:")
        for key in webhook_storage.keys():
            if key.startswith(job_id):
                print("-", key)
        try:
            data = webhook_storage.get(f"{job_id}|{selected_url}")
            if data is not None:
                print("line34", data)
                return Response(data={"selected_page": data}, metadata={"status": "page_selected"})

            return Response(data={"error": "Job is not completed yet."}, status_code=202)

        except Exception as e:
            return Response(data={"error": f"Error loading job: {str(e)}"}, status_code=500)

    # Case 2: User selects "None" — Start a new batch scrape
    elif selected_id == "None":
        urls = data.get("urls", [])
        screenshot = data.get("screenshot", False)
        extracted_markdown = data.get("extractMarkdown", False)
        extraction_prompt = data.get("extraction_prompt", "").strip()

        formats = []
        if extracted_markdown:
            formats.append("markdown")
        if screenshot:
            formats.append("screenshot")
        if extraction_prompt:
            formats.append("json")

        json_options = None
        if extraction_prompt:
            json_options = {
                "prompt": extraction_prompt,
                "schema": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "description": {"type": "string"}
                    },
                    "required": ["title", "description"]
                }
            }

        try:
            batch_result = firecrawl_client.async_batch_scrape_urls(
                urls=urls,
                formats=formats,
                json_options=json_options,
                webhook={
                    "url": "https://6a99-146-70-174-252.ngrok-free.app/batch_scrape/v1/webhook",
                    "metadata": {"source": "batch_ui"},
                    "events": ["started", "page", "completed", "failed"]
                }
            )

            label = extraction_prompt[:40] + "..." if len(extraction_prompt) > 40 else extraction_prompt

            # batch_scrape_jobs["jobs"].append({
            #     "job_id": batch_result.id,
            #     "label": label,
            #     "urls": urls
            # })

            return Response(data={"message": "Batch job submitted", "job_id": batch_result.id, "label": label}, metadata={"status": "submitted"})

        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response(data={"error": str(e)}, metadata={}, status_code=500)

    else:
        return Response(data={"error": "Invalid selection or missing ID."}, status_code=400)

# Define the webhook endpoint that will receive POST requests from Firecrawl
@router.route("/webhook", methods=["POST"])
def firecrawl_webhook():
    payload = flask_request.get_json(force=True) 

    # If Firecrawl sends a list of events (batched), handle each event individually
    if isinstance(payload, list):
        for event in payload:
            handle_webhook_event(event)
    # If Firecrawl sends a single event as a dictionary, handle it directly
    elif isinstance(payload, dict):
        handle_webhook_event(payload)
    # Catch any unexpected or malformed payloads
    else:
        print("Unrecognized webhook payload:", payload)

    # Respond to Firecrawl with a 200 OK and a simple confirmation message
    return Response(data={"received": True}, metadata={"status": "ok"})


# This function handles individual webhook events sent from Firecrawl
# Global storage


def handle_webhook_event(payload):
    event_type = payload.get("type")
    job_id = payload.get("id")
    data = payload.get("data", {})

    if event_type == "batch_scrape.started":
        print(f"Scrape started for job {job_id}")
        webhook_storage[job_id] = []

    elif event_type == "batch_scrape.page":
        if job_id not in webhook_storage:
            webhook_storage[job_id] = []

        if isinstance(data, list):
            for item in data:
                url = item.get("metadata", {}).get("url")
                if url:
                    webhook_storage[f"{job_id}|{url}"] = item
        elif isinstance(data, dict):
            url = data.get("metadata", {}).get("url")
            if url:
                webhook_storage[f"{job_id}|{url}"] = data
        else:
            print(f"Unexpected data format for batch_scrape.page: {data}")

    elif event_type == "batch_scrape.completed":
        print(f"Scrape complete for job {job_id}")

        if isinstance(data, list):
            for item in data:
                url = item.get("metadata", {}).get("url")
                if url:
                    webhook_storage[f"{job_id}|{url}"] = item
        elif isinstance(data, dict):
            url = data.get("metadata", {}).get("url")
            if url:
                webhook_storage[f"{job_id}|{url}"] = data

    elif event_type == "batch_scrape.failed":
        print(f"Scrape failed for job {job_id}")
    else:
        print(f"Unknown event type: {event_type}")




@router.route("/content", methods=["POST", "GET"])
def content():
    request = Request(flask_request)
    data = request.data
    content_object_names = data.get("content_object_names", [])
    
    if isinstance(content_object_names, list) and content_object_names and isinstance(content_object_names[0], dict):
        content_object_names = [obj.get("id") for obj in content_object_names if "id" in obj]

    content_objects = []
    print("content_object_name", content_object_names)
    if "batch_scrape_results" in content_object_names:
        dropdown_options = [{
            "value": {"id": "None", "label": "None"},
            "label": "None"
        }]

        for key in webhook_storage:
            if "|" in key:
                job_id, url = key.split("|", 1)
                dropdown_options.append({
                    "value": {"id": key, "label": url},
                    "label": f"{url} ({job_id[:6]})"
                })


        content_objects.append({
            "content_object_name": "batch_scrape_results",
            "data": dropdown_options
        })

    return Response(data={"content_objects": content_objects})
