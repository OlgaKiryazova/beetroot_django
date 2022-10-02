from django.contrib import admin

from . models import Age, Category,  Product, Image


class ProductAdmin(admin.ModelAdmin):
    list_display = ('title', 'price')
    prepopulated_fields = {'slug': ('title',)}


admin.site.register(Category)

admin.site.register(Product, ProductAdmin)
admin.site.register(Image)
# admin.site.register(Reviews)
admin.site.register(Age)