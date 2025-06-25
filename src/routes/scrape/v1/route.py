from workflows_cdk import Response, Request
from flask import request as flask_request
from main import router
from firecrawl import FirecrawlApp, JsonConfig
import os
import json
import traceback
import requests


# Initialize the Firecrawl client using the API key from environment variables

firecrawl_client = FirecrawlApp(api_key=os.getenv("FIRECRAWL_API_KEY"))

# print("🚀 scrape.py was loaded")
@router.route("/test", methods=["GET"])
def test_router():
    return {"router": "working"}, 200

@router.route("/execute", methods=["GET", "POST"])
def execute():
    """
    Triggered when the workflow runs the Scrape module.
    Scrapes a given URL and optionally returns markdown and screenshot data.
    """
    request = Request(flask_request)
    data = request.data

    url = data.get("url", "").strip()
    # print(f"Received URL to scrape: {url}")

    if not url.startswith("http"):
        return Response(
            data={"error": f"Invalid URL format: {url}"},
            metadata={"affected_rows": 0},
            status_code=400
        )
    format_mapping = {
        "Markdown": "markdown",
        "Clean HTML": "html",
    }
    selected_format_label = data.get("formats", "None")
    print("line40", selected_format_label)
    screenshot_type = data.get("screenshot_type", "")
    html_type = data.get("html_type", "")
    extracted_markdown = data.get("extract_markdown", False)
    extract_links = data.get("extract_links", False)
    extract_json = data.get("extract_json", False)
    prompt = data.get("extract_prompt", "").strip()
    main_format = format_mapping.get(selected_format_label, "markdown")

# Check if JSON is empty or lists are empty
    

    formats = []
    if main_format:
        formats.append(main_format)
    if extract_links:
        formats.append("links")
    if screenshot_type == "Standard Screenshot":
        formats.append("screenshot")
    elif screenshot_type == "Full Page Screenshot":
        formats.append("screenshot@fullPage")
    if prompt:
        formats.append("json")
        json_options = JsonConfig(prompt=prompt)
    elif extract_json:
        formats.append("json")
        json_options = JsonConfig(prompt="")  # or some default if needed
    else:
        json_options = None

    # print("SCRAPE DEBUG: json_options =", json_options.model_dump() if json_options else None)

    # print("SCRAPE DEBUG: Formats =", formats)
    # print("SCRAPE DEBUG: JSON Prompt =", prompt)
    # print(f"Formats to scrape: {formats}")
    # print(f"Calling Firecrawl's scrape_url with URL: {url}, formats: {formats}")

    try:
        # Call Firecrawl and return JSON-safe data
        scrape_result = firecrawl_client.scrape_url(
            url=url,
            formats=formats,
            json_options=json_options
        )

        # Clean JSON response from Pydantic v2
        result_data = scrape_result.model_dump(exclude_unset=True)
        json_data = result_data.get("json", {})
        if not json_data or all(isinstance(v, list) and len(v) == 0 for v in json_data.values()):
        # Replace with a meaningful message or default
            result_data["json"] = {"message": "No data found matching the prompt."}
        # print("result_data", result_data)
        return Response(data={"output":result_data}, metadata={"status": "success"})
    
    except requests.exceptions.HTTPError as http_err:
        # Return a clear error message to the user
        return Response(
            data={"error": "Scraping failed. The target site may block automated requests or the URL is invalid."},
            metadata={"status": "scrape_failed"},
            status_code=502
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response(data={"error": str(e)},metadata={"affected_rows": 0},status_code=500)


# @router.route("/content", methods=["POST","GET"])
# def content():
#     request = Request(flask_request)
#     data = request.data
#     # print("data",data )
#     form_data = data.get("form_data", {})
#     # print("form data",form_data)
#     markdown = form_data.get("markdown", [])  # This is what was selected in the scrape step
#     # print("markdown ", markdown)
#     content_object_names = data.get("content_object_names", [])
#     if isinstance(content_object_names, list) and content_object_names and isinstance(content_object_names[0], dict):
#         content_object_names = [obj.get("id") for obj in content_object_names if "id" in obj]
#     # print("content object name", content_object_names)

#     content_objects = []
#     label_map = {
#         "markdown": "Markdown",
#         "rawHtml": "Raw HTML",
#         "html": "Clean HTML",
#         "json": "JSON",
#         "links": "Links",
#         "screenshot": "Screenshot",
#         "screenshot@fullPage": "Full Page Screenshot",
#         "metadata": "Metadata"
#     }

#     for content_object_name in content_object_names:
#         # print("content object name", content_object_name)
#         if content_object_name == "format_options":
#             result_data = scrape_results_object.get("latest", {})
#             if not isinstance(result_data, dict):
#                 result_data = {}
#             # print("result dataaaaaaaa", result_data)
#             dropdown_options = [{
#                 "value": {"id": "None", "label": "None"},
#                 "label": "None"
#             }]
            
#             scrape_results_object["lookup"] = {}

#             for key, content in result_data.items():
#                 # print("line 186", key)
#                 if content:
#                     readable_label = label_map.get(key, key)
#                     # print("readable lable", readable_label)
#                     dropdown_options.append({
#                         "value": {"id": key, "label": readable_label},
#                         "label": readable_label
#                     })
#                     scrape_results_object["lookup"][key] = {
#                         "meta": {
#                             "format": key,
#                             "content": content,
#                         }
#                     }

#             content_objects.append({
#                 "content_object_name": "format_options",
#                 "data": dropdown_options
#             })


#     return Response(data={"content_objects": content_objects})
