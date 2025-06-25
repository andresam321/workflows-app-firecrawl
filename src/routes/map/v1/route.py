from workflows_cdk import Response, Request
from flask import request as flask_request
from main import router
from firecrawl import FirecrawlApp
import os
import json
import traceback


firecrawl_client = FirecrawlApp(api_key=os.getenv("FIRECRAWL_API_KEY"))

@router.route("/execute", methods=["GET", "POST"])
def execute():
    """
    Triggered when the workflow runs the Map module.
    Input a website and get all the urls on the website - extremely fast.
    """
    request = Request(flask_request)
    data = request.data

    url = data.get("url", "").strip()
    search_term = data.get("search_term", "").strip().lower()


    if not url.startswith("http"):
        return Response(
            data={"error": f"Invalid URL format: {url}"},
            metadata={"affected_rows": 0},
            status_code=400
        )

    try:

        scrape_result = firecrawl_client.map_url(
            url=url,
            search=search_term if search_term else None
        )

        # Parse and store results
        result_data = scrape_result.model_dump(exclude_unset=True)
        # print("line78", result_data)
        links = result_data.get("links", [])


        return Response(
            data={"links": links},
            metadata={
                "status": "fresh_scrape",
                "affected_rows": len(result_data.get("links", []))
            }
        )

    except Exception as e:
        traceback.print_exc()
        return Response(
            data={"error": str(e)},
            metadata={"status": "error"},
            status_code=500
        )


# @router.route("/content", methods=["POST", "GET"])
# def content():
#     """
#     Provide dynamic content for the module UI.
#     Handles map results dropdown with page titles.
#     """
#     try:
#         request = Request(flask_request)
#         data = request.data

#         if not data:
#             return Response(data={"message": "Missing request data"}, status_code=400)

#         form_data = data.get("form_data", {})
#         print("form_data", form_data)
#         content_object_names = data.get("content_object_names", [])

#         if isinstance(content_object_names, list) and content_object_names and isinstance(content_object_names[0], dict):
#             content_object_names = [obj.get("id") for obj in content_object_names if "id" in obj]

#         content_objects = []

#         for content_name in content_object_names:
#             if content_name == "map_results":
#                 # Ensure memory is populated before filtering
#                 results = map_results_object.get("latest", {})
#                 all_links = results

#                 if not all_links:
#                     return Response(
#                         data={"message": "No links available. Run the Map action by selecting 'None' first."},
#                         status_code=400
#                     )

#                 # Optional filtering using the search term
#                 search_term = form_data.get("search_term", "").strip().lower()
#                 if search_term:
#                     filtered_links = [link for link in all_links if search_term in link.lower()]
#                 else:
#                     filtered_links = all_links

#                 dropdown_options = [{
#                     "value": {
#                         "url": "None"
#                     },
#                     "label": "None"
#                 }]

#                 for url in list(filtered_links.keys())[:25]:
#                     dropdown_options.append({
#                         "value": {"url": url},
#                         "label": url[:100] + "..." if len(url) > 100 else url
#                     })

#                 # Store to lookup for later (optional, depending on your implementation)
#                 if "lookup" not in map_results_object:
#                     map_results_object["lookup"] = {}
#                 for url in filtered_links[:25]:
#                     map_results_object["lookup"][url] = {"meta": {"url": url}}

#                 content_objects.append({
#                     "content_object_name": "map_results",
#                     "data": dropdown_options
#                 })

#         return Response(data={"content_objects": content_objects})
#     except Exception as e:
#         import traceback
#         traceback.print_exc()
#         return Response(
#             data={"error": str(e)},
#             metadata={"status": "content_error"},
#             status_code=500
#         )
