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
# Defines the /execute route that accepts both GET and POST requests.

def execute():
    request = Request(flask_request)
    # Wraps the incoming Flask request using the custom Request class to standardize data handling.

    data = request.data
    # Extracts the request payload into a dictionary.

    url = data.get("url", "").strip()
    # Retrieves the "url" field from the request data and removes leading/trailing spaces. Defaults to an empty string.

    extract_query = data.get("extract_query", "").strip()
    # Retrieves the "extract_query" field from the request data and removes leading/trailing spaces. Defaults to an empty string.

    if not url.startswith("http"):
        # Checks if the provided URL is valid (must start with http/https). If not, return a 400 error response.
        return Response(
            data={"error": f"Invalid URL format: {url}"},
            metadata={"affected_rows": 0},
            status_code=400
        )

    try:
        # Attempts to execute the extraction logic using Firecrawl.

        extract_result = firecrawl_client.extract(
            urls=[url],
            prompt=extract_query
        )
        # Calls the Firecrawl `extract` method with the given URL and query prompt.

        return Response(
            data={"result": extract_result.model_dump(exclude_unset=True)},
            metadata={"status": "success"}
        )
        # Returns a successful response with the serialized result from the extract call.

    except Exception as e:
        import traceback
        traceback.print_exc()
        # If any exception occurs, prints the full stack trace for debugging.

        return Response(
            data={"error": str(e)},
            metadata={"affected_rows": 0},
            status_code=500
        )
        # Returns a 500 error response with the exception message and metadata.

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
