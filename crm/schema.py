import re
from decimal import Decimal
from typing import Dict, Iterable, List, Sequence

import graphene
from django.db import transaction
from django.utils import timezone
from graphene import relay
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from graphql import GraphQLError
from graphql_relay import from_global_id

from crm.filters import CustomerFilter, OrderFilter, ProductFilter
from crm.models import Customer, Order, Product
from crm.models import Product

PHONE_PATTERN = re.compile(r"^(\+\d{7,15}|\d{3}-\d{3}-\d{4})$")
CUSTOMER_ORDER_FIELDS = {"name", "email", "created_at"}
PRODUCT_ORDER_FIELDS = {"name", "price", "stock", "created_at"}
ORDER_ORDER_FIELDS = {"order_date", "total_amount", "created_at"}


def _coerce_input(input_value: Dict | None) -> Dict:
    if not input_value:
        return {}
    if isinstance(input_value, dict):
        return {key: value for key, value in input_value.items() if value not in (None, "", [])}
    if hasattr(input_value, "items"):
        return {key: value for key, value in input_value.items() if value not in (None, "", [])}
    data = {}
    if hasattr(input_value, "keys"):
        keys = input_value.keys()
    else:
        keys = [key for key in dir(input_value) if not key.startswith("_")]
    for key in keys:
        value = getattr(input_value, key, None)
        if value not in (None, "", []):
            data[key] = value
    return data


def _apply_filterset(queryset, filterset_class, filter_input):
    data = _coerce_input(filter_input)
    if not data:
        return queryset
    filterset = filterset_class(data=data, queryset=queryset)
    if filterset.form.is_valid():
        return filterset.qs.distinct()
    errors = []
    for field, messages in filterset.form.errors.items():
        errors.extend(messages)
    raise GraphQLError("; ".join(errors))


def _apply_ordering(queryset, order_by: List[str] | str | None, allowed_fields: Sequence[str]):
    if not order_by:
        return queryset
    if isinstance(order_by, str):
        requested = [value.strip() for value in order_by.split(',') if value.strip()]
    else:
        requested = [value for value in order_by if value]
    normalized = []
    for value in requested:
        key = value.lstrip('-')
        if key not in allowed_fields:
            continue
        normalized.append(value)
    return queryset.order_by(*normalized) if normalized else queryset


def _to_db_id(raw_id: str | int | None, label: str) -> int:
    if raw_id in (None, ""):
        raise GraphQLError(f"{label} ID is required.")
    try:
        return int(raw_id)
    except (TypeError, ValueError):
        try:
            _, database_id = from_global_id(raw_id)
            return int(database_id)
        except (TypeError, ValueError) as exc:
            raise GraphQLError(f"Invalid {label} ID") from exc


def _validate_phone(phone: str | None) -> None:
    if phone and not PHONE_PATTERN.match(phone):
        raise GraphQLError("Phone must match +1234567890 or 123-456-7890.")


def _ensure_unique_email(email: str) -> str:
    cleaned = email.strip()
    if not cleaned:
        raise GraphQLError("Email is required.")
    if Customer.objects.filter(email__iexact=cleaned).exists():
        raise GraphQLError("Email already exists.")
    return cleaned


def _create_customer_instance(name: str, email: str, phone: str | None = None) -> Customer:
    if not name or not name.strip():
        raise GraphQLError("Name is required.")
    normalized_email = _ensure_unique_email(email)
    _validate_phone(phone)
    return Customer.objects.create(name=name.strip(), email=normalized_email, phone=phone or "")


def _validate_price_and_stock(price: Decimal, stock: int) -> None:
    if price is None or Decimal(price) <= Decimal("0"):
        raise GraphQLError("Price must be a positive value.")
    if stock is not None and int(stock) < 0:
        raise GraphQLError("Stock cannot be negative.")


def _fetch_products(product_ids: Iterable[str | int]) -> List[Product]:
    db_ids = [_to_db_id(raw_id, "Product") for raw_id in product_ids]
    products = list(Product.objects.filter(id__in=db_ids))
    missing = set(db_ids) - {product.id for product in products}
    if missing:
        missing_str = ", ".join(str(value) for value in sorted(missing))
        raise GraphQLError(f"Invalid product ID(s): {missing_str}")
    return products


def _get_customer(raw_id: str | int) -> Customer:
    customer_id = _to_db_id(raw_id, "Customer")
    try:
        return Customer.objects.get(pk=customer_id)
    except Customer.DoesNotExist as exc:
        raise GraphQLError(f"Customer with id {customer_id} not found.") from exc


class CustomerFilterInput(graphene.InputObjectType):
    name_icontains = graphene.String()
    email_icontains = graphene.String()
    created_at_gte = graphene.DateTime()
    created_at_lte = graphene.DateTime()
    phone_pattern = graphene.String()


class ProductFilterInput(graphene.InputObjectType):
    name_icontains = graphene.String()
    price_gte = graphene.Float()
    price_lte = graphene.Float()
    stock_gte = graphene.Int()
    stock_lte = graphene.Int()


class OrderFilterInput(graphene.InputObjectType):
    total_amount_gte = graphene.Float()
    total_amount_lte = graphene.Float()
    order_date_gte = graphene.DateTime()
    order_date_lte = graphene.DateTime()
    customer_name = graphene.String()
    product_name = graphene.String()
    product_id = graphene.ID()


class CustomerInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    email = graphene.String(required=True)
    phone = graphene.String()


class ProductInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    price = graphene.Decimal(required=True)
    stock = graphene.Int(default_value=0)


class OrderInput(graphene.InputObjectType):
    customer_id = graphene.ID(required=True)
    product_ids = graphene.List(graphene.NonNull(graphene.ID), required=True)
    order_date = graphene.DateTime()


class CustomerType(DjangoObjectType):
    class Meta:
        model = Customer
        fields = ("id", "name", "email", "phone")


class CustomerNode(DjangoObjectType):
    database_id = graphene.Int()

    class Meta:
        model = Customer
        fields = ("id", "name", "email", "phone", "created_at", "updated_at")
        interfaces = (relay.Node,)

    def resolve_database_id(self, info):
        return self.id


class ProductNode(DjangoObjectType):
    database_id = graphene.Int()

    class Meta:
        model = Product
        fields = ("id", "name", "price", "stock", "created_at", "updated_at")
        interfaces = (relay.Node,)

    def resolve_database_id(self, info):
        return self.id


class OrderNode(DjangoObjectType):
    database_id = graphene.Int()

    class Meta:
        model = Order
        fields = ("id", "customer", "products", "total_amount", "order_date", "created_at", "updated_at")
        interfaces = (relay.Node,)

    def resolve_database_id(self, info):
        return self.id


class Query(graphene.ObjectType):
    hello = graphene.String(default_value="Hello, GraphQL!")
    all_customers = graphene.List(CustomerType)
    all_products = DjangoFilterConnectionField(
        ProductNode,
        filter=ProductFilterInput(),
        order_by=graphene.String(),
        filterset_class=ProductFilter,
    )
    all_orders = DjangoFilterConnectionField(
        OrderNode,
        filter=OrderFilterInput(),
        order_by=graphene.String(),
        filterset_class=OrderFilter,
    )

    def resolve_all_customers(self, info, filter=None, order_by=None, **kwargs):
        queryset = Customer.objects.all()
        queryset = _apply_filterset(queryset, CustomerFilter, filter)
        return _apply_ordering(queryset, order_by, CUSTOMER_ORDER_FIELDS)

    def resolve_all_products(self, info, filter=None, order_by=None, **kwargs):
        queryset = Product.objects.all()
        queryset = _apply_filterset(queryset, ProductFilter, filter)
        return _apply_ordering(queryset, order_by, PRODUCT_ORDER_FIELDS)

    def resolve_all_orders(self, info, filter=None, order_by=None, **kwargs):
        queryset = Order.objects.all().prefetch_related("products", "customer")
        queryset = _apply_filterset(queryset, OrderFilter, filter)
        return _apply_ordering(queryset.distinct(), order_by, ORDER_ORDER_FIELDS)


class CreateCustomer(graphene.Mutation):
    class Arguments:
        input = CustomerInput(required=True)

    customer = graphene.Field(CustomerType)
    message = graphene.String()

    @classmethod
    def mutate(cls, root, info, input):
        payload = _coerce_input(input)
        customer = _create_customer_instance(
            name=payload.get("name", ""),
            email=payload.get("email", ""),
            phone=payload.get("phone"),
        )
        return CreateCustomer(customer=customer, message="Customer created successfully.")


class BulkCreateCustomers(graphene.Mutation):
    class Arguments:
        input = graphene.List(graphene.NonNull(CustomerInput), required=True)

    customers = graphene.List(CustomerNode)
    errors = graphene.List(graphene.String)

    @classmethod
    def mutate(cls, root, info, input):
        created: List[Customer] = []
        errors: List[str] = []
        for index, payload in enumerate(input, start=1):
            try:
                normalized = _coerce_input(payload)
                with transaction.atomic():
                    customer = _create_customer_instance(
                        name=normalized.get("name", ""),
                        email=normalized.get("email", ""),
                        phone=normalized.get("phone"),
                    )
                created.append(customer)
            except GraphQLError as exc:
                errors.append(f"Row {index}: {exc.message}")
        return BulkCreateCustomers(customers=created, errors=errors)


class CreateProduct(graphene.Mutation):
    class Arguments:
        input = ProductInput(required=True)

    product = graphene.Field(ProductNode)

    @classmethod
    def mutate(cls, root, info, input):
        payload = _coerce_input(input)
        if "price" not in payload:
            raise GraphQLError("Price is required.")
        price = Decimal(str(payload.get("price")))
        stock = payload.get("stock", 0) or 0
        _validate_price_and_stock(price, stock)
        name = (payload.get("name") or "").strip()
        if not name:
            raise GraphQLError("Product name is required.")
        product = Product.objects.create(name=name, price=price, stock=stock)
        return CreateProduct(product=product)


class CreateOrder(graphene.Mutation):
    class Arguments:
        input = OrderInput(required=True)

    order = graphene.Field(OrderNode)

    @classmethod
    def mutate(cls, root, info, input):
        payload = _coerce_input(input)
        product_ids = payload.get("product_ids") or []
        if not product_ids:
            raise GraphQLError("At least one product ID is required.")
        customer = _get_customer(payload.get("customer_id"))
        products = _fetch_products(product_ids)
        order_date = payload.get("order_date") or timezone.now()
        with transaction.atomic():
            order = Order.objects.create(customer=customer, order_date=order_date)
            order.products.set(products)
            total = sum((product.price for product in products), Decimal("0.00"))
            order.total_amount = total
            order.save()
        return CreateOrder(order=order)


class UpdateLowStockProducts(graphene.Mutation):
    class Arguments:
        pass

    products = graphene.List(ProductNode)
    message = graphene.String()

    @classmethod
    def mutate(cls, root, info):
        # Query products with stock < 10
        low_stock_products = Product.objects.filter(stock__lt=10)
        
        updated_products = []
        for product in low_stock_products:
            product.stock += 10
            product.save()
            updated_products.append(product)
        
        message = f"Updated {len(updated_products)} products with low stock."
        return UpdateLowStockProducts(products=updated_products, message=message)


class Mutation(graphene.ObjectType):
    create_customer = CreateCustomer.Field()
    bulk_create_customers = BulkCreateCustomers.Field()
    create_product = CreateProduct.Field()
    create_order = CreateOrder.Field()
    update_low_stock_products = UpdateLowStockProducts.Field()
