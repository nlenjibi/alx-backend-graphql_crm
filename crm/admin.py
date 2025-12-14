from django.contrib import admin

from crm.models import Customer, Order, Product


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
	list_display = ('name', 'email', 'phone', 'created_at')
	search_fields = ('name', 'email')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
	list_display = ('name', 'price', 'stock', 'created_at')
	search_fields = ('name',)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
	list_display = ('id', 'customer', 'order_date', 'total_amount')
	search_fields = ('customer__name', 'customer__email')
	date_hierarchy = 'order_date'
	filter_horizontal = ('products',)
