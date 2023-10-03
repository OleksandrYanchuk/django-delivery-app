from django.urls import path
from .views import (
    ShopListView,
    ShopDetailView,
    CreateShopView,
    GoodsListView,
    CreateGoodsView,
    ShoppingCartDetailView,
    CartItemView,
    CartItemDetailView,
    ShopGoodsDetailView,
    add_to_cart,
    shopping_cart,
    update_cart_item,
    remove_cart_item,
    OrderCreateView,
    OrderListView,
    OrderDetailView,
    OrderItemDetailView,
    update_user_info,
    active_coupons,
    apply_coupon,
)

urlpatterns = [
    path("shops/", ShopListView.as_view(), name="shop_list"),
    path("shops/<int:pk>/", ShopDetailView.as_view(), name="shop_detail"),
    path(
        "shops/<int:pk>/goods/", ShopGoodsDetailView.as_view(), name="shop_goods_detail"
    ),
    path("shops/create/", CreateShopView.as_view(), name="create_shop"),
    path("goods/", GoodsListView.as_view(), name="goods_list"),
    path("goods/create/", CreateGoodsView.as_view(), name="create_goods"),
    path("shopping-cart/", shopping_cart, name="shopping_cart"),
    path(
        "shopping-cart/<int:pk>/",
        ShoppingCartDetailView.as_view(),
        name="shopping_cart_detail",
    ),
    path("cart-item/", CartItemView.as_view(), name="cart_item"),
    path("cart-item/<int:pk>/", CartItemDetailView.as_view(), name="cart_item_detail"),
    path("add_to_cart/", add_to_cart, name="add_to_cart"),
    path("update_cart_item/", update_cart_item, name="update_cart_item"),
    path("remove_cart_item/", remove_cart_item, name="remove_cart_item"),
    path("order-create/", OrderCreateView.as_view(), name="order_create"),
    path("order-list/", OrderListView.as_view(), name="order_list"),
    path("order-detail/<int:pk>/", OrderDetailView.as_view(), name="order_detail"),
    path(
        "order-item/<int:pk>/", OrderItemDetailView.as_view(), name="order_item_detail"
    ),
    path("update-user-info/", update_user_info, name="update_user_info"),
    path("generate-coupon/", active_coupons, name="generate_coupon"),
    path("apply_coupon/", apply_coupon, name="apply_coupon"),
]

app_name = "services"
