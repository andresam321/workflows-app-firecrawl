from workflows_cdk import Response, Request
from flask import request as flask_request
from main import router
from firecrawl import FirecrawlApp, ScrapeOptions
import os
import json
import requests
import builtins
USE_MOCK_DATA = True  # Toggle this OFF when you want to use real API calls

crawl_results_store = {
    "latest": []
}

# if USE_MOCK_DATA:
#     crawl_results_store["latest"] = [
#         {
#             "markdown": "[Day 7 - Launch Week III.Integrations DayApril 14th to 20th](...)",
#             "rawHtml": "<html><body>Example page</body></html>",
#             "screenshot": "https://fake-screenshot-url.com/screenshot.png",
#             "metadata": {
#                 "title": "15 Python Web Scraping Projects: From Beginner to Advanced",
#                 "scrapeId": "97dcf796-c09b-43c9-b4f7-868a7a5af722",
#                 "sourceURL": "https://www.firecrawl.dev/blog/python-web-scraping-projects",
#                 "url": "https://www.firecrawl.dev/blog/python-web-scraping-projects",
#                 "statusCode": 200
#             }
#         },
#         {
#             "markdown": "[Another post link](...)",
#             "rawHtml": "<html><body>Another example</body></html>",
#             "screenshot": "https://fake-url.com/another-screenshot.png",
#             "metadata": {
#                 "title": "Scraping the Web with Python: A Practical Guide",
#                 "scrapeId": "2222aaaa-bbbb-cccc-dddd-eeeeffff1111",
#                 "sourceURL": "https://example.com/practical-guide",
#                 "url": "https://example.com/practical-guide",
#                 "statusCode": 200
#             }
#         }
#     ]

# print("crawl_results_store location:", id(crawl_results_store))
# Initialize the Firecrawl client using the API key from environment variables
firecrawl_client = FirecrawlApp(api_key=os.getenv("FIRECRAWL_API_KEY"))


@router.route("/execute", methods=["POST", "GET"])
def execute():
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

    selected_page = data.get("crawl_results")
    # print("selected page", selected_page)

    # Part 1: User selected a page from dropdown
    if isinstance(selected_page, dict):
        selected_id = selected_page.get("id")

        # Reuse a previous crawl
        if selected_id and selected_id != "None":
            stored_results = crawl_results_store.get("latest", [])
            matched = next(
                (r for r in stored_results if r.get("metadata", {}).get("scrapeId") == selected_id),
                None
            )
            if not matched:
                return Response(data={"error": "Selected page not found"}, status_code=404)

            return Response(
                data={"selected_page": matched},
                metadata={"status": "page_selected"}
            )

        # If user selected "None", crawl fresh
        elif selected_id == "None":
            print("User selected None, performing new crawl...")

    # Part 2: First time crawling or "None" selected
    limit = int(data.get("limit", 5))
    include_markdown = data.get("include_markdown")
    html_type = data.get("html")

    formats = []
    if include_markdown:
        formats.append("markdown")
    if html_type:
        formats.append("html")

    crawl_kwargs = {"url": url, "limit": limit}
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
            metadata={"status": "crawl_failed"},
            status_code=500
        )




@router.route("/content", methods=["POST", "GET"])
def content():
    """
    Provide dynamic content for the module UI.
    Handles crawl_results dropdown with page titles.
    """
    try:
        request = Request(flask_request)
        data = request.data

        if not data:
            return Response(data={"message": "Missing request data"}, status_code=400)

        form_data = data.get("form_data", {})
        content_object_names = data.get("content_object_names", [])
        print("content object names", content_object_names)
        # If IDs are wrapped in objects, extract them
        if isinstance(content_object_names, list) and content_object_names and isinstance(content_object_names[0], dict):
            content_object_names = [obj.get("id") for obj in content_object_names if "id" in obj]

        content_objects = []

        for content_name in content_object_names:
            if content_name == "crawl_results":
                results = crawl_results_store.get("latest", [])

                # Build dropdown options
                dropdown_options = [{
                    "value": {
                        "id": "None",
                        "label": "None"
                    },
                    "label": "None"
                }]

                # Initialize lookup store if not already
                if "lookup" not in crawl_results_store:
                    crawl_results_store["lookup"] = {}

                for item in results:
                    metadata = item.get("metadata", {})
                    print("metadata", metadata)
                    title = metadata.get("title", "Untitled Page").strip()
                    url = metadata.get("url", "No URL")
                    print("url", url)
                    scrape_id = metadata.get("scrapeId") or url
                    print("scrapeid", scrape_id)

                    # Add to dropdown list
                    dropdown_options.append({
                        "value": {
                            "id": scrape_id,
                            "label": title,
                        
                        },
                        "label": f"{title} ({url})"
                    })

                    # Store full item in lookup for later use
                    crawl_results_store["lookup"][scrape_id] = {
                        "meta": {
                            "id": scrape_id,
                            "label": title,
                            "url": url,
                            "scrapeId": scrape_id
                        },
                        "formats": {
                            "markdown": item.get("markdown"),
                            "rawHtml": item.get("rawHtml"),
                            "screenshot": item.get("screenshot")
                        }
                    }
                content_objects.append({
                    "content_object_name": "crawl_results",
                    "data": dropdown_options
                })
                print("content_objects", content_objects)

        return Response(data={"content_objects": content_objects})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response(
            data={"error": str(e)},
            metadata={"status": "content_error"},
            status_code=500
        )




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
