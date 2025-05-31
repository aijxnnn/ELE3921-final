from django.contrib import admin
from .models import MenuItem, Order, MenuItemSize, PizzaTopping

admin.site.register(Order)

class PizzaToppingInline(admin.TabularInline):
    model = PizzaTopping
    fk_name = 'pizza'
    extra = 1 
    autocomplete_fields = ['topping']

class MenuItemSizeInline(admin.TabularInline):
    model = MenuItemSize
    extra = 1

class MenuItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'category')
    list_filter = ('category',)
    search_fields = ['name']
    inlines = [MenuItemSizeInline]
    def get_inlines(self, request, obj=None):
        if obj and obj.category == 'pizza':
            return [MenuItemSizeInline, PizzaToppingInline]
        return [MenuItemSizeInline]

admin.site.register(MenuItem, MenuItemAdmin)

