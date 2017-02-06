#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^login/$', views.LoginView.as_view(), name='login'),
    url(r'^logout/$', views.LogoutView.as_view(), name='logout'),
    url(r'^register/$', views.RegisterView.as_view(), name='register'),
    url(r'^profile/$', views.ProfileView.as_view(), name='profile'),
    url(r'^profile/password/$', views.ChangePasswordView.as_view(), name='change_password'),
    url(r'^users/$', views.UsersView.as_view(), name='users'),
    url(r'^users/(?P<pk>(-)?[0-9]+)/$', views.UserView.as_view(), name='user'),
    url(r'^users/(?P<pk>(-)?[0-9]+)/edit/$', views.UserEditView.as_view(), name='user_edit'),
    url(r'^groups/(?P<group_id>[0-9]+)/users/$', views.UsersView.as_view(), name='group_users'),
    url(r'^groups/$', views.GroupsView.as_view(), name='groups'),
    url(r'^groups/(?P<pk>(-)?[0-9]+)/$', views.GroupView.as_view(), name='group'),
]