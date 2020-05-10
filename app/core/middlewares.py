from rest_framework_simplejwt import authentication


class MyMiddleware:
    def __init__(self, inner):
        self.inner = inner

    def __call__(self, scope):
        response = self.inner(scope)
        return response
