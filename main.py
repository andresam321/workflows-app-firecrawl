from flask import Flask
from workflows_cdk import Router
# from src.routes.scrape import register_scrape_routes
# print("✅ Routes imported")


# Create Flask app
app = Flask(__name__)
router = Router(app)

# register_scrape_routes(router)

app = router.app

@app.route("/ping", methods=["POST", "GET"])
def test_execute():
    return {"status": "pong"}, 200

@router.route("/test", methods=["GET"])
def test_router():
    return {"router": "working"}, 200


if __name__ == "__main__":
    router.run_app(app)