from workflows_cdk import Response, Request
from flask import request as flask_request
from main import router
from firecrawl import FirecrawlApp, ScrapeOptions
import os
import json
import requests
import builtins


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
    selected_id = selected_page.get("id") if isinstance(selected_page, dict) else selected_page
    # Part 1: User selected a page from dropdown
    if selected_id and "|" in selected_id:
        try:
            job_id, url = selected_id.split("|", 1)
            print("🔍 Parsed job_id:", job_id)
            print("🔍 Parsed url:", url)

            result_data = fetch_and_return_results(job_id)
            print("line34", result_data)
            # full_results = result_data.get("results", {})
            full_results = result_data.get("results", {}).get("data", [])
            print("line35", full_results)
            # print("🔍 URL to match:", url)
            # print("🔍 Available URLs in results:")
            # for item in full_results:
            #     print("🔍 item:", item)
            #     print("🔍 matched url:", item.get("metadata", {}).get("url"))
                # print("Checking against:", item.get("results", {}).get("sorceUrl"))
            matched_result = next((item for item in full_results if item.get("metadata", {}).get("sourceURL") == url), None)
            # print("line38", matched_result)
            if matched_result:
                return Response(
                    data={"selected_page": matched_result},
                    metadata={"status": "page_selected"}
                )
            else:
                return Response(
                    data={"error": f"No result found for {url}"},
                    status_code=404
                )

        except Exception as e:
            return Response(
                data={"error": f"Error selecting specific page: {str(e)}"},
                status_code=500
            )
    # Case 1: User selects existing job_id|url to check status
    fc_id = data.get("firecrawl_job_id", False)        
    print("fc_id", fc_id)    
    if fc_id:
        try:
            result_data = fetch_and_return_results(fc_id)
            # if hasattr(result_data["results"], "to_dict"):
            #     result_data["results"] = result_data["results"].to_dict()
            # elif hasattr(result_data["results"], "__dict__"):
            #     result_data["results"] = result_data["results"].__dict__

            print("Cleaned result_data", result_data)
            if result_data:
                return Response(
                    data={"message": "Crawl completed. Please select a page from the dropdown to view specific details.","selected_page": result_data, },
                    metadata={"status": "page_selected"},
                    
                )
            else:
                return Response(
                    data={"error": "Job is not completed yet."},
                    status_code=202
                )

        except Exception as e:
            return Response(
                data={"error": f"Error loading job: {str(e)}"},
                status_code=500
            )
    # Case 2: User selects "None" — Start a new batch scrape
    elif not fc_id:
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
            crawl_results = firecrawl_client.async_crawl_url(
                **crawl_kwargs,
                webhook={
                    "url": "https://79f3-73-15-183-86.ngrok-free.app/crawl/v1/webhook",
                    "metadata": {"source": "batch_ui"},
                    "events": ["started", "page", "completed", "failed"]
                }
            )
                
            print("Crawl started successfully:", crawl_results)
            result_data = crawl_results.model_dump(exclude_unset=True)
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
    request = Request(flask_request)
    data = request.data
    form_data = data.get("form_data", {})
    content_object_names = data.get("content_object_names", [])

    print("form_data:", form_data)
    print("content_obj_name:", content_object_names)

    job_id = form_data.get("firecrawl_job_id", {})
    url = form_data.get("url")
    print("url_list", url )

    print("job_id from dropdown:", job_id)

    # Clean up content object names
    if isinstance(content_object_names, list) and content_object_names and isinstance(content_object_names[0], dict):
        content_object_names = [obj.get("id") for obj in content_object_names if "id" in obj]

    content_objects = []

    if "crawl_results" in content_object_names:
        dropdown_options = [{
            "value": {"id": "None", "label": "None"},
            "label": "None"
        }]

        if job_id and job_id != "None":
            try:
                # 🔥 Fetch fresh results from Firecrawl
                response = fetch_and_return_results(job_id)
                results = response.get("results", {}).get("data", [])

                # 🔥 Organize dropdown by URL
                # for doc in results:
                # metadata = doc.get("metadata", {})
                # url = metadata.get("url")
                for doc in results:
                    metadata = doc.get("metadata", {})
                    # print("metadata:", metadata)
                    source_url = metadata.get("sourceURL")
                    # print("source_url:", source_url)
                    if source_url:
                        dropdown_options.append({
                            "value": {"id": f"{job_id}|{source_url}", "label": source_url},
                            "label": f"{source_url} ({job_id[:6]})"
                        })

            except Exception as e:
                print(f"Error fetching job {job_id}: {e}")

        content_objects.append({
            "content_object_name": "batch_scrape_results",
            "data": dropdown_options
        })

    return Response(data={"content_objects": content_objects})

def fetch_and_return_results(job_id):
    # print("Fetching results for job:", job_id)
    results = firecrawl_client.check_crawl_status(job_id)
    # print("results:", results)
    # Convert main object to dict
    if hasattr(results, "to_dict"):
        results = results.to_dict()
    elif hasattr(results, "__dict__"):
        results = results.__dict__

    # Convert each document inside results["data"]
    documents = results.get("data", [])
    cleaned_docs = []

    for doc in documents:
        if hasattr(doc, "to_dict"):
            cleaned_docs.append(doc.to_dict())
        elif hasattr(doc, "__dict__"):
            cleaned_docs.append(doc.__dict__)
        else:
            cleaned_docs.append(doc)  # fallback, likely won't happen

    results["data"] = cleaned_docs
    # print("Converted results:", results)
    return {"status": "completed", "results": results}





@router.route("/webhook", methods=["POST"])
def firecrawl_webhook():
    payload = flask_request.get_json(force=True) 

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



def handle_webhook_event(payload):
    event_type = payload.get("type")
    job_id = payload.get("id")
    data = payload.get("data", {})
    metadata = payload.get("metadata", {})

    if event_type == "crawl.started":
        print(f"🚀 Crawl started for job {job_id}")
        return Response(data={"status": "started", "job_id": job_id})

    elif event_type == "crawl.page":
        return fetch_and_return_results

    elif event_type == "crawl.completed":
        print(f"✅ Crawl completed for job {job_id}")
        try:
            result_data = fetch_and_return_results(job_id)

            return Response(data={"status": "completed", "result": result_data})

        except Exception as e:
            print(f"❌ Error during post-completion for job {job_id}: {e}")
            return Response(data={"status": "error", "message": str(e)}, status_code=500)

    elif event_type == "crawl.failed":
        print(f"❌ Crawl failed for job {job_id}")
        return Response(data={"status": "failed", "job_id": job_id})

    else:
        print(f"⚠️ Unknown event type: {event_type}")
        return Response(data={"status": "unknown", "event": event_type})

