from sanic import Sanic
from sanic import response
from sanic.response import json
from sanic.views import HTTPMethodView

from sanic_aiopylimit.decorators import aiopylimit
from sanic_aiopylimit.limit import SanicAIOPyLimit

app = Sanic(__name__)


@app.route("/")
async def test(request):
    return response.json({"test": True})


def custom_key(request):
    return "something"


def custom_view(request):
    return json("bad", status=400)


class SimpleSyncView(HTTPMethodView):

    @aiopylimit("class_based_get", (60, 1))  # 1 per 60 seconds
    def get(self, request):
        return json('OK')


app.add_route(SimpleSyncView.as_view(), '/simpleview')


@app.route("/write")
@aiopylimit("write_api", (60, 1), key_func=custom_key,
            limit_reached_view=custom_view)  # 1 per 60 seconds
async def test(request):
    return response.json({"test": True})


@app.route("/write2")
@aiopylimit("write_api2", (60, 1))  # 1 per 60 seconds
async def test(request):
    return response.json({"test": True})
app.config['SANIC_AIOPYRATELIMIT_REDIS_HOST'] = "localhost"

SanicAIOPyLimit.init_app(app, global_limit=(10, 10))  # 10 per 10 seconds


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8000)
