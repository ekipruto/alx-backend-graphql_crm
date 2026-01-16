"""
URL Configuration for GraphQL CRM
"""

from django.contrib import admin
from django.urls import path
from graphene_django.views import GraphQLView
from django.views.decorators.csrf import csrf_exempt

urlpatterns = [
    # Admin interface
    path('admin/', admin.site.urls),
    
    # GraphQL endpoint
    # csrf_exempt: Disables CSRF protection for GraphQL (development only)
    # graphiql=True: Enables the GraphiQL interactive interface
    path('graphql', csrf_exempt(GraphQLView.as_view(graphiql=True))),
]
