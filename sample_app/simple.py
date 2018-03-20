from sanic import Sanic
from sanic import response
from sanic.response import json
from sanic.views import HTTPMethodView

from sanic_aiopylimit.decorators import aiopylimit
from sanic_aiopylimit.limit import SanicAIOPyLimit

# Initialise the Sanic app
app = Sanic(__name__)


# Add a view that will have the global limit applied
@app.route("/")
async def test(request):
    return response.json({"test": True})


# Use this function to generate a custom limit key based on the request input
# This has to be synchronous
def custom_key(request) -> str:
    return "something"


# A custom view to return. This has to be synchronous
def custom_view(request):
    return json("bad", status=400)


# A simple sync view for example
class SimpleSyncView(HTTPMethodView):

    @aiopylimit("class_based_get", (60, 1))  # 1 per 60 seconds
    def get(self, request):
        return json('OK')


# Wire in the class based view
app.add_route(SimpleSyncView.as_view(), '/simpleview')


# Sample simple view
@app.route("/write")
@aiopylimit("write_api", (60, 1), key_func=custom_key,
            limit_reached_view=custom_view)  # 1 per 60 seconds
async def test(request):
    return response.json({"test": True})


# Sample simple view
@app.route("/write2")
@aiopylimit("write_api2", (60, 1))  # 1 per 60 seconds
async def test(request):
    return response.json({"test": True})

# Local redis host
app.config['SANIC_AIOPYRATELIMIT_REDIS_HOST'] = "localhost"

# Initialise the app
SanicAIOPyLimit.init_app(app, global_limit=(10, 10))  # 10 per 10 seconds

# Start goin' fast
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8000)
