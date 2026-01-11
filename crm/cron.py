import datetime
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport


def log_crm_heartbeat():
    timestamp = datetime.datetime.now().strftime('%d/%m/%Y-%H:%M:%S')
    message = f"{timestamp} CRM is alive"

    # Optionally query the GraphQL hello field
    try:
        transport = RequestsHTTPTransport(url='http://localhost:8000/graphql')
        client = Client(transport=transport, fetch_schema_from_transport=True)
        query = gql("query { hello }")
        result = client.execute(query)
        if result.get('hello'):
            message += " - GraphQL endpoint responsive"
    except Exception as e:
        message += f" - GraphQL check failed: {str(e)}"

    with open('/tmp/crm_heartbeat_log.txt', 'a') as f:
        f.write(message + '\n')


def updatelowstock():
    # Execute the UpdateLowStockProducts mutation
    try:
        transport = RequestsHTTPTransport(url='http://localhost:8000/graphql')
        client = Client(transport=transport, fetch_schema_from_transport=True)
        mutation = gql("""
        mutation UpdateLowStock {
          updateLowStockProducts {
            products {
              name
              stock
            }
            message
          }
        }
        """)
        result = client.execute(mutation)
        
        # Log the updates
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open('/tmp/lowstockupdates_log.txt', 'a') as f:
            f.write(f"{timestamp}: {result['updateLowStockProducts']['message']}\n")
            for product in result['updateLowStockProducts']['products']:
                f.write(f"  - {product['name']}: stock now {product['stock']}\n")
    except Exception as e:
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open('/tmp/lowstockupdates_log.txt', 'a') as f:
            f.write(f"{timestamp}: Error updating low stock products: {str(e)}\n")