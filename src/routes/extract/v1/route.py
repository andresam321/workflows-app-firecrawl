from workflows_cdk import Response, Request
from flask import request as flask_request
from main import router
from firecrawl import FirecrawlApp, JsonConfig
import os
import json
import traceback
from threading import Thread
import time
# Initialize the Firecrawl client using the API key from environment variables
firecrawl_client = FirecrawlApp(api_key=os.getenv("FIRECRAWL_API_KEY"))

extract_results = {} 
print("extracted_res",extract_results)
def poll_extract_job(job_id):
    for _ in range(20):  # Poll every 5s for up to ~100 seconds
        status = firecrawl_client.get_extract_status(job_id)
        if status.status == "completed":
            extract_results[job_id] = {
                "status": "completed",
                "data": status.data
            }
            break
        elif status.status == "failed":
            extract_results[job_id] = {
                "status": "failed",
                "error": "Job failed"
            }
            break
        time.sleep(5)

@router.route("/execute", methods=["GET", "POST"])
def execute():
    request = Request(flask_request)
    # Wraps the incoming Flask request using the custom Request class to standardize data handling.

    data = request.data
    # Extracts the request payload into a dictionary.

    url = data.get("url", "").strip()
    # Retrieves the "url" field from the request data and removes leading/trailing spaces. Defaults to an empty string.
    # schema = data.get("schema")
    enable_web_search = data.get("enable_web_search", False)
    # use_async = data.get("use_async", False)
    extract_query = data.get("extract_query", "").strip()
    # Retrieves the "extract_query" field from the request data and removes leading/trailing spaces. Defaults to an empty string.

    if not url.startswith("http"):
        # Checks if the provided URL is valid (must start with http/https). If not, return a 400 error response.
        return Response(
            data={"error": f"Invalid URL format: {url}"},
            metadata={"affected_rows": 0},
            status_code=400
        )

    try:
        # if use_async:
        #     job = firecrawl_client.async_extract(
        #         urls = [url],
        #         prompt=extract_query,
        #         enable_web_search=enable_web_search
        #     )
        #     Thread(target=poll_extract_job, args=(job.id,)).start()

        #     return Response(data={"status":"submitted","job_id": job.id})
        # # Attempts to execute the extraction logic using Firecrawl.
        # else:

        extract_result = firecrawl_client.extract(
            urls=[url],
            prompt=extract_query,
                # schema=schema,
                enable_web_search=enable_web_search
            )
            # Calls the Firecrawl `extract` method with the given URL and query prompt.

        return Response(
            data={"result": extract_result.model_dump(exclude_unset=True)},
            metadata={"status": "success"}
        )
            # Returns a successful response with the serialized result from the extract call.

    except Exception as e:
        import traceback
        traceback.print_exc()
        # If any exception occurs, prints the full stack trace for debugging.

        return Response(
            data={"error": str(e)},
            metadata={"affected_rows": 0},
            status_code=500
        )
        # Returns a 500 error response with the exception message and metadata.