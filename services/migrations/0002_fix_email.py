from django.db import migrations

def fix_email(apps, schema_editor):
    EmailAddress = apps.get_model('account', 'EmailAddress')
    for email in EmailAddress.objects.all():
        if email.email != email.email.lower():
            email.email = email.email.lower()
            email.save()

class Migration(migrations.Migration):

    dependencies = [
        ('services', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(fix_email),
    ]
