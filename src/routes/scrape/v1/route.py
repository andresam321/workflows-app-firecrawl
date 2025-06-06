from workflows_cdk import Response, Request
from flask import request as flask_request
from main import router
from firecrawl import FirecrawlApp, ScrapeOptions
import os
import json
import traceback

# Initialize the Firecrawl client using the API key from environment variables
firecrawl_client = FirecrawlApp(api_key=os.getenv("FIRECRAWL_API_KEY"))

@router.route("/execute", methods=["GET", "POST"])
def execute():
    """
    Triggered when the workflow runs the Scrape module.
    Scrapes a given URL and optionally returns markdown and screenshot data.
    """
    request = Request(flask_request)
    data = request.data

    url = data.get("url", "").strip()
    print(f"Received URL to scrape: {url}")

    if not url.startswith("http"):
        return Response(
            data={"error": f"Invalid URL format: {url}"},
            metadata={"affected_rows": 0},
            status_code=400
        )

    screenshot = data.get("screenshot", False)
    extracted_markdown = data.get("extractMarkdown", False)
    extracted_structured = data.get("extractStructuredData", False)  # Not used here, safely ignored

    formats = []
    if extracted_markdown:
        formats.append("markdown")
    if screenshot:
        formats.append("screenshot")
    # if extracted_structured:
    #     formats.append("extract")

    # options = {}
    # if extracted_structured:
    #     options["extract"] = {"type": "default"}


    print(f"Calling Firecrawl's scrape_url with URL: {url}, formats: {formats}")

    try:
        # Call Firecrawl and return JSON-safe data
        scrape_result = firecrawl_client.scrape_url(
            url=url,
            formats=formats,
            # options=options if options else None
        )

        # Clean JSON response from Pydantic v2
        result_data = scrape_result.model_dump(exclude_unset=True)

        return Response(data=result_data, metadata={"status": "success"})

    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response(data={"error": str(e)},metadata={"affected_rows": 0},status_code=500)


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
