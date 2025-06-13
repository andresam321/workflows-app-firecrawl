from workflows_cdk import Response, Request
from flask import request as flask_request
from main import router
import os
import requests



@router.route("/execute", methods=["POST", "GET"])
def v2_execute():
    """
    Fetch Firecrawl results directly from Firecrawl API using job_id.
    No caching, no storing locally.
    """
    request = Request(flask_request)
    data = request.data
    job_id = data.get("job_id", "").strip()

    if not job_id:
        return Response(data={"error": "Missing job_id"}, status_code=400)

    try:
        response = requests.get(
            f"https://api.firecrawl.dev/v1/crawl/{job_id}",
            headers={"Authorization": f"Bearer {os.getenv('FIRECRAWL_API_KEY')}"}
        )
        response.raise_for_status()
        return Response(data={"job_id": job_id, "result": response.json()})

    except Exception as e:
        return Response(
            data={"error": f"Failed to fetch results: {str(e)}"},
            status_code=500
        )
