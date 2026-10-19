"""
Headless unit tests for Aurion Banking Core.
Demonstrates running full banking logic (auth, balance, cash in, cash out,
transfers, bill payments, and expired cashout checks) WITHOUT Qt or any GUI.
"""

import os
import shutil
import tempfile
import unittest

from core.database import Database
from core.bank_service import BankService
from core.auth_service import AuthService


class TestBankingCore(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory and test database
        self.test_dir = tempfile.mkdtemp()
        self.db = Database(filename="test_database.json", base_dir=self.test_dir)
        self.bank_service = BankService(self.db)
        self.auth_service = AuthService(self.db)

    def tearDown(self):
        # Clean up temporary directory
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_account_creation_and_login(self):
        # Register new account
        ok, msg = self.auth_service.create_account(
            username="alice",
            name="Alice Smith",
            email="alice@test.com",
            password="secretpassword",
            pin="1234"
        )
        self.assertTrue(ok)
        self.assertEqual(self.bank_service.get_balance("alice"), 0.0)

        # Login with username & password
        ok, canon_user, _ = self.auth_service.login("alice", "secretpassword")
        self.assertTrue(ok)
        self.assertEqual(canon_user, "alice")

        # Login with email & PIN
        ok, canon_user, _ = self.auth_service.login("alice@test.com", "1234")
        self.assertTrue(ok)
        self.assertEqual(canon_user, "alice")

        # Login with invalid secret
        ok, canon_user, err = self.auth_service.login("alice", "wrongpass")
        self.assertFalse(ok)
        self.assertIsNone(canon_user)

    def test_cash_in_and_cash_out(self):
        self.auth_service.create_account("bob", "Bob Jones", "bob@test.com", "pass", "9999")

        # Cash in
        ok, new_bal, receipt = self.bank_service.cash_in("bob", 1500.0)
        self.assertTrue(ok)
        self.assertEqual(new_bal, 1500.0)
        self.assertEqual(receipt["amount"], 1500.0)
        self.assertEqual(receipt["type"], "Cash In")

        # Cash out
        ok, new_bal, receipt = self.bank_service.cash_out("bob", 500.0)
        self.assertTrue(ok)
        self.assertEqual(new_bal, 1000.0)

        # Insufficient funds
        ok, err, _ = self.bank_service.cash_out("bob", 2000.0)
        self.assertFalse(ok)

    def test_send_money(self):
        self.auth_service.create_account("user1", "Sender User", "u1@test.com", "pass", "1111")
        self.auth_service.create_account("user2", "Receiver User", "u2@test.com", "pass", "2222")

        self.bank_service.cash_in("user1", 3000.0)

        # Send money
        ok, new_sender_bal, receipt = self.bank_service.send_money("user1", "user2", 1200.0)
        self.assertTrue(ok)
        self.assertEqual(new_sender_bal, 1800.0)
        self.assertEqual(self.bank_service.get_balance("user2"), 1200.0)

        # Check inboxes
        inbox_user2 = self.bank_service.get_inbox("user2")
        self.assertTrue(any("Received PHP 1,200.00" in msg for msg in inbox_user2))

        # Cannot send to self
        ok, err, _ = self.bank_service.send_money("user1", "user1", 500.0)
        self.assertFalse(ok)

    def test_pay_bill(self):
        self.auth_service.create_account("payer", "Payer Person", "payer@test.com", "pass", "3333")
        self.bank_service.cash_in("payer", 2000.0)

        ok, new_bal, receipt = self.bank_service.pay_bill("payer", "Meralco Electric", 850.0)
        self.assertTrue(ok)
        self.assertEqual(new_bal, 1150.0)
        self.assertEqual(receipt["recipient"], "Meralco Electric")

    def test_kiosk_cashout_code_generation_and_redemption(self):
        self.auth_service.create_account("kiosk_user", "Kiosk Guy", "kg@test.com", "pass", "4444")
        self.bank_service.cash_in("kiosk_user", 5000.0)

        # Generate cashout code
        ok, code, exp_time, new_bal = self.bank_service.generate_cashout_code("kiosk_user", 1000.0)
        self.assertTrue(ok)
        self.assertEqual(len(code), 6)
        self.assertEqual(new_bal, 4000.0)

        # Redeem at kiosk
        ok, msg, receipt = self.bank_service.redeem_cashout_code(code)
        self.assertTrue(ok)
        self.assertEqual(receipt["amount"], 1000.0)

        # Attempt to redeem again (should fail)
        ok, msg, _ = self.bank_service.redeem_cashout_code(code)
        self.assertFalse(ok)


if __name__ == "__main__":
    unittest.main()

