from django.contrib import admin

# Register your models here.

from django.contrib import admin
from django.db.models import Count
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group
from django.contrib.auth.admin import GroupAdmin
from django.utils.html import format_html

from .forms import CustomUserCreationForm, CustomUserChangeForm
from .models import CustomUser



# ATTN: 9/20/25 Fix for error manually adding user complaining about "Unknown field(s) (usable_password)"; we need to avoid adding this to derived user admin
def cleanUserAdminAddFieldsets():
    cleaned = []
    for name, opts in UserAdmin.add_fieldsets:
        opts = opts.copy()  # copy to avoid mutating original
        if "fields" in opts:
            opts["fields"] = tuple(f for f in opts["fields"] if f != "usable_password")
        cleaned.append((name, opts))
    return cleaned




class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = CustomUser

    ordering = ('-date_joined',)  # Sort by date_joined in descending order
    list_display = UserAdmin.list_display + ("date_joined", "bggname", "webpage", "is_staff", "group_list",)
    fieldsets = UserAdmin.fieldsets + ((None, {"fields": ("bggname","webpage",)}),)
    add_fieldsets = cleanUserAdminAddFieldsets() + [(None, {"fields": ("bggname","webpage",)}),]



    def get_queryset(self, request):
        # Annotate the queryset with the number of groups per user
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(groups_count=Count('groups'))
        return queryset

    def group_list(self, obj):
        # Retrieves all groups for the user and formats them as a comma-separated list.
        groups = obj.groups.all()
        if groups:
            return format_html("<br>".join([group.name for group in groups]))
        return "-"  # Return a placeholder or empty string if no groups

    # Add sorting capability to the formatted_groups column
    group_list.admin_order_field = 'groups_count'  # Allows sorting by the annotated field












# Unregister the original User admin and register the custom one
#admin.site.unregister(User)
#admin.site.register(User, UserAdmin)
#admin.site.unregister(CustomUser)
admin.site.register(CustomUser, CustomUserAdmin)





# add list of users in each group to the group admin page
class CustomGroupAdmin(GroupAdmin):
    def users(self, obj):
        # Retrieves all users in the group and formats them as a comma-separated list.
        users = obj.user_set.all()
        return format_html("<br>".join([user.username for user in users]))

    # Adding the users method to list_display to show it in the admin list view
    list_display = GroupAdmin.list_display + ("users",)



# Unregister the original admin and register the custom one
admin.site.unregister(Group)
admin.site.register(Group, CustomGroupAdmin)


