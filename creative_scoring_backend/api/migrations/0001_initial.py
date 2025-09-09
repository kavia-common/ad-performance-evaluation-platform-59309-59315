from django.db import migrations, models
import django.db.models.deletion
import api.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='Audience',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=255, unique=True)),
                ('description', models.TextField(blank=True)),
                ('size', models.PositiveIntegerField(default=10000)),
                ('traits', models.JSONField(blank=True, default=dict)),
            ],
        ),
        migrations.CreateModel(
            name='ScoreWeighting',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(default='default', max_length=128, unique=True)),
                ('brand_lift_weight', models.FloatField(default=0.34)),
                ('performance_weight', models.FloatField(default=0.33)),
                ('attention_weight', models.FloatField(default=0.33)),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={
                'verbose_name': 'Score Weighting',
                'verbose_name_plural': 'Score Weightings',
            },
        ),
        migrations.CreateModel(
            name='Creative',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('title', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True)),
                ('creative_type', models.CharField(choices=[('mp4', 'MP4 Video'), ('image', 'Image (JPG/PNG)'), ('html5', 'HTML5 Zip/Bundle')], max_length=16)),
                ('file', models.FileField(blank=True, null=True, upload_to=api.models.creative_upload_path)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='creatives', to='auth.user')),
            ],
        ),
        migrations.CreateModel(
            name='Scorecard',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('brand_lift', models.FloatField()),
                ('performance', models.FloatField()),
                ('attention', models.FloatField()),
                ('composite', models.FloatField()),
                ('weights_snapshot', models.JSONField(blank=True, default=dict)),
                ('breakdown_labels', models.JSONField(blank=True, default=dict)),
                ('extra', models.JSONField(blank=True, default=dict)),
                ('audience', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='scorecards', to='api.audience')),
                ('creative', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='scorecards', to='api.creative')),
            ],
            options={
                'unique_together': {('creative', 'audience')},
            },
        ),
        migrations.CreateModel(
            name='Recommendation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('text', models.TextField()),
                ('priority', models.PositiveSmallIntegerField(default=2)),
                ('category', models.CharField(blank=True, max_length=128)),
                ('scorecard', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='recommendations', to='api.scorecard')),
            ],
        ),
        migrations.CreateModel(
            name='ComparativeTest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('lift_projection', models.JSONField(blank=True, default=dict)),
                ('result_summary', models.TextField(blank=True)),
                ('audience', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='comparative_tests', to='api.audience')),
                ('creative_a', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='comparisons_as_a', to='api.creative')),
                ('creative_b', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='comparisons_as_b', to='api.creative')),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='comparative_tests', to='auth.user')),
            ],
        ),
    ]
