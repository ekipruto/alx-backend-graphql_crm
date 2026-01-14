"""
GraphQL Schema Definition
This file defines the GraphQL schema for the CRM application.
"""

import graphene


class Query(graphene.ObjectType):
    """
    Root Query class
    Defines all available queries in the GraphQL API
    """
    
    # Define a 'hello' field that returns a String
    hello = graphene.String()
    
    def resolve_hello(self, info):
        """
        Resolver function for the 'hello' query
        This function is automatically called when 'hello' is queried
        
        Args:
            self: The Query instance
            info: GraphQL execution info (context, variables, etc.)
            
        Returns:
            str: A greeting message
        """
        return "Hello, GraphQL!"


# Create the schema instance
schema = graphene.Schema(query=Query)
