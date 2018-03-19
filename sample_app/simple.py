from sanic import Sanic
from sanic import response

from sanic_aiopylimit.decorators import aiopylimit
from sanic_aiopylimit.limit import SanicAIOPyLimit

app = Sanic(__name__)


@app.route("/")
async def test(request):
    return response.json({"test": True})


@app.route("/write")
@aiopylimit("write_api", (60, 1))  # 1 per minute
async def test(request):
    return response.json({"test": True})

app.config['SANIC_AIOPYRATELIMIT_REDIS_HOST'] = "localhost"

SanicAIOPyLimit.init_app(app, global_limit=(60, 60))  # 1 per second


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8000)
