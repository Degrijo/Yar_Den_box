from rest_framework_simplejwt import authentication


class MyMiddleware:
    def __init__(self, inner):
        self.inner = inner

    def __call__(self, scope):
        scope['user'] = authentication.JWTAuthentication().authenticate(scope)[0]
        response = self.inner(scope)
        return response
