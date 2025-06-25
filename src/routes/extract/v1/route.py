from workflows_cdk import Response, Request
from flask import request as flask_request
from main import router
from firecrawl import FirecrawlApp, JsonConfig
import os
import json
import traceback
from threading import Thread
import time
import requests
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
    run_id_flag = data.get("run_id", False)
    selected_page = data.get("extract_results")
    print("Selected page object:", selected_page)
    selected_id = selected_page.get("id") if isinstance(selected_page, dict) else selected_page
    print("Selected ID:", selected_id)
    if selected_id and "|" in selected_id:
        try:
            job_id, url = selected_id.split("|", 1)
            print("🔍 Parsed job_id:", job_id)
            print("🔍 Parsed url:", url)

            result_data = fetch_and_return_results(job_id)
            print("line34", result_data)
            page_data = result_data.get("results", {})
            # full_results = result_data.get("results", {}).get("data", [])
            # print("🔍 URL to match:", url)
            # print("🔍 Available URLs in results:")
            # for item in full_results:
            #     print("🔍 item:", item)
            #     print("🔍 matched url:", item.get("metadata", {}).get("url"))
                # print("Checking against:", item.get("results", {}).get("sorceUrl"))
            # matched_result = next((item for item in full_results if item.get("metadata", {}).get("sourceURL") == url), None)
            # print("line38", matched_result)
            if page_data:
                return Response(
                    data={"selected_page": page_data},
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
    fc_id_raw = data.get("firecrawl_job_id", False)
    print("fc_id (raw)", fc_id_raw)

    if fc_id_raw:
        try:
            # Parse the string into an actual list
            if not isinstance(fc_id_raw, list):
                return Response(
                    data={"error": "Expected a list of job IDs."},
                    status_code=400
                )

            all_results = []

            for job_id in fc_id_raw:
                print("Fetching results for job:", job_id)
                result_data = fetch_and_return_results(job_id)

                if result_data:
                    all_results.append({
                        "job_id": job_id,
                        "data": "select a url to display extracted data",
                    })

            return Response(
                data={"selected_pages": all_results},
                metadata={"status": "page_selected"}
            )

        except json.JSONDecodeError:
            return Response(
                data={"error": "Invalid JSON format for job ID list."},
                status_code=400
            )
        except Exception as e:
            return Response(
                data={"error": f"Error loading job: {str(e)}"},
                status_code=500
            )
    # Case 2: User selects "None" — Start a new batch scrape
    # if run_id_flag:
    elif not fc_id_raw:
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


                    jobs_list.append({"job_id": job_id, "urls": url, "label": label})

                # Now return the response AFTER all async_extracts finish
                return Response(
                    data={"message": "Jobs submitted.", "jobs": jobs_list},
                    metadata={"status": "submitted"}
                )
            
            # except requests.exceptions.HTTPError as http_err:
            #     # Return a clear error message to the user
            #     return Response(
            #         data={"error": "Scraping failed. The target site may block automated requests or the URL is invalid."},
            #         metadata={"status": "scrape_failed"},
            #     status_code=502
            # )

            except Exception as e:
                return Response(data={f"error prevent scraping {url}": str(e)}, status_code=500)

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
    content_object_names = data.get("content_object_names", [])

    print("form_data:", form_data)
    print("content_object_names:", content_object_names)

    # Normalize content_object_names to string list
    if isinstance(content_object_names, list) and content_object_names and isinstance(content_object_names[0], dict):
        content_object_names = [obj.get("id") for obj in content_object_names if "id" in obj]

    content_objects = []

    if "extract_results" in content_object_names:
        dropdown_options = [{
            "value": {"id": "None", "label": "None"},
            "label": "None"
        }]

        # Normalize job_id input

        job_id = form_data.get("firecrawl_job_id", "[]")
        url_list = form_data.get("urls", [])
        # Ensuring both lists are properly parsed
        try:
            job_ids = json.loads(job_id) if isinstance(job_id, str) else job_id
        except json.JSONDecodeError:
            return Response(data={"error": "Invalid job_id JSON format."}, status_code=400)
        print("Initial job_id:", job_id)
        print("url_list:", url_list)

        # if isinstance(job_id, list):
        #     job_id = job_id[0] if job_id else None
        # elif isinstance(job_id, str) and job_id.startswith("["):
        #     try:
        #         parsed = json.loads(job_id)
        #         job_id = parsed[0] if parsed else None
        #     except json.JSONDecodeError:
        #         print("⚠️ Invalid JSON for job_id")
        #         job_id = None

        # print("Normalized job_id:", job_id)

        # Build dropdown if we have a valid job_id
        if job_id and job_id != "None":
            try:
                # response = fetch_and_return_results(job_id)
                # results = response.get("results", {}).get("data", [])

                for job_id, url in zip(job_ids, url_list):
                    if url:
                        dropdown_options.append({
                            "value": {"id": f"{job_id}|{url}", "label": url},
                            "label": f"{url} ({job_id[:6]})"
                        })

            except Exception as e:
                print(f"❌ Error fetching job {job_id}: {e}")
                return Response(
                    data={"error": f"Failed to fetch job {job_id}: {str(e)}"},
                    status_code=500
                )

        content_objects.append({
            "content_object_name": "extract_results",  # Keep this consistent
            "data": dropdown_options
        })

    return Response(data={"content_objects": content_objects})



def fetch_and_return_results(job_id):
    print("Fetching results for job:", job_id)
    results = firecrawl_client.get_extract_status(job_id)
    print("line 119", results)
    # Convert main object to dict
    if hasattr(results, "to_dict"):
        results = results.to_dict()
    elif hasattr(results, "__dict__"):
        results = results.__dict__

    # Convert each document inside results["data"]
    documents = results.get("data", [])
    # print("line227", documents)
    # cleaned_docs = []

    # for doc in documents:
    #     if hasattr(doc, "to_dict"):
    #         cleaned_docs.append(doc.to_dict())
    #     elif hasattr(doc, "__dict__"):
    #         cleaned_docs.append(doc.__dict__)
    #     else:
    #         cleaned_docs.append(doc)  # fallback, likely won't happen

    # results["data"] = cleaned_docs
    # # print("Converted results:", results)
    # print("line239",results)
    return {"status": "completed", "results": documents}
