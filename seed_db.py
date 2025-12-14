"""Populate the database with demo CRM data."""

from __future__ import annotations

import os
from decimal import Decimal

import django
from django.utils import timezone

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "graphql_crm.settings")
django.setup()

from crm.models import Customer, Order, Product  # noqa: E402  pylint: disable=wrong-import-position


def seed_customers() -> list[Customer]:
    dataset = [
        {"name": "Alice Johnson", "email": "alice@example.com", "phone": "+1234567890"},
        {"name": "Bob Smith", "email": "bob@example.com", "phone": "123-456-7890"},
        {"name": "Carol Davis", "email": "carol@example.com", "phone": "+14155550100"},
    ]
    customers: list[Customer] = []
    for entry in dataset:
        customer, _ = Customer.objects.get_or_create(
            email=entry["email"],
            defaults={"name": entry["name"], "phone": entry["phone"]},
        )
        customers.append(customer)
    return customers


def seed_products() -> list[Product]:
    dataset = [
        {"name": "Laptop", "price": Decimal("999.99"), "stock": 10},
        {"name": "Smartphone", "price": Decimal("699.00"), "stock": 25},
        {"name": "Headphones", "price": Decimal("199.50"), "stock": 40},
    ]
    products: list[Product] = []
    for entry in dataset:
        product, _ = Product.objects.get_or_create(
            name=entry["name"],
            defaults={"price": entry["price"], "stock": entry["stock"]},
        )
        products.append(product)
    return products


def seed_orders(customers: list[Customer], products: list[Product]) -> None:
    if not customers or not products:
        return
    if Order.objects.exists():
        return
    first_customer = customers[0]
    second_customer = customers[1] if len(customers) > 1 else first_customer
    order_one = Order.objects.create(customer=first_customer, order_date=timezone.now())
    order_one.products.set(products[:2])
    order_one.total_amount = sum((product.price for product in products[:2]), Decimal("0.00"))
    order_one.save(update_fields=["total_amount"])

    order_two = Order.objects.create(customer=second_customer, order_date=timezone.now())
    order_two.products.set(products[1:])
    order_two.total_amount = sum((product.price for product in products[1:]), Decimal("0.00"))
    order_two.save(update_fields=["total_amount"])


def run() -> None:
    customers = seed_customers()
    products = seed_products()
    seed_orders(customers, products)
    print("Database seeded with demo CRM data.")


if __name__ == "__main__":
    run()
