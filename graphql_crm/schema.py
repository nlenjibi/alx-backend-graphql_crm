import graphene

from crm.schema import Mutation as CRMMutation, Query as CRMQuery


class Query(CRMQuery, graphene.ObjectType):
    """Root query combining CRM-level queries."""

    pass


class Mutation(CRMMutation, graphene.ObjectType):
    """Root mutation that exposes CRM mutations."""

    pass


schema = graphene.Schema(query=Query, mutation=Mutation)
