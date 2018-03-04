#!/usr/bin/env python
# -*- coding:utf-8 -*-
from rest_framework.authentication import BaseAuthentication
from rest_framework.authentication import get_authorization_header
from django.utils.translation import ugettext_lazy as _

from rest_framework import HTTP_HEADER_ENCODING, exceptions
from lufei.models import UserAuthToken


class LuffyTokenAuthentication(BaseAuthentication):
    keyword = 'Token'

    def authenticate(self, request):
        """
        Authenticate the request and return a two-tuple of (user, token).
        """
        token = request.query_params.get('token')
        if not token:
            raise exceptions.AuthenticationFailed('验证失败')

        return self.authenticate_credentials(token)

    def authenticate_credentials(self, token):
        try:
            token_obj = UserAuthToken.objects.select_related('user').get(token=token)
        except Exception as e:
            raise exceptions.AuthenticationFailed(_('Invalid token.'))

        return (token_obj.user, token_obj)
