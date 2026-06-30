"""Update django_content_type rows so moved models point to their new apps."""
from django.db import migrations


MODEL_APP_MAP = {
    'farmerprofile': 'accounts',
    'subsidyapplication': 'accounts',
    'cooperative': 'products',
    'product': 'products',
    'productbatch': 'products',
    'review': 'products',
    'traceevent': 'traceability',
    'order': 'trade',
    'orderitem': 'trade',
    'cart': 'trade',
    'cartitem': 'trade',
    'favorite': 'trade',
    'logisticsevent': 'trade',
    'supplydemandpost': 'marketplace',
    'farmingguide': 'knowledge',
    'preordercampaign': 'preorder',
    'preorder': 'preorder',
    'notification': 'notifications',
}

# These models stay in core — ensure their app_label is correct
STAY_IN_CORE = ['announcement', 'training']


def update_content_types(apps, schema_editor):
    ContentType = apps.get_model('contenttypes', 'ContentType')
    for model_name, new_app in MODEL_APP_MAP.items():
        updated = ContentType.objects.filter(
            app_label='core', model=model_name
        ).update(app_label=new_app)
        if updated:
            print(f"  {model_name}: core -> {new_app}")


def reverse_content_types(apps, schema_editor):
    ContentType = apps.get_model('contenttypes', 'ContentType')
    for model_name, new_app in MODEL_APP_MAP.items():
        ContentType.objects.filter(
            app_label=new_app, model=model_name
        ).update(app_label='core')


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0014_remove_cartitem_cart_remove_cartitem_product_and_more'),
        ('accounts', '0002_initial'),
        ('products', '0002_initial'),
        ('traceability', '0001_initial'),
        ('trade', '0001_initial'),
        ('marketplace', '0001_initial'),
        ('knowledge', '0001_initial'),
        ('preorder', '0001_initial'),
        ('notifications', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(update_content_types, reverse_content_types),
    ]
