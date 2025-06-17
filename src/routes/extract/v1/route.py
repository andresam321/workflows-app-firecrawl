from workflows_cdk import Response, Request
from flask import request as flask_request
from main import router
from firecrawl import FirecrawlApp, JsonConfig
import os
import json
import traceback
from threading import Thread
import time

extract_results_object = {}
# Initialize the Firecrawl client using the API key from environment variables
firecrawl_client = FirecrawlApp(api_key=os.getenv("FIRECRAWL_API_KEY"))

# extract_results = {} 
# print("extracted_res",extract_results)
# def poll_extract_job(job_id):
#     for _ in range(20):  # Poll every 5s for up to ~100 seconds
#         status = firecrawl_client.get_extract_status(job_id)
#         if status.status == "completed":
#             extract_results[job_id] = {
#                 "status": "completed",
#                 "data": status.data
#             }
#             break
#         elif status.status == "failed":
#             extract_results[job_id] = {
#                 "status": "failed",
#                 "error": "Job failed"
#             }
#             break
#         time.sleep(5)

@router.route("/execute", methods=["GET", "POST"])
def execute():
    request = Request(flask_request)
    data = request.data

    selected_page = data.get("extract_results")
    print("Selected page object:", selected_page)

    if isinstance(selected_page, dict):
        selected_id = selected_page.get("id")
        print("Selected ID string:", selected_id)

        if selected_id and "|" in selected_id:
            job_id, selected_url = selected_id.split("|", 1)
            # print("Parsed job_id:", job_id)
            # print("Parsed selected_url:", selected_url)

            try:
                status = firecrawl_client.get_extract_status(job_id)
                # print("Firecrawl status object:", status)
             
                # print("Type of data:", type(status.data))
                # print("Data:", status.data)
                if status.status == "completed":
                    result_data = status.data
                    print("Completed result data type:", type(result_data))
                    print("Raw result data:", result_data)

                    # Since result_data is always a dict for your use case
                    return Response(data={"selected_page": result_data}, metadata={"status": "page_selected"})

                else:
                    return Response(data={"error": "Job is not completed yet."}, status_code=202)

            except Exception as e:
                print("Error while fetching extract status:", str(e))
                return Response(data={"error": f"Error loading job: {str(e)}"}, status_code=500)


        # Case 2: User selected "None" → Start new scrape
        elif selected_id == "None":
            urls = data.get("urls", [])
            print("urls line 78", urls)
            extract_query = data.get("extract_query", "").strip()
            enable_web_search = data.get("enable_web_search", False)

            if not isinstance(urls, list) or not all(isinstance(u, str) and u.startswith("http") for u in urls):
                return Response(
                    data={"error": "Invalid URLs provided. Must be a list of valid http/https strings."},
                    status_code=400
                )
            try:
                
                jobs_list = []

                for url in urls:
                    extract_result = firecrawl_client.async_extract(
                        urls=[url],
                        prompt=extract_query,
                        enable_web_search=enable_web_search
                    )
                    # print("line102 extract result", extract_result)
                    job_id = extract_result.id
                    label = extract_query[:40] + "..." if len(extract_query) > 40 else extract_query

                    if "jobs" not in extract_results_object:
                        extract_results_object["jobs"] = []

                    extract_results_object["jobs"].append({
                        "job_id": job_id,
                        "query": label,
                        "urls": url  
                    })

                    jobs_list.append({"job_id": job_id, "url": url})

                # Now return the response AFTER all async_extracts finish
                return Response(
                    data={"message": "Jobs submitted.", "jobs": jobs_list},
                    metadata={"status": "submitted"}
                )

            except Exception as e:
                return Response(data={"error": str(e)}, status_code=500)

    # Default fallback — neither job selection nor new extract provided
    return Response(
        data={"error": "No valid job or URL provided."},
        status_code=400
    )


@router.route("/content", methods=["POST", "GET"])
def content():
    request = Request(flask_request)
    data = request.data
    form_data = data.get("form_data", {})
    extract_query_data = form_data.get("extract_query")
    
    print("line114", extract_query_data)
    # Get the selected job label or id from the dropdown
    

    content_object_names = data.get("content_object_names", [])
    if isinstance(content_object_names, list) and content_object_names and isinstance(content_object_names[0], dict):
        content_object_names = [obj.get("id") for obj in content_object_names if "id" in obj]

    content_objects = []
    
    print("content_object_name",content_object_names)
    # Build dropdown of previous extract jobs
    if "extract_results" in content_object_names:
        jobs = extract_results_object.get("jobs", [])
        # print("line143, jobs",jobs)
        dropdown_options = [{
            "value": {"id": "None", "label": "None"},
            "label": "None"
        }]

        for job in jobs:
            print()
            job_id = job["job_id"]
            label = job["query"]
            urls = job['urls']

            if isinstance(urls, str):
                urls = [urls]

            for url in urls:
                # print("line 162", url)
                dropdown_options.append({
                    "value": {"id": f"{job_id}|{url}", "label": url},
                    "label": f"{url} ({job_id[:6]})"
                })

        content_objects.append({
            "content_object_name": "extract_results",
            "data": dropdown_options
        })

    return Response(data={"content_objects": content_objects})
 