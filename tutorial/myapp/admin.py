from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(ZippedFolder)


@admin.register(AccountProfile)
class AccountProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'managed_by', 'prefix', 'lock_at', 'delete_at', 'created_at')
    list_filter = ('managed_by', 'prefix')
    search_fields = ('user__username',)


@admin.register(AccountPrefix)
class AccountPrefixAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'created_at')
    search_fields = ('name', 'owner__username')
