from django.db.models.signals import pre_save, post_save
from django.test import TestCase
from django.contrib.auth import get_user_model
from credit_line.signals import (
    capture_previous_adjustment_status,
    update_credit_line_on_approval,
)
from credit_subline.signals import (
    capture_previous_amount_adjustment_status,
    update_credit_subline_amount_on_approval,
)

User = get_user_model()


class SignalConnectionTests(TestCase):
    def test_credit_line_adjustment_signal_connections(self):
        # Verify pre_save signal is connected to the capture_previous_adjustment_status
        pre_save_receivers = [
            receiver[1]()
            for receiver in pre_save.receivers
            if receiver[1]() == capture_previous_adjustment_status
        ]
        self.assertTrue(pre_save_receivers)

        # Verify post_save signal is connected to the update_credit_line_on_approval
        post_save_receivers = [
            receiver[1]()
            for receiver in post_save.receivers
            if receiver[1]() == update_credit_line_on_approval
        ]
        self.assertTrue(post_save_receivers)

    def test_credit_amount_adjustment_signal_connections(self):
        # Verify signal connection
        pre_save_receivers = [
            receiver[1]()
            for receiver in pre_save.receivers
            if receiver[1]() == capture_previous_amount_adjustment_status
        ]
        self.assertTrue(pre_save_receivers)

        # Verify post_save signal is connected accordingly
        post_save_receivers = [
            receiver[1]()
            for receiver in post_save.receivers
            if receiver[1]() == update_credit_subline_amount_on_approval
        ]
        self.assertTrue(post_save_receivers)
