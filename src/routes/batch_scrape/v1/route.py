from workflows_cdk import Response, Request
from flask import request as flask_request
from main import router
from firecrawl import FirecrawlApp, JsonConfig
import os
import json
import traceback


# batch_scrape_jobs = {
#     "jobs": []  
# }

# Initialize the Firecrawl client using the API key from environment variables
firecrawl_client = FirecrawlApp(api_key=os.getenv("FIRECRAWL_API_KEY"))


@router.route("/execute", methods=["GET", "POST"])
def execute():
    request = Request(flask_request)
    data = request.data
    form_data = request.data.get("form_data", {})
    selected_page = data.get("batch_scrape_results")
    selected_id = selected_page.get("id") if isinstance(selected_page, dict) else selected_page
    print("selected_page", selected_id)
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
                    data={"selected_page": result_data},
                    metadata={"status": "page_selected"}
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
        urls = data.get("urls", [])
        if isinstance(urls, str):
            urls = [urls]
        screenshot = data.get("screenshot", False)
        extracted_markdown = data.get("extractMarkdown", False)
        extraction_prompt = data.get("extraction_prompt", "").strip()
    

        formats = []
        if extracted_markdown:
            formats.append("markdown")
        if screenshot:
            formats.append("screenshot")
        if extraction_prompt:
            formats.append("json")

        json_options = None
        if extraction_prompt:
            json_options = {
                "prompt": extraction_prompt,
                "schema": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "description": {"type": "string"}
                    },
                    "required": ["title", "description"]
                }
            }

        try:
            batch_result = firecrawl_client.async_batch_scrape_urls(
                urls=urls,
                formats=formats,
                json_options=json_options,
                webhook={
                    "url": "https://2f20-185-98-169-23.ngrok-free.app/batch_scrape/v1/webhook",
                    "metadata": {"source": "batch_ui"},
                    "events": ["started", "page", "completed", "failed"]
                }
            )

            label = extraction_prompt[:40] + "..." if len(extraction_prompt) > 40 else extraction_prompt
            print("batch_resulets", batch_result)
            # batch_scrape_jobs["jobs"].append({
            #     "job_id": batch_result.id,
            #     "label": label,
            #     "urls": urls
            # })

            return Response(
                data={
                    "message": "Batch job submitted",
                    "job_id": batch_result.id,
                    "url": batch_result.url,
                    "firecrawl_job_id":batch_result.id,
                    "batch_scrape_results": {
                        "id": batch_result.id,
                        "label": label  # e.g., "mission"
                    }
                },
                metadata={"firecrawl_job_id": batch_result.id}
            )


        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response(data={"error": str(e)}, metadata={}, status_code=500)

    else:
        return Response(data={"error": "Invalid selection or missing ID."}, status_code=400)


@router.route("/content", methods=["POST", "GET"])
def content():
    request = Request(flask_request)
    data = request.data
    form_data = data.get("form_data", {})
    content_object_names = data.get("content_object_names", [])

    print("form_data:", form_data)
    print("content_obj_name:", content_object_names)

    job_id = form_data.get("firecrawl_job_id", {})
    url_list = form_data.get("urls")
    print("url_list", url_list)

    print("job_id from dropdown:", job_id)

    # Clean up content object names
    if isinstance(content_object_names, list) and content_object_names and isinstance(content_object_names[0], dict):
        content_object_names = [obj.get("id") for obj in content_object_names if "id" in obj]

    content_objects = []

    if "batch_scrape_results" in content_object_names:
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
                for url in url_list:
                    if url:
                            dropdown_options.append({
                                "value": {"id": f"{job_id}|{url}", "label": url},
                                "label": f"{url} ({job_id[:6]})"
                            })

            except Exception as e:
                print(f"Error fetching job {job_id}: {e}")

        content_objects.append({
            "content_object_name": "batch_scrape_results",
            "data": dropdown_options
        })

    return Response(data={"content_objects": content_objects})



# Define the webhook endpoint that will receive POST requests from Firecrawl
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


# This function handles individual webhook events sent from Firecrawl
# Global storage


def handle_webhook_event(payload):
    event_type = payload.get("type")
    job_id = payload.get("id")

    print(f"Webhook event received: {event_type} for job {job_id}")

    if event_type == "batch_scrape.completed":
        return fetch_and_return_results(job_id)

    elif event_type == "batch_scrape.page":
        return fetch_and_return_results(job_id)

    elif event_type == "batch_scrape.started":
        return {"message": f"Scrape started for job {job_id}"}

    elif event_type == "batch_scrape.failed":
        return {"error": f"Scrape failed for job {job_id}"}

    else:
        return {"error": f"Unknown event type: {event_type}"}




def fetch_and_return_results(job_id):
    print("Fetching results for job:", job_id)
    results = firecrawl_client.check_batch_scrape_status(job_id)

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



# def fetch_and_return_current_progress(job_id):
#     status = firecrawl_client.check_batch_scrape_status(job_id)
#     print("status",status)
#     return {"status": status}

