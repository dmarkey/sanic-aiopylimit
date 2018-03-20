from collections import UserDict

import asynctest
import unittest

from aiopylimit import AIOPyRateLimit
from sanic import Sanic, response
from unittest.mock import Mock

from sanic_aiopylimit.limit import (SanicAIOPyLimit, REDIS_HOST_KEY,
                                    REDIS_PORT_KEY,
                                    REDIS_DB_KEY, REDIS_IS_SENTINAL_KEY,
                                    REDIS_PASSWORD_KEY)

from sanic_aiopylimit.decorators import aiopylimit


class TestSanicAIOPyLimit(unittest.TestCase):
    def test_config_non_default(self):
        app = Sanic(__name__)
        app.config[REDIS_HOST_KEY] = 'remote-redis'
        app.config[REDIS_PORT_KEY] = '1234'
        app.config[REDIS_DB_KEY] = '10'
        app.config[REDIS_PASSWORD_KEY] = 'boom'
        app.config[REDIS_IS_SENTINAL_KEY] = '1'

        SanicAIOPyLimit.init_app(app)
        self.assertEqual(AIOPyRateLimit.redis_helper.db, 10)
        self.assertEqual(AIOPyRateLimit.redis_helper.password, 'boom')
        self.assertEqual(AIOPyRateLimit.redis_helper.host, 'remote-redis')
        self.assertEqual(AIOPyRateLimit.redis_helper.port, 1234)
        self.assertEqual(AIOPyRateLimit.redis_helper.is_sentinel, 1)

    def test_config_default(self):
        app = Sanic(__name__)
        self.assertRaises(ValueError, SanicAIOPyLimit.init_app, app)
        app.config[REDIS_HOST_KEY] = 'remote-redis'
        SanicAIOPyLimit.init_app(app)
        self.assertEqual(AIOPyRateLimit.redis_helper.db, 1)
        self.assertEqual(AIOPyRateLimit.redis_helper.password, None)
        self.assertEqual(AIOPyRateLimit.redis_helper.host, 'remote-redis')
        self.assertEqual(AIOPyRateLimit.redis_helper.port, 6379)
        self.assertEqual(AIOPyRateLimit.redis_helper.is_sentinel, 0)
        self.assertEqual(app.limit_global_namespace_prefix, 'sanic-aiopylimit')

    def test_config_exception(self):
        app = Sanic(__name__)
        app.config[REDIS_HOST_KEY] = 'remote-redis'
        self.assertRaises(ValueError, SanicAIOPyLimit.init_app,
                          app,
                          limit_reached_http_code=200,
                          limit_reached_view=lambda x: x)

    def test_advanced_options(self):
        app = Sanic(__name__)
        app.config[REDIS_HOST_KEY] = 'remote-redis'
        custom_view = lambda x: x
        custom_key_func = lambda x: x

        SanicAIOPyLimit.init_app(
            app,
            key_func=custom_key_func,
            limit_reached_view=custom_view, global_namespace_prefix="lala")

        self.assertEqual(app.limit_key_func, custom_key_func)
        self.assertEqual(app.limit_reached_view, custom_view)
        self.assertEqual(app.limit_global_namespace_prefix, 'lala')

    def test_middleware_installed(self):
        app = Sanic(__name__)
        app.config[REDIS_HOST_KEY] = 'remote-redis'

        SanicAIOPyLimit.init_app(
            app, global_limit=(60, 60))

        self.assertEqual(app.request_middleware[0].__name__,
                         'global_limit_middleware')


class TestMiddleware(asynctest.TestCase):

    @asynctest.patch("sanic_aiopylimit.limit.AIOPyRateLimit.is_rate_limited",
                     return_value=False)
    @asynctest.patch("sanic_aiopylimit.limit.AIOPyRateLimit.attempt",
                     return_value=True)
    async def test_middleware_success(self, attempt, is_rate_limited):
        app = Sanic(__name__)
        app.config[REDIS_HOST_KEY] = 'remote-redis'

        SanicAIOPyLimit.init_app(
            app, global_limit=(60, 60))
        request = UserDict()
        request.remote_addr = ''
        ret = await app.request_middleware[0](request)
        self.assertEqual(ret, None)
        attempt.assert_called_once_with(
            ('sanic-aiopylimit-pylimit_global-127.0.0.1'))
        is_rate_limited.assert_called_once_with(
            ('sanic-aiopylimit-pylimit_global-127.0.0.1'))

    @asynctest.patch("sanic_aiopylimit.limit.AIOPyRateLimit.is_rate_limited",
                     return_value=True)
    @asynctest.patch("sanic_aiopylimit.limit.AIOPyRateLimit.attempt",
                     return_value=False)
    async def test_middleware_limited(self, attempt, is_rate_limited):
        app = Sanic(__name__)
        app.config[REDIS_HOST_KEY] = 'remote-redis'

        SanicAIOPyLimit.init_app(
            app, global_limit=(60, 60))
        request = UserDict()
        request.remote_addr = ''
        ret = await app.request_middleware[0](request)
        self.assertEqual(ret.status, 429)
        attempt.assert_not_called()
        is_rate_limited.assert_called_once_with(
            ('sanic-aiopylimit-pylimit_global-127.0.0.1'))

    @asynctest.patch("sanic_aiopylimit.limit.AIOPyRateLimit.is_rate_limited",
                     return_value=False)
    @asynctest.patch("sanic_aiopylimit.limit.AIOPyRateLimit.attempt",
                     return_value=False)
    async def test_middleware_just_over(self, attempt, is_rate_limited):
        app = Sanic(__name__)
        app.config[REDIS_HOST_KEY] = 'remote-redis'

        SanicAIOPyLimit.init_app(
            app, global_limit=(60, 60))
        request = UserDict()
        request.remote_addr = ''
        ret = await app.request_middleware[0](request)
        self.assertEqual(ret.status, 429)
        is_rate_limited.assert_called_once_with(
            ('sanic-aiopylimit-pylimit_global-127.0.0.1'))
        attempt.assert_called_once_with(
            ('sanic-aiopylimit-pylimit_global-127.0.0.1'))

    @asynctest.patch("sanic_aiopylimit.limit.AIOPyRateLimit.is_rate_limited",
                     return_value=False)
    @asynctest.patch("sanic_aiopylimit.limit.AIOPyRateLimit.attempt",
                     return_value=False)
    async def test_middleware_success(self, attempt, is_rate_limited):
        app = Sanic(__name__)
        app.config[REDIS_HOST_KEY] = 'remote-redis'

        SanicAIOPyLimit.init_app(
            app, global_limit=(60, 60), key_func=lambda x: "temp")
        request = UserDict()
        request.remote_addr = ''
        ret = await app.request_middleware[0](request)
        self.assertEqual(ret.status, 429)
        is_rate_limited.assert_called_once_with(
            ('sanic-aiopylimit-pylimit_global-temp'))
        attempt.assert_called_once_with(
            ('sanic-aiopylimit-pylimit_global-temp'))

    @asynctest.patch("sanic_aiopylimit.limit.AIOPyRateLimit.is_rate_limited",
                     return_value=False)
    @asynctest.patch("sanic_aiopylimit.limit.AIOPyRateLimit.attempt",
                     return_value=False)
    async def test_middleware_success(self, attempt, is_rate_limited):
        app = Sanic(__name__)
        app.config[REDIS_HOST_KEY] = 'remote-redis'

        SanicAIOPyLimit.init_app(
            app, global_limit=(60, 60), key_func=lambda x: "temp",
            global_namespace_prefix="testing")
        request = UserDict()
        request.remote_addr = ''
        ret = await app.request_middleware[0](request)
        self.assertEqual(ret.status, 429)
        is_rate_limited.assert_called_once_with(
            'testing-pylimit_global-temp')
        attempt.assert_called_once_with('testing-pylimit_global-temp')


class TestDecorator(asynctest.TestCase):

    @asynctest.patch("sanic_aiopylimit.limit.AIOPyRateLimit.is_rate_limited",
                     return_value=False)
    @asynctest.patch("sanic_aiopylimit.limit.AIOPyRateLimit.attempt",
                     return_value=True)
    async def test_decorator_success(self, attempt, is_rate_limited):
        app = Sanic(__name__)

        @app.route("/")
        @aiopylimit("root_view", (60, 1))  # 1 per 60 seconds
        async def test(request):
            return response.json({"test": True})

        request = UserDict()
        request.app = Mock()
        request.app.limit_global_namespace_prefix = "sanic"
        request.app.limit_key_func = lambda x: "key"
        ret = await test(request)
        self.assertEqual(ret.status, 200)
        attempt.assert_called_once_with(
            'sanic-root_view-key')
        is_rate_limited.assert_called_once_with(
            'sanic-root_view-key')

    @asynctest.patch("sanic_aiopylimit.limit.AIOPyRateLimit.is_rate_limited",
                     return_value=True)
    @asynctest.patch("sanic_aiopylimit.limit.AIOPyRateLimit.attempt",
                     return_value=True)
    async def test_decorator_is_limited(self, attempt, is_rate_limited):
        app = Sanic(__name__)

        @app.route("/")
        @aiopylimit("root_view", (60, 1))  # 1 per 60 seconds
        async def test(request):
            return response.json({"test": True})

        request = UserDict()
        request.app = Mock()
        request.app.limit_global_namespace_prefix = "sanic"
        request.app.limit_key_func = lambda x: "key"
        request.app.limit_reached_view = lambda x: response.json("bad",
                                                                 status=429)
        ret = await test(request)
        self.assertEqual(ret.status, 429)
        attempt.assert_not_called()
        is_rate_limited.assert_called_once_with(
            'sanic-root_view-key')

    @asynctest.patch("sanic_aiopylimit.limit.AIOPyRateLimit.is_rate_limited",
                     return_value=False)
    @asynctest.patch("sanic_aiopylimit.limit.AIOPyRateLimit.attempt",
                     return_value=False)
    async def test_decorator_bad_attempt(self, attempt, is_rate_limited):
        app = Sanic(__name__)

        @app.route("/")
        @aiopylimit("root_view", (60, 1))  # 1 per 60 seconds
        async def test(request):
            return response.json({"test": True})

        request = UserDict()
        request.app = Mock()
        request.app.limit_global_namespace_prefix = "sanic"
        request.app.limit_key_func = lambda x: "key"
        request.app.limit_reached_view = lambda x: response.json("bad",
                                                                 status=429)
        ret = await test(request)
        self.assertEqual(ret.status, 429)
        attempt.assert_called_once_with(
            'sanic-root_view-key')
        is_rate_limited.assert_called_once_with(
            'sanic-root_view-key')

    @asynctest.patch("sanic_aiopylimit.limit.AIOPyRateLimit.is_rate_limited",
                     return_value=False)
    @asynctest.patch("sanic_aiopylimit.limit.AIOPyRateLimit.attempt",
                     return_value=False)
    async def test_decorator_custom_view(self, attempt, is_rate_limited):
        app = Sanic(__name__)

        @app.route("/")
        @aiopylimit("root_view", (60, 1),
                    limit_reached_view=lambda x: response.json("bad",
                                                               status=400))
        async def test(request):
            return response.json({"test": True})

        request = UserDict()
        request.app = Mock()
        request.app.limit_global_namespace_prefix = "sanic"
        request.app.limit_key_func = lambda x: "key"
        request.app.limit_reached_view = lambda x: response.json("bad",
                                                                 status=429)
        ret = await test(request)
        self.assertEqual(ret.status, 400)
        attempt.assert_called_once_with(
            'sanic-root_view-key')
        is_rate_limited.assert_called_once_with(
            'sanic-root_view-key')

    @asynctest.patch("sanic_aiopylimit.decorators.AIOPyRateLimit",
                     return_value=asynctest.MagicMock(
                         is_rate_limited=asynctest.CoroutineMock(
                             return_value=True)))
    async def test_decorator_limiter_called_correctly(self, limit_class):
        app = Sanic(__name__)

        @app.route("/")
        @aiopylimit("root_view", (60, 1),
                    limit_reached_view=lambda x: response.json("bad",
                                                               status=400))
        async def test(request):
            return response.json({"test": True})

        request = UserDict()
        request.app = Mock()
        request.app.limit_global_namespace_prefix = "sanic"
        request.app.limit_key_func = lambda x: "key"
        request.app.limit_reached_view = lambda x: response.json("bad",
                                                                 status=429)

        ret = await test(request)
        limit_class.assert_called_once_with(60, 1)
        self.assertEqual(ret.status, 400)

    @asynctest.patch("sanic_aiopylimit.decorators.AIOPyRateLimit",
                     return_value=asynctest.MagicMock(
                         is_rate_limited=asynctest.CoroutineMock(
                             return_value=True)))
    async def test_decorator_sync_view(self, limit_class):
        app = Sanic(__name__)

        @app.route("/")
        @aiopylimit("root_view", (60, 1),
                    limit_reached_view=lambda x: response.json("bad",
                                                               status=400))
        def test(request):
            return response.json({"test": True})

        request = UserDict()
        request.app = Mock()
        request.app.limit_global_namespace_prefix = "sanic"
        request.app.limit_key_func = lambda x: "key"
        request.app.limit_reached_view = lambda x: response.json("bad",
                                                                 status=429)

        ret = await test(request)
        limit_class.assert_called_once_with(60, 1)
        self.assertEqual(ret.status, 400)

    @asynctest.patch("sanic_aiopylimit.limit.AIOPyRateLimit.is_rate_limited",
                     return_value=False)
    @asynctest.patch("sanic_aiopylimit.limit.AIOPyRateLimit.attempt",
                     return_value=False)
    async def test_decorator_class_based(self, attempt, is_rate_limited):

        class TestClass(object):
            @aiopylimit("root_view", (60, 1),
                        limit_reached_view=lambda x: response.json(
                            "bad",
                            status=400))
            async def test(self, request):
                return response.json({"test": True})

        request = UserDict()
        request.app = Mock()
        request.app.limit_global_namespace_prefix = "sanic"
        request.app.limit_key_func = lambda x: "key"
        request.app.limit_reached_view = lambda x: response.json("bad",
                                                                 status=429)
        ret = await TestClass().test(request)
        self.assertEqual(ret.status, 400)
        attempt.assert_called_once_with(
            'sanic-root_view-key')
        is_rate_limited.assert_called_once_with(
            'sanic-root_view-key')

