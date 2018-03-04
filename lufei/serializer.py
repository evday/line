from rest_framework import serializers


class AuthSerializer(serializers.Serializer):
    username = serializers.CharField(error_messages={'required':'用户名不能为空'})
    password = serializers.CharField(error_messages={'required':'密码不能为空'})





