from workflows_cdk import Response, Request
from flask import request as flask_request
from main import router
from firecrawl import FirecrawlApp, JsonConfig
import os
import json
import traceback

scrape_results_object = {
    "latest": []
}
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
    # print(f"Received URL to scrape: {url}")

    if not url.startswith("http"):
        return Response(
            data={"error": f"Invalid URL format: {url}"},
            metadata={"affected_rows": 0},
            status_code=400
        )
    
    selected_page = data.get("format_options")
    # print("selected page", selected_page)
    # Part 1: User selected a page from dropdown
    if isinstance(selected_page, dict):
        selected_id = selected_page.get("id")

        # find format idk
        if selected_id and selected_id != "None":
            stored_results = scrape_results_object.get("lookup", [])
            matched = stored_results.get(selected_id)

            if not matched:
                return Response(data={"error": "Selected page not found, start a new scrape"}, status_code=404)

            return Response(
                data={"selected_page": matched},
                metadata={"status": "page_selected"}
            )

        # If user selected "None", scrape fresh
        elif selected_id == "None":
            print("User selected None, performing new crawl...")

    screenshot_type = data.get("screenshot_type", "")
    html_type = data.get("html_type", "")
    extracted_markdown = data.get("extract_markdown", False)
    extract_links = data.get("extract_links", False)
    extract_json = data.get("extract_json", False)
    prompt = data.get("extract_prompt", "").strip()

    json_options = None
    formats = []
    if extracted_markdown:
        formats.append("markdown")
    if extract_links:
        formats.append("links")
    if screenshot_type == "Standard Screenshot":
        formats.append("screenshot")
    elif screenshot_type == "Full Page Screenshot":
        formats.append("screenshot@fullPage")
    if html_type == "Clean HTML":
        formats.append('html')
    elif html_type == "Raw HTML":
        formats.append("rawHtml")
    if extract_json:
        formats.append("json")
        if prompt:
            json_options = JsonConfig(prompt=prompt)
        else:
            return Response(
                data={"error": "Prompt is required for JSON extraction."},
                metadata={"status": "failed"},
                status_code=400
        )


    # print(f"Formats to scrape: {formats}")
    # print(f"Calling Firecrawl's scrape_url with URL: {url}, formats: {formats}")

    try:
        # Call Firecrawl and return JSON-safe data
        scrape_result = firecrawl_client.scrape_url(
            url=url,
            formats=formats,
            json_options=json_options
        )

        format_labels = {
            "markdown": "Markdown",
            "html": "Clean HTML",
            "rawHtml": "Raw HTML",
            "screenshot": "Screenshot",
            "screenshot@fullPage": "Full Page Screenshot",
            "links": "Links",
            "json": "JSON"
        }


        # Clean JSON response from Pydantic v2
        result_data = scrape_result.model_dump(exclude_unset=True)
        scrape_results_object["latest"] = result_data
        # print("scrape results",scrape_results_object["latest"] )
        outputs = []
        for format_key, content in result_data.items():
            # print("line80",format_key)
            outputs.append({
                "type": format_key,
                "description": format_labels.get(format_key, ""),
                "content": content
        })
        # print("individual_outputs", outputs)
        metadata_block = next((item for item in outputs if item.get("type") == "metadata"), None)

        if metadata_block:
            metadata_content = metadata_block.get("content", {})
            status_code = metadata_content.get("statusCode", 200)
            if status_code != 200:
                return Response(
                    data={"error": f"Scrape failed with status code {status_code}. The site may have blocked the request."},
                    metadata={"status": "scrape_failed"},
                    status_code=502
                )
        return Response(data={"output":outputs}, metadata={"status": "success"})

    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response(data={"error": str(e)},metadata={"affected_rows": 0},status_code=500)


@router.route("/content", methods=["POST","GET"])
def content():
    request = Request(flask_request)
    data = request.data
    # print("data",data )
    form_data = data.get("form_data", {})
    # print("form data",form_data)
    markdown = form_data.get("markdown", [])  # This is what was selected in the scrape step
    # print("markdown ", markdown)
    content_object_names = data.get("content_object_names", [])
    if isinstance(content_object_names, list) and content_object_names and isinstance(content_object_names[0], dict):
        content_object_names = [obj.get("id") for obj in content_object_names if "id" in obj]
    # print("content object name", content_object_names)

    content_objects = []
    label_map = {
        "markdown": "Markdown",
        "rawHtml": "Raw HTML",
        "html": "Clean HTML",
        "json": "JSON",
        "links": "Links",
        "screenshot": "Screenshot",
        "screenshot@fullPage": "Full Page Screenshot",
        "metadata": "Metadata"
    }

    for content_object_name in content_object_names:
        # print("content object name", content_object_name)
        if content_object_name == "format_options":
            result_data = scrape_results_object.get("latest", {})
            if not isinstance(result_data, dict):
                result_data = {}
            # print("result dataaaaaaaa", result_data)
            dropdown_options = [{
                "value": {"id": "None", "label": "None"},
                "label": "None"
            }]
            
            scrape_results_object["lookup"] = {}

            for key, content in result_data.items():
                # print("line 186", key)
                if content:
                    readable_label = label_map.get(key, key)
                    # print("readable lable", readable_label)
                    dropdown_options.append({
                        "value": {"id": key, "label": readable_label},
                        "label": readable_label
                    })
                    scrape_results_object["lookup"][key] = {
                        "meta": {
                            "format": key,
                            "content": content,
                        }
                    }

            content_objects.append({
                "content_object_name": "format_options",
                "data": dropdown_options
            })


    return Response(data={"content_objects": content_objects})
