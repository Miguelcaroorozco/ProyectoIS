from django.contrib.auth import views as auth_views
from django.urls import path
from django.urls import reverse_lazy


app_name = 'autenticacion'


urlpatterns = [
    path(
        'login/',
        auth_views.LoginView.as_view(template_name='autenticacion/login.html'),
        name='login',
    ),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path(
        'password-reset/',
        auth_views.PasswordResetView.as_view(
            template_name='autenticacion/password_reset_flow.html',
            email_template_name='autenticacion/password_reset_email.html',
            subject_template_name='autenticacion/password_reset_subject.txt',
            success_url=reverse_lazy('autenticacion:password_reset_done'),
            extra_context={'password_reset_step': 'form'},
        ),
        name='password_reset',
    ),
    path(
        'password-reset/done/',
        auth_views.PasswordResetDoneView.as_view(
            template_name='autenticacion/password_reset_flow.html',
            extra_context={'password_reset_step': 'done'},
        ),
        name='password_reset_done',
    ),
    path(
        'reset/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='autenticacion/password_reset_flow.html',
            success_url=reverse_lazy('autenticacion:password_reset_complete'),
            extra_context={'password_reset_step': 'confirm'},
        ),
        name='password_reset_confirm',
    ),
    path(
        'reset/done/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='autenticacion/password_reset_flow.html',
            extra_context={'password_reset_step': 'complete'},
        ),
        name='password_reset_complete',
    ),
]
