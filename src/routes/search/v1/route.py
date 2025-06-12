from workflows_cdk import Response, Request
from flask import request as flask_request
from main import router
from firecrawl import FirecrawlApp, ScrapeOptions
from src.forms import SearchForm
import os
import json
import traceback

# Initialize the Firecrawl client using the API key from environment variables
firecrawl_client = FirecrawlApp(api_key=os.getenv("FIRECRAWL_API_KEY"))

@router.route("/execute", methods=["POST"])
def execute():
    """
    Search the web and get full content from results.
    """
    request = Request(flask_request)
    data = request.data

    # Validate incoming data using SearchForm
    form = SearchForm(data=data)

    if not form.validate():
        # print("Form validation failed:", form.errors)  
        return Response(
            data={"error": "Invalid input", "details": form.errors},
            metadata={"affected_rows": 0},
            status_code=400
        )


    # Extract values from data after validation
    search_query = form.prompt.data
    # search_query = form.data("prompt")
    include_markdown = form.include_markdown.data
    html_type = form.html_type.data or ""
    include_links = form.include_links.data
    screenshot_type = form.screenshot_type.data or ""
    language_type = form.lang.data or ""
    country_type = form.country.data or ""
    time_filter = form.tbs.data or ""

    formats = []
    if include_markdown:
        formats.append("markdown")
    if include_links:
        formats.append("links")
    if screenshot_type == "Standard Screenshot":
        formats.append("screenshot")
    elif screenshot_type == "Full Page Screenshot":
        formats.append("screenshot@fullPage")
    if html_type == "Clean HTML":
        formats.append('html')
    elif html_type == "Raw HTML":
        formats.append("rawHtml")

    language_map = {
        "English": "en",
        "Français": "fr",
        "Español": "es",
        "中文": "zh"
    }
    country_map = {
        "United States": "us",
        "France": "fr",
        "Mexico": "mx",
        "中国": "cn"
    }
    time_filter_map = {
        "Past hour": "qdr:h",
        "Past day": "qdr:d",
        "Past week": "qdr:w",
        "Past month": "qdr:m",
        "Past year": "qdr:y"
    }

    language_code = language_map.get(language_type)
    country_code = country_map.get(country_type)
    time_filter_args = time_filter_map.get(time_filter)

    search_kwargs = {
        "query": search_query,
        "limit": 5
    }

    if formats:
        search_kwargs["scrape_options"] = ScrapeOptions(formats=formats)
    if language_code:
        search_kwargs["lang"] = language_code
    if country_code:
        search_kwargs["country"] = country_code
    if time_filter_args:
        search_kwargs["tbs"] = time_filter_args

    print("search_kwargs", search_kwargs)
    try:
        search_results = firecrawl_client.search(**search_kwargs)
        result_data = search_results.model_dump(exclude_unset=True)
        return Response(data=result_data, metadata={"status": "success"})

    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response(
            data={"error": str(e)},
            metadata={"affected_rows": 0},
            status_code=500
        )

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
