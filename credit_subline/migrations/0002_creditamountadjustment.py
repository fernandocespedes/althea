# Generated by Django 5.0.6 on 2024-06-24 18:53

import credit_line.models
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('credit_subline', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CreditAmountAdjustment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('initial_amount', models.DecimalField(decimal_places=2, max_digits=12)),
                ('adjusted_amount', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ('effective_date', models.DateField(default=credit_line.models.current_date)),
                ('reason_for_adjustment', models.TextField()),
                ('adjustment_status', models.CharField(choices=[('pending_review', 'Pending Review'), ('approved', 'Approved'), ('rejected', 'Rejected'), ('implemented', 'Implemented')], default='pending_review', max_length=20)),
                ('credit_subline', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='amount_adjustments', to='credit_subline.creditsubline')),
            ],
            options={
                'ordering': ['-effective_date'],
            },
        ),
    ]
