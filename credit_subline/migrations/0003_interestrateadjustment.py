# Generated by Django 5.0.6 on 2024-06-25 03:39

import credit_line.models
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('credit_subline', '0002_creditamountadjustment'),
    ]

    operations = [
        migrations.CreateModel(
            name='InterestRateAdjustment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('initial_interest_rate', models.DecimalField(decimal_places=3, max_digits=6)),
                ('adjusted_interest_rate', models.DecimalField(decimal_places=3, max_digits=6)),
                ('effective_date', models.DateField(default=credit_line.models.current_date)),
                ('reason_for_adjustment', models.TextField()),
                ('adjustment_status', models.CharField(choices=[('pending_review', 'Pending Review'), ('approved', 'Approved'), ('rejected', 'Rejected'), ('implemented', 'Implemented')], default='pending_review', max_length=20)),
                ('credit_subline', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='interest_rate_adjustments', to='credit_subline.creditsubline')),
            ],
            options={
                'ordering': ['-effective_date'],
            },
        ),
    ]
