
from django.db import models
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

from django.contrib.postgres.fields import ArrayField

User = get_user_model()


class Category(models.Model):

    name = models.CharField(max_length=255, verbose_name='Имя Категории')
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('category_detail', kwargs={'slug': self.slug})

    def get_fields_for_filter_in_template(self):
        return ProductFeatures.objects.filter(
            category = self,
            use_in_filter=True
        ).prefetch_telated('category').value('feature_key', 'feature_measure', 'feature_name', 'filter_type')


class Product(models.Model):

    category = models.ForeignKey(Category, verbose_name='Категория', on_delete=models.CASCADE)
    title = models.CharField(max_length=255, verbose_name='Наивенование')
    slug = models.SlugField(unique=True)
    image = models.ImageField(verbose_name='Изображение')
    description = models.TextField(verbose_name='Описание', null=True)
    price = models.DecimalField(max_digits=9, decimal_places=2, verbose_name='Цена')
    pieces = ArrayField(ArrayField(models.IntegerField()))

    def __str__(self):
        return self.title

    def get_model_name(self):
        return self.__class__.__name__.lower()

    def get_absolute_url(self):
        return reverse('product_detail', kwargs={'slug': self.slug})


class ProductFeatures(models.Model):

    RADIO = 'radio'
    CHECKBOX = 'checkbox'

    FILTER_TYPE_CHOICES = {
        (RADIO, 'Радиокнопка'),
        (CHECKBOX, 'Чекбокс')
    }
    feature_key = models.CharField(max_length=100, verbose_name='Ключ характеристики')
    feature_name = models.CharField(max_length=255, verbose_name='Наименования характеристики')
    category = models.ForeignKey(Category, verbose_name='Категория', on_delete=models.CASCADE)
    postfix_for_value = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        verbose_name='Постфикс для значения',
        help_text=f'Пример для характкристики "Часы работы "'
        f'к значению работы можно добавить постфикс часов, и как результат -  значнеие " 10 часов"'
    )
    user_in_filter = models.BooleanField(
        default=False,
        verbose_name='Использовать фильтрации товаров в шаблоне'
    )
    filter_type = models.CharField(
        max_length=20,
        verbose_name='Тип фильтра',
        default=CHECKBOX,
        choices=FILTER_TYPE_CHOICES,
    )
    filter_measure = models.CharField(
        max_length=50,
        verbose_name='Еденица измерения для фильтра',
        help_text='Единица измерения для конкретного фильтра. Например "Частота процессора (Ghz).'
                  'Единицей измерения будет информация в скобках'
    )

    def __str__(self):
        return f'Каткгория -"{self.category.name}" | Характеристика - "{self.feature_name}"'


class ProductFeaturesValidator(models.Model):

    category = models.ForeignKey(Category, verbose_name='Категория', on_delete=models.CASCADE)
    feature = models.ForeignKey(ProductFeatures, verbose_name='Характкристика', null=True, blank=True, on_delete=models.CASCADE)
    feature_value = models.CharField(max_length=255, unique=True, null=True, verbose_name='Значения характеристики')

    def __str__(self):
        if not self.feature:
            return f'Валидатор категории "{self.category.name}" - Характеристика не выбрана'
        return f'Валидатор категории "{self.category.name}" |' \
                f'Характеристика - "{self.feature.feature_name}" |'\
                f'Значение - "{self.feature_value}"'


class CartProduct(models.Model):

    user = models.ForeignKey('Customer', verbose_name='Покупатель', on_delete=models.CASCADE)
    cart = models.ForeignKey('Cart', verbose_name='Корзина', on_delete=models.CASCADE, related_name='related_product')
    product = models.ForeignKey(Product, verbose_name='Товар', on_delete=models.CASCADE)
    qty = models.PositiveIntegerField(default=1)
    final_price = models.DecimalField(max_digits=9, decimal_places=2, verbose_name='Общая цена')

    def __str__(self):
        return 'Продукт: {} для корзины'.format(self.product.title)

    def save(self, *args, **kwargs):
        self.final_price = self.qty * self.product.price
        super().save(*args, **kwargs)


class Cart(models.Model):

    owner = models.ForeignKey('Customer', null=True, verbose_name='Владелец', on_delete=models.CASCADE)
    product = models.ManyToManyField(CartProduct, blank=True, related_name='related_cart')
    total_product = models.PositiveIntegerField(default=0)
    final_price = models.DecimalField(max_digits=9, default=0, decimal_places=2, verbose_name='Общая цена')
    in_order = models.BooleanField(default=False)
    for_anonymous_user = models.BooleanField(default=False)

    def __str__(self):
        return str(self.id)


class Customer(models.Model):

    user = models.ForeignKey(User, verbose_name='Пользователь', on_delete=models.CASCADE)
    phone = models.CharField(max_length=20, verbose_name='Номер телефона', null=True, blank=True)
    address = models.CharField(max_length=255, verbose_name='Адрес', null=True, blank=True)
    orders = models.ManyToManyField('Order', verbose_name='Заказы покупателя', related_name='related_customer')

    def __str__(self):
        return 'Покупатель {} {}'.format(self.user.first_name, self.user.last_name)


class Order(models.Model):

    STATUS_NEW = 'new'
    STATUS_IN_PROGRESS = 'in_progress'
    STATUS_READY = 'is_ready'
    STATUS_COMPLETED = 'completed'

    BUYING_TYPE_SELF = 'self'
    BUYING_TYPE_DELIVERY = 'delivery'

    STATUS_CHOICES = (
        (STATUS_NEW, 'Новый заказ'),
        (STATUS_IN_PROGRESS, 'Заказ в обработке'),
        (STATUS_READY, 'Заказ готов'),
        (STATUS_COMPLETED, 'Заказ выполнен')
    )

    BUYING_TYPE_CHOICES = (
        (BUYING_TYPE_SELF, 'Самовывоз'),
        (BUYING_TYPE_DELIVERY, 'Доставка')
    )

    customer = models.ForeignKey(Customer, verbose_name='Покупатель', related_name='related_orders', on_delete=models.CASCADE)
    first_name = models.CharField(max_length=250, verbose_name='Имя')
    last_name = models.CharField(max_length=255, verbose_name='Фамилия')
    phone = models.CharField(max_length=20, verbose_name='Телефон')
    cart = models.ForeignKey(Cart, verbose_name='Корзина', on_delete=models.CASCADE, null=True, blank=True)
    address = models.CharField(max_length=1024, verbose_name='Адрес', null=True, blank=True)
    status = models.CharField(
        max_length=100,
        verbose_name='Статус заказа',
        choices=STATUS_CHOICES,
        default=STATUS_NEW
    )
    buying_type = models.CharField(
        max_length=100,
        verbose_name='Тип заказа',
        choices=BUYING_TYPE_CHOICES,
        default=BUYING_TYPE_SELF
    )
    comment = models.TextField(verbose_name='Комментарий к зааказу', null=True, blank=True)
    created_at = models.DateTimeField(auto_now=True, verbose_name='Дата заказа товара')
    order_date = models.DateField(verbose_name='Дата получения заказа', default=timezone.now)

    def __str__(self):
        return str(self.id)
