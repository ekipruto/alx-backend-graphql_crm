"""
GraphQL Schema Definition
This file defines the GraphQL schema for the application.
"""

import graphene
from crm.schema import CRMQuery


class Query(CRMQuery, graphene.ObjectType):
    """
    Root Query class
    Inherits from CRMQuery and graphene.ObjectType
    Defines all available queries in the GraphQL API
    """
    
    # Define a 'hello' field that returns a String
    hello = graphene.String()
    
    def resolve_hello(self, info):
        """
        Resolver function for the 'hello' query
        
        Args:
            self: The Query instance
            info: GraphQL execution info
            
        Returns:
            str: A greeting message
        """
        return "Hello, GraphQL!"


# Create the schema instance
schema = graphene.Schema(query=Query)
