from datetime import datetime
from celery import shared_task
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

@shared_task
def generate_crm_report():
    transport = RequestsHTTPTransport(url='http://localhost:8000/graphql')
    client = Client(transport=transport, fetch_schema_from_transport=True)
    query = gql('''
    query CRMReport {
      totalCustomers: allCustomers { totalCount }
      totalOrders: allOrders { totalCount }
      orders: allOrders { edges { node { totalAmount } } }
    }
    ''')
    result = client.execute(query)
    total_customers = result['totalCustomers']['totalCount']
    total_orders = result['totalOrders']['totalCount']
    total_revenue = sum(edge['node']['totalAmount'] for edge in result['orders']['edges'])
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open('/tmp/crmreportlog.txt', 'a') as f:
      f.write(f"{timestamp} - Report: {total_customers} customers, {total_orders} orders, {total_revenue} revenue\n")
