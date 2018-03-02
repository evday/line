from lufei.utils.auth.token_auth import LuffyTokenAuthentication

class AuthApiView(object):
    authentication_classes = [LuffyTokenAuthentication,]