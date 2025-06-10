from workflows_cdk import Response, Request
from flask import request as flask_request
from main import router
from firecrawl import FirecrawlApp, JsonConfig
import os
import json
import traceback

# Initialize the Firecrawl client using the API key from environment variables
firecrawl_client = FirecrawlApp(api_key=os.getenv("FIRECRAWL_API_KEY"))


@router.route("/execute", methods=["GET", "POST"])
def execute():
    request = Request(flask_request)
    data = request.data

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

    # Optional: define schema for extracted data
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
        batch_result = firecrawl_client.batch_scrape_urls(
        urls=urls,  # List of URLs to scrape
        formats=formats,  # List of output formats (e.g. markdown, screenshot, json)
        json_options=json_options,  # Optional structured extraction with prompt and schema

        # Webhook configuration to receive real-time updates for the job
        webhook={
            "url": "https://7908-79-127-185-164.ngrok-free.app/batch_scrape/v1/webhook",  # Your webhook endpoint that Firecrawl will POST to
            "metadata": {"source": "batch_ui"},  # Custom metadata to identify or filter jobs
            "events": ["started", "page", "completed", "failed"]  # List of events to subscribe to

            # Note: The structure and supported fields of this webhook object
            # are defined by Firecrawl's API documentation and may vary depending
            # on the provider's requirements. Always refer to the latest docs.
        }
    )
        # print("line52",batch_result)
        # print("type",type(batch_result))
        # print("dir",dir(batch_result))
        # print("data",batch_result.data)
        outputs = []
        for res in batch_result.data:
            # print("line57 res", res)
            outputs.append({
                "url": res.url if hasattr(res, "url") else "unknown",
                "result": res.model_dump(exclude_unset=True)
            })

        # print("outputs", outputs)
        return Response(data=outputs, metadata={"status": "success"})

    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response(data={"error": str(e)}, metadata={}, status_code=500)

# Define the webhook endpoint that will receive POST requests from Firecrawl
@router.route("/webhook", methods=["POST"])
def firecrawl_webhook():
    request = Request(flask_request)  # Wrap the incoming Flask request
    payload = request.data  # Extract the JSON payload from the request

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
def handle_webhook_event(payload):
    event_type = payload.get("event")  # The type of event, such as 'started' or 'page'
    job_id = payload.get("jobId")  # Unique ID for the scraping job
    data = payload.get("data", {})  # Additional data related to the event, if available

    # Handle each event type accordingly
    if event_type == "batch_scrape.started":
        print(f"Scrape started for job {job_id}")  # Log when the batch scrape starts
    elif event_type == "batch_scrape.page":
        print(f"Page scraped: {data.get('url')}")  # Log each individual page scraped
    elif event_type == "batch_scrape.completed":
        print(f"Scrape complete for job {job_id}")  # Log when all pages are scraped
    elif event_type == "batch_scrape.failed":
        print(f"Scrape failed for job {job_id}")  # Log if the scraping job fails
    else:
        print(f"Unknown event type: {event_type}")  # Handle any unrecognized event types


# @router.route("/content", methods=["GET", "POST"])
# def content():
#     """
#     This is the function that goes and fetches the necessary data to populate the possible choices in dynamic form fields.
#     For example, if you have a module to delete a contact, you would need to fetch the list of contacts to populate the dropdown
#     and give the user the choice of which contact to delete.

#     An action's form may have multiple dynamic form fields, each with their own possible choices. Because of this, in the /content route,
#     you will receive a list of content_object_names, which are the identifiers of the dynamic form fields. A /content route may be called for one or more content_object_names.

#     Every data object takes the shape of:
#     {
#         "value": "value",
#         "label": "label"
#     }
    
#     Args:
#         data:
#             form_data:
#                 form_field_name_1: value1
#                 form_field_name_2: value2
#             content_object_names:
#                 [
#                     {   "id": "content_object_name_1"   }
#                 ]
#         credentials:
#             connection_data:
#                 value: (actual value of the connection)

#     Return:
#         {
#             "content_objects": [
#                 {
#                     "content_object_name": "content_object_name_1",
#                     "data": [{"value": "value1", "label": "label1"}]
#                 },
#                 ...
#             ]
#         }
#     """
#     request = Request(flask_request)

#     data = request.data

#     form_data = data.get("form_data", {})
#     content_object_names = data.get("content_object_names", [])
    
#     # Extract content object names from objects if needed
#     if isinstance(content_object_names, list) and content_object_names and isinstance(content_object_names[0], dict):
#         content_object_names = [obj.get("id") for obj in content_object_names if "id" in obj]

#     content_objects = [] # this is the list of content objects that will be returned to the frontend

#     for content_object_name in content_object_names:
#         if content_object_name == "requested_content_object_1":
#             # logic here
#             data = [
#                 {"value": "value1", "label": "label1"},
#                 {"value": "value2", "label": "label2"}
#             ]
#             content_objects.append({
#                     "content_object_name": "requested_content_object_1",
#                     "data": data
#                 })
#         elif content_object_name == "requested_content_object_2":
#             # logic here
#             data = [
#                 {"value": "value1", "label": "label1"},
#                 {"value": "value2", "label": "label2"}
#             ]
#             content_objects.append({
#                     "content_object_name": "requested_content_object_2",
#                     "data": data
#                 })
    
#     return Response(data={"content_objects": content_objects})
