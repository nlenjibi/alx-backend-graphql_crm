#!/usr/bin/env python3

import datetime
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

# GraphQL endpoint
transport = RequestsHTTPTransport(url='http://localhost:8000/graphql')
client = Client(transport=transport, fetch_schema_from_transport=True)

# Query for orders in the last 7 days
seven_days_ago = (datetime.datetime.now() - datetime.timedelta(days=7)).isoformat()

query = gql(f"""
query GetRecentOrders {{
  allOrders(filter: {{orderDateGte: "{seven_days_ago}"}}) {{
    edges {{
      node {{
        databaseId
        customer {{
          email
        }}
      }}
    }}
  }}
}}
""")

result = client.execute(query)

# Log the results
with open('/tmp/order_reminders_log.txt', 'a') as f:
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    for edge in result['allOrders']['edges']:
        order = edge['node']
        f.write(f"{timestamp}: Order ID {order['databaseId']}, Customer Email {order['customer']['email']}\n")

print("Order reminders processed!")