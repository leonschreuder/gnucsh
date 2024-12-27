# pyright: reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownArgumentType=false, reportMissingTypeStubs=false

import os
import unittest
import warnings
import tempfile

from gnucsh.convenience_types.ledger import openLedger
from tests.testhelpers import createTestLedger


class TestLedger(unittest.TestCase):

    def test__should_find_account_by_name(self):
        # given
        testBookFile = os.path.join(tempfile.gettempdir(), "example.gnucash")
        createTestLedger(testBookFile)
        with openLedger(testBookFile) as book:
            _savingsAcct2 = book.findAccountByName(
                "Savings"
            ).createBankAccount("Savings2")
            book.save()

            # when
            accExpenses = book.findAccountByName("Expenses")
            # then
            self.assertEqual("Expenses", accExpenses.fullname)

            # when
            accSavings = book.findAccountByName("Savings")
            # then
            self.assertEqual("Savings", accSavings.fullname)

            # when
            accSavings2 = book.findAccountByName("Savings:Savings2")
            # then
            self.assertEqual("Savings:Savings2", accSavings2.fullname)

    # ------------------------------------------------------------


with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    if __name__ == "__main__":
        _ = unittest.main()
