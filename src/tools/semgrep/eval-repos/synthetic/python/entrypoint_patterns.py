"""Test file for Elttam entrypoint discovery patterns.

Contains Flask, Django, and FastAPI entrypoint patterns.
"""

# Flask entrypoints
from flask import Flask, request, jsonify

app = Flask(__name__)


# ENTRYPOINT_DISCOVERY: Flask route
@app.route('/')
def index():
    return jsonify({"message": "Home page"})


# ENTRYPOINT_DISCOVERY: Flask route with methods
@app.route('/api/users', methods=['GET', 'POST'])
def users():
    if request.method == 'GET':
        return jsonify({"users": []})
    return jsonify({"created": True})


# ENTRYPOINT_DISCOVERY: Flask route with parameter
@app.route('/api/users/<int:user_id>')
def get_user(user_id):
    return jsonify({"id": user_id})


# ENTRYPOINT_DISCOVERY: Flask blueprint route
from flask import Blueprint

api = Blueprint('api', __name__)


@api.route('/products')
def products():
    return jsonify({"products": []})


# Django entrypoints (simulated patterns)
# ENTRYPOINT_DISCOVERY: Django URL pattern
# urlpatterns = [
#     path('api/orders/', views.orders, name='orders'),
# ]

# ENTRYPOINT_DISCOVERY: Django view function
def django_view(request):
    return {"data": "response"}


# ENTRYPOINT_DISCOVERY: Django class-based view
class DjangoListView:
    def get(self, request):
        return {"items": []}

    def post(self, request):
        return {"created": True}


# Django REST Framework patterns
# ENTRYPOINT_DISCOVERY: DRF ViewSet
class UserViewSet:
    def list(self, request):
        return {"users": []}

    def retrieve(self, request, pk=None):
        return {"user": {"id": pk}}

    def create(self, request):
        return {"created": True}


# ENTRYPOINT_DISCOVERY: DRF APIView
class OrderAPIView:
    def get(self, request):
        return {"orders": []}

    def post(self, request):
        return {"order_id": 123}


# FastAPI entrypoints
from fastapi import FastAPI, Path, Query

fastapi_app = FastAPI()


# ENTRYPOINT_DISCOVERY: FastAPI route
@fastapi_app.get("/")
async def fastapi_root():
    return {"message": "Hello World"}


# ENTRYPOINT_DISCOVERY: FastAPI route with path parameter
@fastapi_app.get("/items/{item_id}")
async def fastapi_get_item(item_id: int = Path(...)):
    return {"item_id": item_id}


# ENTRYPOINT_DISCOVERY: FastAPI POST endpoint
@fastapi_app.post("/items/")
async def fastapi_create_item(item: dict):
    return item


# ENTRYPOINT_DISCOVERY: FastAPI with query parameters
@fastapi_app.get("/search/")
async def fastapi_search(q: str = Query(None)):
    return {"query": q}


# Tornado handler pattern
# ENTRYPOINT_DISCOVERY: Tornado RequestHandler
class TornadoHandler:
    def get(self):
        self.write({"data": "response"})

    def post(self):
        self.write({"created": True})


# AUDIT_INPUT_SINK: User input handling
@app.route('/api/process', methods=['POST'])
def process_input():
    user_data = request.get_json()  # AUDIT_INPUT_SINK
    return jsonify({"processed": user_data})


# AUDIT_FILE_UPLOAD: File upload endpoint
@app.route('/api/upload', methods=['POST'])
def upload_file():
    file = request.files['file']  # AUDIT_FILE_UPLOAD
    return jsonify({"filename": file.filename})
