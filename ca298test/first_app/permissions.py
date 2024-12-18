from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.decorators import user_passes_test

def admin_required(function=None, redirect_field=REDIRECT_FIELD_NAME, login_url='login'):
    decorator = user_passes_test(
        lambda u: u.is_active and u.is_admin,
        login_url = login_url,
        redirect_field_name = redirect_field
    )

    if function:
        return decorator(function)
    return decorator
