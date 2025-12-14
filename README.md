# alx-backend-graphql_crm

GraphQL-powered CRM backend built with Django, Graphene, and django-filter. The project exposes
queries, filters, and mutations to manage customers, products, and orders from a single
`/graphql` endpoint (with GraphiQL enabled for exploration).

## Requirements

- Python 3.13+
- Django 6
- graphene-django 3
- django-filter 25

Install dependencies inside the provided virtual environment:

```powershell
C:\Users\ModernTech\Desktop\django\alx\alx-backend-graphql_crm\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

> The key runtime packages (Django, graphene-django, django-filter) are already included in the
> environment. Generate `requirements.txt` via `pip freeze > requirements.txt` when needed.

## Setup

```powershell
cd C:\Users\ModernTech\Desktop\django\alx\alx-backend-graphql_crm
.venv\Scripts\python.exe manage.py migrate
.venv\Scripts\python.exe seed_db.py  # optional demo data
.venv\Scripts\python.exe manage.py runserver
```

Visit `http://localhost:8000/graphql` to access GraphiQL. Run the hello-world query to confirm the
endpoint:

```graphql
{
  hello
}
```

## Example Mutations

```graphql
mutation {
  createCustomer(
    input: { name: "Alice", email: "alice@example.com", phone: "+1234567890" }
  ) {
    customer {
      databaseId
      name
      email
      phone
    }
    message
  }
}

mutation {
  createProduct(input: { name: "Laptop", price: 999.99, stock: 10 }) {
    product {
      databaseId
      name
      price
      stock
    }
  }
}

mutation {
  createOrder(input: { customerId: "1", productIds: ["1", "2"] }) {
    order {
      databaseId
      totalAmount
      orderDate
      customer {
        name
      }
      products {
        name
        price
      }
    }
  }
}
```

## Filtering & Sorting

All list queries expose Relay connections via `edges/node`. Each query accepts a `filter` object
plus an `orderBy` argument for sorting, e.g.:

```graphql
query {
  allProducts(filter: { priceGte: 100, priceLte: 1000 }, orderBy: "-stock") {
    edges {
      node {
        databaseId
        name
        price
        stock
      }
    }
  }
}
```

Refer to `crm/schema.py` for the complete list of filter fields covering customers (name/email,
date ranges, phone patterns), products (price and stock ranges), and orders (totals, dates,
customer/product lookups).
