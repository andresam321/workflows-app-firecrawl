from workflows_cdk import Response, Request
from flask import request as flask_request
from main import router
from firecrawl import FirecrawlApp, ScrapeOptions
import os
import json
import requests
import builtins
crawl_results_store = {
    "latest": []  # This should be updated from your crawl logic
}
print("crawl_results_store location:", id(crawl_results_store))
# Initialize the Firecrawl client using the API key from environment variables
firecrawl_client = FirecrawlApp(api_key=os.getenv("FIRECRAWL_API_KEY"))


@router.route("/execute", methods=["POST", "GET"])
def execute():
    """
    Crawl
    Firecrawl can recursively search through a URL’s subdomains and gather the content.
    """
    request = Request(flask_request)
    data = request.data
    form_data = data.get("form_data", {})

    url = data.get("url", "").strip()
    if not url.startswith("http"):
        return Response(
            data={"error": f"Invalid URL format: {url}"},
            metadata={"affected_rows": 0},
            status_code=400
        )

    selected_page = form_data.get("crawl_results")

    # 🟡 Part 1: User selected a page (second submission)
    if selected_page and selected_page.strip().lower() != "None":
        stored_results = crawl_results_store.get("latest", [])
        matched = next(
            (r for r in stored_results if r["metadata"].get("title", "").strip() == selected_page.strip()), 
            None
        )

        if not matched:
            return Response(data={"error": "Selected page not found"}, status_code=404)

        return Response(
            data={"selected_page": matched},
            metadata={"status": "page_selected"}
        )

    # 🔵 Part 2: First run — Firecrawl + populate store
    limit = int(data.get("limit", 5))
    allowed_backward_links = data.get("allowed_backward_links")
    print("line56",allowed_backward_links)
    include_markdown = data.get("include_markdown")
    html_type = data.get("html_type")
    screenshot_type = data.get("screenshot_type")

    formats = []
    if include_markdown:
        formats.append("markdown")
    if screenshot_type == "Standard Screenshot":
        formats.append("screenshot")
    elif screenshot_type == "Full Page Screenshot":
        formats.append("screenshot@fullPage")
    if html_type == "Clean HTML":
        formats.append("html")
    elif html_type == "Raw HTML":
        formats.append("rawHtml")

    crawl_kwargs = {"url": url, "limit": limit}
    if allowed_backward_links is not None:
        crawl_kwargs["allow_backward_links"] = allowed_backward_links
    if formats:
        crawl_kwargs["scrape_options"] = ScrapeOptions(formats=formats)

    try:
        crawl_results = firecrawl_client.crawl_url(**crawl_kwargs)
        result_data = crawl_results.model_dump(exclude_unset=True)
        crawl_results_store["latest"] = result_data.get("data", [])
        return Response(
            data=result_data,
            metadata={"status": "crawl_complete"}
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response(
            data={"error": str(e)},
            metadata={"affected_rows": 0},
            status_code=500
        )



@router.route("/content", methods=["POST"])
def content():
    from flask import request as flask_request
    request = Request(flask_request)
    data = request.data

    form_data = data.get("form_data", {})
    content_object_names = data.get("content_object_names", [])
    print("line105", content_object_names)

    if isinstance(content_object_names, list) and content_object_names and isinstance(content_object_names[0], dict):
        content_object_names = [obj.get("id") for obj in content_object_names if "id" in obj]

    content_objects = []

    if "crawl_results" in content_object_names:
        results = crawl_results_store.get("latest", [])
        print("113", results)
        dropdown_options = []

        # Add "None" option to allow re-running Firecrawl
        for item in results:
            # print("line120", results)
            metadata = item.get("metadata", {})
            title = metadata.get("title", "Untitled Page").strip()
            url = metadata.get("url", "No URL")
            scrape_id = metadata.get("scrapeId") or url
            rawHtml = item.get("rawHtml")
            screenshot = item.get("screenshot")
            markdown = item.get("markdown")
            # print("line128", markdown)

            label = f"{title} ({url})"

            dropdown_options.append({
                "value": {
                    "id": scrape_id,
                    "label": label,
                    "markdown":markdown
                },
                "label": label
            })

        content_objects.append({
            "content_object_name": "crawl_pages_dropdown",
            "data": dropdown_options
        })

    return Response(data={"content_objects": content_objects})



# @router.route("/webhook", methods=["POST"])
# def firecrawl_webhook():
#     try:
#         payload = flask_request.get_json(force=True)

#         if isinstance(payload, list):
#             for event in payload:
#                 handle_webhook_event(event)
#         elif isinstance(payload, dict):
#             handle_webhook_event(payload)
#         else:
#             print("⚠️ Unknown payload format:", type(payload))

#         return Response(data={"received": True}, metadata={"status": "ok"})

#     except Exception as e:
#         import traceback
#         traceback.print_exc()
#         return Response(data={"error": str(e)}, status_code=500)


# def handle_webhook_event(payload):
#     event_type = payload.get("type")
#     job_id = payload.get("id")
#     data = payload.get("data", {})
#     metadata = payload.get("metadata", {})

#     if event_type == "crawl.started":
#         print(f"🚀 Crawl started for job {job_id}")
#         return Response(data={"status": "started", "job_id": job_id})

#     elif event_type == "crawl.page":
#         print("📄 Page crawled:", json.dumps(data, indent=2))
#         return Response(data=data)

#     elif event_type == "crawl.completed":
#         print(f"✅ Crawl completed for job {job_id}")
#         try:
#             # Optionally still store result (if you want to use /content endpoint)
#             firecrawl_response = requests.get(
#                 f"https://api.firecrawl.dev/v1/crawl/{job_id}",
#                 headers={"Authorization": f"Bearer {os.getenv('FIRECRAWL_API_KEY')}"}
#             )
#             firecrawl_response.raise_for_status()
#             crawl_result = firecrawl_response.json()

#             # (Optional) If still using a store for dropdowns or UI later
#             # crawl_results_store[job_id] = crawl_result

#             # 🚨 Trigger v2 automatically by POSTing job_id
#             requests.post(
#                 "https://6e43-79-127-185-251.ngrok-free.app/crawl/v1/data", 
#                 json={"job_id": job_id}
#             )

#             return Response(data={"status": "completed", "job_id": job_id})

#         except Exception as e:
#             print(f"❌ Error during post-completion for job {job_id}: {e}")
#             return Response(data={"status": "error", "message": str(e)}, status_code=500)

#     elif event_type == "crawl.failed":
#         print(f"❌ Crawl failed for job {job_id}")
#         return Response(data={"status": "failed", "job_id": job_id})

#     else:
#         print(f"⚠️ Unknown event type: {event_type}")
#         return Response(data={"status": "unknown", "event": event_type})

# @router.route("/data", methods=["POST","GET"])
# def data():
#     request = Request(flask_request)
#     data = request.data

#     # Check if the webhook is posting a job_id directly
#     job_id = data.get("job_id")
#     if job_id:
#         try:
#             response = requests.get(
#                 f"https://api.firecrawl.dev/v1/crawl/{job_id}",
#                 headers={"Authorization": f"Bearer {os.getenv('FIRECRAWL_API_KEY')}"}
#             )
#             response.raise_for_status()
#             return Response(data={"job_id": job_id, "result": response.json()})
#         except Exception as e:
#             return Response(data={"error": str(e)}, status_code=500)

#     # Handle Dev Studio dropdown population (content_object_names logic)
#     form_data = data.get("form_data", {})
#     content_object_names = data.get("content_object_names", [])

#     if isinstance(content_object_names, list) and content_object_names and isinstance(content_object_names[0], dict):
#         content_object_names = [obj.get("id") for obj in content_object_names if "id" in obj]

#     content_objects = []

#     for content_object_name in content_object_names:
#         if content_object_name == "crawl_result":
#             job_id = form_data.get("job_id")
#             if job_id:
#                 try:
#                     response = requests.get(
#                         f"https://api.firecrawl.dev/v1/crawl/{job_id}",
#                         headers={"Authorization": f"Bearer {os.getenv('FIRECRAWL_API_KEY')}"}
#                     )
#                     response.raise_for_status()
#                     crawl_result = response.json()
#                     data = [
#                         {"value": page.get("url", f"page_{i}"), "label": page.get("title") or page.get("url")}
#                         for i, page in enumerate(crawl_result.get("pages", []))
#                     ]
#                     content_objects.append({
#                         "content_object_name": "crawl_result",
#                         "data": data
#                     })
#                 except Exception as e:
#                     return Response(data={"error": str(e)}, status_code=500)

#     return Response(data={"content_objects": content_objects})

# @router.route("/results/<job_id>", methods=["GET"])
# def get_crawl_result(job_id):
#     if job_id in crawl_results_store:
#         return Response(data={"job_id": job_id, "result": crawl_results_store[job_id]})
#     return Response(data={"error": "Result not ready or job ID not found"}, status_code=404)
