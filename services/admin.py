from django.contrib import admin
from .models import (
    Shop,
    Goods,
    ShoppingCart,
    CartItem,
    Order,
    OrderItem,
    DiscountCoupon,
)

admin.site.register(Shop)
admin.site.register(ShoppingCart)
admin.site.register(CartItem)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(DiscountCoupon)


@admin.register(Goods)
class GoodsAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "price",
        "shop_name",
    )
