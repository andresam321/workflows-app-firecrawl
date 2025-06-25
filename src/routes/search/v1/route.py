from workflows_cdk import Response, Request
from flask import request as flask_request
from main import router
from firecrawl import FirecrawlApp, ScrapeOptions
from src.forms import SearchForm
import os
import json
import traceback

# search_results_object = {
#     "latest": []
# }
# Initialize the Firecrawl client using the API key from environment variables
# print("search res object", search_results_object)
firecrawl_client = FirecrawlApp(api_key=os.getenv("FIRECRAWL_API_KEY"))

@router.route("/execute", methods=["POST", "GET"])
def execute():
    """
    Search the web and get full content from results.
    """
    request = Request(flask_request)
    data = request.data
    print("line20", data)
    # Validate incoming data using SearchForm
    form = SearchForm(data=data)

    if not form.validate():
        # print("Form validation failed:", form.errors)  
        return Response(
            data={"error": "Invalid input", "details": form.errors},
            metadata={"affected_rows": 0},
            status_code=400
        )
    selected_page = data.get("search_results")
    print("selected page", selected_page)

    # Part 1: User selected a page from dropdown
    # if isinstance(selected_page, dict):
    #     selected_url = selected_page.get("url")

        # Reuse a previous crawl
        # if selected_url and selected_url != "None":
        #     stored_results = search_results_object.get("latest", [])
        #     matched = next(
        #         (r for r in stored_results if r.get("url") == selected_url),
        #         None
        #     )
        #     if not matched:
        #         return Response(data={"error": "Selected page not found"}, status_code=404)

        #     return Response(
        #         data={"selected_page": matched},
        #         metadata={"status": "page_selected"}
        #     )

        # # If user selected "None", crawl fresh
        # elif selected_url == "None":
        #     print("User selected None, performing new crawl...")

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
        "limit": 1
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
        # search_results_object["latest"] = result_data.get("data", [])
        return Response(data=result_data, metadata={"status": "success"})

    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response(
            data={"error": str(e)},
            metadata={"affected_rows": 0},
            status_code=500
        )

@router.route("/content", methods=["GET", "POST"])
def content():
    request = Request(flask_request)
    data = request.data

    form_data = data.get("form_data", {})
    content_object_names = data.get("content_object_names", [])
    # print("Form Data:", form_data)
    # print("Requested content_object_names:", content_object_names)

    # Flatten structure if it's a list of dicts
    if isinstance(content_object_names, list) and content_object_names and isinstance(content_object_names[0], dict):
        content_object_names = [obj.get("id") for obj in content_object_names if "id" in obj]

    content_objects = []

    for content_object_name in content_object_names:
        if content_object_name == "html_format_options":
            data = [
                {"value": "None", "label": "None"},
                {"value": "Clean HTML", "label": "Clean HTML"},
                {"value": "Raw HTML", "label": "Raw HTML"}
            ]
            content_objects.append({
                "content_object_name": "html_format_options",
                "data": data
            })

        if content_object_name == "screenshot_format_options":
            data = [
                {"value": "None", "label": "None"},
                {"value": "Standard Screenshot", "label": "Standard Screenshot"},
                {"value": "Full Page Screenshot", "label": "Full Page Screenshot"}
            ]
            content_objects.append({
                "content_object_name": "screenshot_format_options",
                "data": data
            })

        if content_object_name == "time_filter_options":
            content_objects.append({
                "content_object_name": "time_filter_options",
                "data": [
                    {"value": "Past hour", "label": "Past hour"},
                    {"value": "Past day", "label": "Past day"},
                    {"value": "Past week", "label": "Past week"},
                    {"value": "Past month", "label": "Past month"},
                    {"value": "Past year", "label": "Past year"}
                ]
            })

        if content_object_name == "country_options":
            content_objects.append({
                "content_object_name": "country_options",
                "data": [
                    {"value": "United States", "label": "United States"},
                    {"value": "France", "label": "France"},
                    {"value": "Mexico", "label": "Mexico"},
                    {"value": "中国", "label": "中国"}
                ]
            })

        if content_object_name == "language_options":
            content_objects.append({
                "content_object_name": "language_options",
                "data": [
                    {"value": "English", "label": "English"},
                    {"value": "Français", "label": "Français"},
                    {"value": "Español", "label": "Español"},
                    {"value": "中文", "label": "中文"}
                ]
            })
        # if content_object_name == "search_results":
        #     results = search_results_object.get("latest", [])

        #     dropdown_options = [{
        #         "value": {
        #                 "id": "None",
        #                 "label": "None"
        #             },
        #         "label": "None"
        #     }]

        #     if "lookup" not in search_results_object:
        #         search_results_object["lookup"] = {}

        #     for item in results:
        #         # print("line226 item", item)
        #         metadata = item.get("metadata", {})
        #         title = item.get("title", "Untitled Page").strip()
        #         url = item.get("url", "No URL")
        #         description = item.get("description")
                
        #         # print("url", url)

        #         dropdown_options.append({
        #             "value": {
        #                 "url": url,
        #                 "label": title,
                        
        #                 },
        #             "label": f"{title} ({url})"
        #         })
        #         search_results_object["lookup"][url] = {
        #                 "meta": {
        #                     "label": title,
        #                     "url": url,
        #                     "description": description,

        #                 },
        #                 "formats": {
        #                     "markdown": item.get("markdown"),
        #                     "rawHtml": item.get("rawHtml"),
        #                     "screenshot": item.get("screenshot")
        #                 }
        #             }
        #     content_objects.append({
        #         "content_object_name": "search_results",
        #         "data": dropdown_options
        #     })
        #     print("content_objects", content_objects)

    return Response(data={"content_objects": content_objects})
