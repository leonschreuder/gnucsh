# pyright: reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownArgumentType=false, reportMissingTypeStubs=false

from datetime import datetime
import unittest
import os
import tempfile

from gnucsh.convenience_types.ledger import openLedger
from tests.testhelpers import createTestLedger, createTestLedgerWithDuplicates


class TestBaseAccount(unittest.TestCase):

    def test__should_filter_entries(self):
        # given
        testBookFile = os.path.join(tempfile.gettempdir(), "example.gnucash")
        createTestLedger(testBookFile)
        filter = "Gro.*ies"
        with openLedger(testBookFile) as book:
            expensesAcct = book.findAccountByName("Expenses")

            # when
            entries = expensesAcct.findEntriesWithDescription(filter)

            # then
            self.assertEqual(1, len(entries))
            self.assertEqual("Groceries", entries[0].description)

    def test__should_find_all_entries(self):
        # given
        testBookFile = os.path.join(tempfile.gettempdir(), "example.gnucash")
        createTestLedger(testBookFile)
        with openLedger(testBookFile) as book:
            acc = book.findAccountByName("Expenses")

            # when
            entries = acc.getEntries()

            # then
            self.assertEqual(2, len(entries))
            self.assertEqual("Groceries", entries[0].description)
            self.assertEqual("Savings", entries[0].account_path)
            self.assertEqual("4.00", entries[0].value)
            self.assertEqual("Pharmacy", entries[1].description)
            self.assertEqual("Savings", entries[1].account_path)
            self.assertEqual("15.00", entries[1].value)

    def test__add_entry(self):
        testBookFile = os.path.join(tempfile.gettempdir(), "example.gnucash")
        customDate = datetime.strptime("2024-12-09", "%Y-%m-%d").date()
        createTestLedger(testBookFile)
        with openLedger(testBookFile) as book:
            expensesAcct = book.findAccountByName("Expenses")
            savingsAcc = book.findAccountByName("Savings")
            expensesAcct.addEntry("10", "description1", savingsAcc)
            expensesAcct.addEntry("10", "description2", savingsAcc, customDate)
            book.save()

        with openLedger(testBookFile) as book:
            expensesAcct = book.findAccountByName("Expenses")
            self.assertEqual(
                1, len(expensesAcct.findEntriesWithDescription("description1"))
            )
            assert 1 == len(
                expensesAcct.findEntriesWithDescription("description2")
            )
            assert (
                customDate
                == expensesAcct.findEntriesWithDescription("description2")[
                    0
                ].date
            )

    def test__remove_entry(self):
        testBookFile = os.path.join(tempfile.gettempdir(), "example.gnucash")
        createTestLedger(testBookFile)
        with openLedger(testBookFile) as book:
            expensesAcct = book.findAccountByName("Expenses")
            entries = expensesAcct.findEntriesWithDescription("Gro.*ies")
            self.assertEqual(1, len(entries))

            expensesAcct.removeEntry(entries[0])

            book.save()  # might cause problems if removing is incorrect

        with openLedger(testBookFile) as book:
            expensesAcct = book.findAccountByName("Expenses")
            self.assertEqual(
                0, len(expensesAcct.findEntriesWithDescription("Gro.*ies"))
            )

    def test__find_duplicates(self):
        # given
        testBookFile = os.path.join(tempfile.gettempdir(), "example.gnucash")
        createTestLedgerWithDuplicates(testBookFile)
        with openLedger(testBookFile) as ledger:
            expensesAcc = ledger.findAccountByName("Expenses")
            savingsAcc = ledger.findAccountByName("Savings")

            # when
            foundPairs = expensesAcc.findDuplicates(savingsAcc)

            # then
            self.assertEqual(1, len(foundPairs))
            first = foundPairs[0][0]
            second = foundPairs[0][1]
            self.assertEqual(
                second.description,
                first.description,
                "should have same description",
            )
            # first is expenses to imbalance
            self.assertEqual("Expenses", first.thisAccount.account_path)
            self.assertEqual("Imbalance-EUR", first.otherAccount.account_path)
            # first is savings to imbalance
            self.assertEqual("Savings", second.thisAccount.account_path)
            self.assertEqual("Imbalance-EUR", second.otherAccount.account_path)
            # reverse value for each
            self.assertEqual("10.00", first.value)
            self.assertEqual("-10.00", second.value)
