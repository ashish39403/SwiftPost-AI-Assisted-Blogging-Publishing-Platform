from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("media_assets", "0002_imagesuggestion")]

    operations = [
        migrations.AddField(
            model_name="imagesuggestion",
            name="selected",
            field=models.BooleanField(default=False),
        ),
    ]
