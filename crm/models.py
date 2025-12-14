from decimal import Decimal

from django.db import models
from django.utils import timezone


class TimeStampedModel(models.Model):
	"""Abstract base model that tracks creation and update timestamps."""

	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		abstract = True


class Customer(TimeStampedModel):
	name = models.CharField(max_length=255)
	email = models.EmailField(unique=True)
	phone = models.CharField(max_length=32, blank=True)

	def __str__(self) -> str:
		return f"{self.name} <{self.email}>"


class Product(TimeStampedModel):
	name = models.CharField(max_length=255)
	price = models.DecimalField(max_digits=10, decimal_places=2)
	stock = models.PositiveIntegerField(default=0)

	def __str__(self) -> str:
		return self.name


class Order(TimeStampedModel):
	customer = models.ForeignKey(Customer, related_name='orders', on_delete=models.CASCADE)
	products = models.ManyToManyField(Product, related_name='orders')
	order_date = models.DateTimeField(default=timezone.now)
	total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))

	def __str__(self) -> str:
		return f"Order #{self.pk}"

	def recalculate_total(self) -> None:
		"""Recompute order total using current product prices."""
		total = sum((product.price for product in self.products.all()), Decimal('0.00'))
		self.total_amount = total
		self.save(update_fields=['total_amount'])
