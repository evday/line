import json

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist

from rest_framework.views import APIView
from rest_framework.response import Response

from . import models
from .serializer import AuthSerializer
from.models import Account,UserAuthToken
from lufei.utils.auth.api_view import AuthApiView
from lufei.utils.exceptions import PricePolicyDoesNotExist
from lufei.utils.pool import POOL

import redis
CONN = redis.Redis(connection_pool=POOL)



class AuthView(APIView):
    def post(self,request,*args,**kwargs):
        response = {"code":1000,"errors":None}
        ser = AuthSerializer(data=request.data)
        if ser.is_valid():
            try:
                # 验证后的数据都存储在validate_data里面的
                user = Account.objects.get(**ser.validated_data)
                #get_or_create方法会根据其参数，从数据库中查询符合条件的记录，如果没有符合条件的记录，则会依据参数创建一条新纪录。
                token_obj,is_create = UserAuthToken.objects.get_or_create(user=user)
                response['token'] = token_obj.token
                response['name'] = user.username
                response['code'] = 1002
            except Exception as e:
                response['errors'] = '用户名或密码错误'
                response['code'] = 1001

        else:
            response['errors'] = ser.errors

        return Response(response)


class ShoppingCarView(AuthApiView,APIView):


    def get(self,request,*args,**kwargs):
        """
        查看购物车
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        response = {"code":1000,"data":None}
        try:
            course = CONN.hget(settings.LUFFY_SHOPPING_CAR,request.user.id)
            if course:
                course_dict = json.loads(course.decode('utf-8'))
                response["data"] = course_dict
        except Exception as e:
            response["code"] = 1001
            response["msg"] = "获取购物车列表失败"
        return Response(response)


    def post(self,request,*args,**kwargs):
        """
        获取课程ID和价格策略ID，放入redis
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        ret = {"code":1000,"msg":None}
        try:
            course_id = request.data.get('course_id')
            price_policy_id = request.data.get('price_policy_id')

            # 获取课程
            course_obj = models.Course.objects.get(id=course_id)

            # 获取当前课程的所有价格策略： id  有效期 价格
            price_policy_list = []
            flag = False
            # price_policy是 model表中的一个反向查询的字段(数据库不存在)
            price_policy_objs = course_obj.price_policy.all()
            for item in price_policy_objs:
                # 用户传递过来的价格策略id在数据库中存在
                if item.id == price_policy_id:
                    flag = True
                price_policy_list.append({"id":item.id,'valid_period':item.get_valid_period_display(),'price':item.price})

            if not flag:
                raise PricePolicyDoesNotExist()

            # 课程和价格策略都没有问题，将课程和价格策略放入到redis中
            # 课程id,课程图片地址，课程标题，课程价格策略，默认价格策略

            course_dict = {
                "id": course_obj.id,
                "img": course_obj.course_img,
                "title":course_obj.name,
                "price_policy_list":price_policy_list,
                "default_price_policy":price_policy_id
            }

            # a 获取当前用户购物车中的课程
            # b car["course_obj.id"] = course_dict
            # c conn.hset("luffy_shopping_car",request.user.id,car)
            nothing = CONN.hget(settings.LUFFY_SHOPPING_CAR,request.user.id)
            if not nothing:
                data = {course_obj.id:course_dict}
            else:
                data = json.loads(nothing.decode('utf-8'))
                # 更新
                data[course_obj.id] = course_dict

            CONN.hset(settings.LUFFY_SHOPPING_CAR,request.user.id,json.dumps(data))
        except ObjectDoesNotExist as e:
            ret["code"] = 1001
            ret["msg"] = "课程不存在"

        except PricePolicyDoesNotExist as e:
            ret["code"] = 1002
            ret["msg"] = "价格策略不存在"

        except Exception as e:
            print(e)
            ret["code"] = 1003
            ret["msg"] = "添加购物车异常"

        return Response(ret)

    def delete(self,request,*args,**kwargs):
        """
        删除购物车中的课程
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        response = {"code":1000}
        try:
            course_id = str(request.data.get("course_id"))
            print(course_id,type(course_id))
            course_dict = CONN.hget(settings.LUFFY_SHOPPING_CAR,request.user.id)
            if not course_dict:
                raise Exception("购物车中不存在课程")
            course_dict = json.loads(course_dict.decode("utf-8"))
            if course_id not in course_dict:
                raise Exception("购物车中无此课程")
            del course_dict[course_id]
            CONN.hset(settings.LUFFY_SHOPPING_CAR,request.user.id,json.dumps(course_dict))
            response["msg"] = "删除课程成功"
        except Exception as e:
            response["code"] = 1001
            response["msg"] = "删除课程异常"

        return Response(response)

    def put(self,request,*args,**kwargs):
        """
        更新购物车中默认的价格策略
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        response = {"code":1000}
        try:
            course_id = str(request.data.get("course_id"))
            price_policy_id = request.data.get("price_policy_id")
            course_dict = CONN.hget(settings.LUFFY_SHOPPING_CAR,request.user.id)
            if not course_dict:
                raise Exception("购物车清单不存在")
            course_dict = json.loads(course_dict.decode("utf-8"))
            if course_id not in course_dict:
                raise Exception("购物车清单中的商品不存在")

            policy_exist = False
            for policy in course_dict[course_id]["price_policy_list"]:
                if policy['id'] == price_policy_id:
                    policy_exist = True
                    break
            if not policy_exist:
                raise PricePolicyDoesNotExist()

            course_dict[course_id]["default_price_policy"] = price_policy_id
            CONN.hset(settings.LUFFY_SHOPPING_CAR,request.user.id,json.dumps(course_dict))
            response["msg"] = "价格策略修改成功"

        except PricePolicyDoesNotExist as e:
            response["code"] = 1001
            response["msg"] = "价格策略不存在"
        except Exception as e:
            response["code"] = 1002
            response["msg"] = str(e)

        return Response(response)








