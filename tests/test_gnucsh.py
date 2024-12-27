# pyright: reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownArgumentType=false, reportMissingTypeStubs=false

import unittest
import os
import tempfile
import io
import contextlib
import builtins

from datetime import datetime
from gnucsh.convenience_types.ledger import openLedger
from gnucsh.gnucsh import changeTransferAccount, unifyDuplicates, listAccounts, listTransactions
from tests.testhelpers import createTestLedger, createTestLedgerWithDuplicates


class TestGnucsh(unittest.TestCase):
    def test__find_duplicates(self):
        testBookFile = os.path.join(tempfile.gettempdir(), "example.gnucash")
        createTestLedgerWithDuplicates(testBookFile)
        original_raw_input = builtins.input
        builtins.input = lambda _: 'y'

        unifyDuplicates(testBookFile, "Expenses", "Savings")

        builtins.input = original_raw_input
        with openLedger(testBookFile) as book:
            expensesAcc = book.findAccountByName("Expenses")
            savingsAcc = book.findAccountByName("Savings")

            entriesWithDescriptionInExpenses = expensesAcc.findEntriesWithDescription("some description")
            entriesWithDescriptionInSavings = savingsAcc.findEntriesWithDescription("some description")
            
            # then - have one transaction in expenses + only one in savings
            self.assertEqual(1, len(entriesWithDescriptionInExpenses))
            self.assertEqual("Savings", entriesWithDescriptionInExpenses[0].otherAccount.account_path)
            # 
            self.assertEqual(1, len(entriesWithDescriptionInSavings))

    def test__list_accounts(self):
        testBookFile = os.path.join(tempfile.gettempdir(), "example.gnucash")
        createTestLedger(testBookFile)

        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            listAccounts(testBookFile)
        self.assertMultiLineEqual(f.getvalue(), "### All Accounts ###\nExpenses\nSavings\nOpening Balance\n")

    def test__list_accounts_with_filter(self):
        testBookFile = os.path.join(tempfile.gettempdir(), "example.gnucash")
        createTestLedger(testBookFile)

        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            listAccounts(testBookFile, "pen")
        self.assertMultiLineEqual(f.getvalue(), "### Listing Accounts matching 'pen' ###\nExpenses\nOpening Balance\n")

    def test__list_transactions(self):
        testBookFile = os.path.join(tempfile.gettempdir(), "example.gnucash")
        createTestLedger(testBookFile)

        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            listTransactions(testBookFile, "Expenses")

        today = datetime.today().strftime('%Y-%m-%d')
        self.assertMultiLineEqual(f.getvalue(), """###  Account:'Expenses'  filter:'None'  ###
{}   4       Groceries                                                                                                                               Savings
{}   15      Pharmacy                                                                                                                                Savings
""".format(today, today))

    def test__should_change_transfer_account(self):
        # given
        testBookFile = os.path.join(tempfile.gettempdir(), "example.gnucash")
        createTestLedger(testBookFile)
        with openLedger(testBookFile) as book:
            imbalanceAcct = book.getRootAccount().createBankAccount("Imbalance-EUR")
            book.findAccountByName("Expenses").addEntry("10", "Some incorrectly linked expence", imbalanceAcct)
            book.save()
        original_raw_input = builtins.input
        builtins.input = lambda _: 'y'

        # when
        changeTransferAccount(testBookFile, "Expenses", "Savings", "incorrectly linked")

        # then
        with openLedger(testBookFile) as book:
            previouslyIncorrectEntry = book.findAccountByName("Expenses").findEntriesWithDescription("incorrectly.linked")
            self.assertEqual("Savings", previouslyIncorrectEntry[0].otherAccount.account_path)
        # teardown
        builtins.input = original_raw_input

