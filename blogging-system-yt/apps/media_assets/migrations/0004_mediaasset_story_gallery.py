from django.db import migrations, models
import django.db.models.deletion


def mark_existing_assets_featured(apps, schema_editor):
    MediaAsset = apps.get_model("media_assets", "MediaAsset")
    MediaAsset.objects.update(is_featured=True)


class Migration(migrations.Migration):
    dependencies = [("media_assets", "0003_imagesuggestion_selected")]

    operations = [
        migrations.AlterField(
            model_name="mediaasset",
            name="post",
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="images", to="blogs.post"),
        ),
        migrations.AddField(
            model_name="mediaasset",
            name="is_featured",
            field=models.BooleanField(default=False),
        ),
        migrations.RunPython(mark_existing_assets_featured, migrations.RunPython.noop),
        migrations.AlterModelOptions(name="mediaasset", options={"ordering": ["is_featured", "created_at", "id"]}),
    ]
