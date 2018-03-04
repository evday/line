from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^auth/',views.AuthView.as_view()),
    url(r'^shopping_car/',views.ShoppingCarView.as_view()),
    url(r'^accounts/',views.AccountView.as_view()),

]

