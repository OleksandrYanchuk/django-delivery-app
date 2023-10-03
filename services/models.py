import random

from django.db import models

from user.models import Customer


class Shop(models.Model):
    name = models.CharField(max_length=255, unique=True)
    lat = models.FloatField(null=True, blank=True)
    lng = models.FloatField()

    def __str__(self):
        return self.name


class Goods(models.Model):
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    shop_name = models.ForeignKey(Shop, related_name="goods", on_delete=models.CASCADE)

    def __str__(self):
        return self.name

    class Meta:
        unique_together = ["name", "shop_name"]


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        Customer, on_delete=models.CASCADE
    )  # Посилання на користувача, який володіє кошиком
    goods = models.ManyToManyField(
        "Goods", through="CartItem"
    )  # Товари в кошику через проміжну модель

    def __str__(self):
        return f"Shopping Cart for {self.user.name}"


class CartItem(models.Model):
    shopping_cart = models.ForeignKey(
        ShoppingCart, on_delete=models.CASCADE
    )  # Посилання на кошик
    goods = models.ForeignKey("Goods", on_delete=models.CASCADE)  # Посилання на товар
    quantity = models.PositiveIntegerField(default=1)  # Кількість товару в кошику
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.quantity} x {self.goods.name}"

    def total_price(self):
        return self.quantity * self.goods.price


class Order(models.Model):
    user = models.ForeignKey(Customer, on_delete=models.CASCADE)
    goods = models.ManyToManyField(Goods, through="OrderItem")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    total_with_discount = models.DecimalField(
        max_digits=10, decimal_places=2, default=None, blank=True, null=True
    )

    def __str__(self):
        return f"Order #{self.id} by {self.user.name}"

    def save(self, *args, **kwargs):
        if self.total_with_discount is None:
            self.total_with_discount = self.total_amount
        super().save(*args, **kwargs)


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order, related_name="order_items", on_delete=models.CASCADE
    )
    product = models.ForeignKey(Goods, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()


class DiscountCoupon(models.Model):
    code = models.CharField(max_length=50, unique=True)  # Унікальний код купону
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE)  # Посилання на магазин
    user = models.ForeignKey(
        Customer, on_delete=models.CASCADE
    )  # Посилання на користувача
    discount_percentage = models.PositiveIntegerField()  # Відсоток знижки
    is_used = models.BooleanField(default=False)  # Позначка про використання купону

    def __str__(self):
        return f"Coupon for {self.shop.name} owned by {self.user.name}"

    @classmethod
    def create_random_coupon(cls, user):
        shop = Shop.objects.order_by("?").first()  # Вибираємо рандомний магазин
        discount_percentage = random.randint(5, 20)  # Генеруємо рандомний відсоток
        code = "".join(
            random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", k=10)
        )  # Генеруємо рандомний код

        coupon = cls.objects.create(
            code=code, shop=shop, user=user, discount_percentage=discount_percentage
        )

        return coupon
