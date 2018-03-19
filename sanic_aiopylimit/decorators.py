from aiopylimit import AIOPyRateLimit


def aiopylimit(namespace, limit_args, limit_reached_view=None, key_func=None):
    def real_decorator(func):
        async def wrapper(*args, **kwargs):
            limiter = AIOPyRateLimit(*limit_args)
            request = args[0]
            limit_reached_view_local = limit_reached_view
            if limit_reached_view_local is None:
                limit_reached_view_local = request.app.limit_reached_view
            if key_func is None:
                key = request.app.limit_key_func(request)
            else:
                key = key_func(request)
            full_key = f'{request.app.limit_global_namespace_prefix}-' \
                       f'{namespace}-{key}'

            if await limiter.is_rate_limited(full_key) \
                    or not await limiter.attempt(full_key):
                return limit_reached_view_local(request)

            return await func(*args, **kwargs)

        return wrapper

    return real_decorator
