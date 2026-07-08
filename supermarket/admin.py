from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Supplier, Product, Customer, Order, OrderItem


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'description')
    search_fields = ('name',)


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('id', 'company_name', 'contact_person', 'phone', 'email')
    search_fields = ('company_name', 'phone', 'email')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'image_preview', 'name', 'category', 'price', 'cost_price', 'stock', 'barcode')
    list_filter = ('category',)
    search_fields = ('name', 'barcode')
    readonly_fields = ('image_preview_large',)

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="width: 48px; height: 48px; object-fit: cover; border-radius: 8px;" />',
                obj.image.url,
            )
        return '—'

    image_preview.short_description = 'Image'

    def image_preview_large(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-width: 240px; max-height: 240px; object-fit: contain; border-radius: 12px;" />',
                obj.image.url,
            )
        return 'No image uploaded'

    image_preview_large.short_description = 'Current Image'


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('id', 'full_name', 'phone', 'email')
    search_fields = ('full_name', 'phone', 'email')


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'user', 'date_ordered', 'total_amount')
    list_filter = ('date_ordered',)
    search_fields = ('customer__full_name',)
    inlines = [OrderItemInline]


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'product', 'quantity', 'price')
