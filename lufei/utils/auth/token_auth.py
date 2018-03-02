from django.utils.translation import ugettext_lazy as _

from rest_framework.authentication import BaseAuthentication
from rest_framework import exceptions

from lufei.models import UserAuthToken

class LuffyTokenAuthentication(BaseAuthentication):
    keyword = 'token'

    def authenticate(self, request):

        # 从get中获取用户传递过来的token
        token = request.query_parmas.get('token')
        if not token:
            raise exceptions.AuthenticationFailed('验证失败')

        return self.authenticate_credentials(token)

    def authenticate_credentials(self, token):
        try:
            token_obj = UserAuthToken.objects.select_related('user').get(token=token)
        except Exception as e:
            # _ 代表django的惰性翻译
            raise exceptions.AuthenticationFailed(_('Invalid token.'))
        return (token_obj.user,token_obj)

