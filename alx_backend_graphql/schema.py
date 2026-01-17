import graphene
from crm.schema import CRMQuery, Mutation as CRMMutation


class Query(CRMQuery, graphene.ObjectType):
    """
    Root Query
    Combines all queries from different apps
    """
    # Hello field for testing
    hello = graphene.String()
    
    def resolve_hello(self, info):
        return "Hello, GraphQL!"


class Mutation(CRMMutation, graphene.ObjectType):
    """
    Root Mutation
    Combines all mutations from different apps
    """
    pass


# Create schema
schema = graphene.Schema(query=Query, mutation=Mutation)
