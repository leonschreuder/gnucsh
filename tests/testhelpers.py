import os

from gnucsh.convenience_types.ledger import createLedger, openLedger

def createTestLedger(file: str):
    if os.path.isfile(file):
        os.remove(file)

    with createLedger(file) as book:
        rootAcct = book.getRootAccount()

        expensesAcct = rootAcct.createExpencesAccount("Expenses")
        savingsAcct = rootAcct.createBankAccount("Savings")
        openingAcct = rootAcct.createAccount("Opening Balance", "EQUITY")

        expensesAcct.addEntry("4", "Groceries", savingsAcct)
        savingsAcct.addEntry("100", "Opening Savings Balance", openingAcct)
        expensesAcct.addEntry("15", "Pharmacy", savingsAcct)

        book.save()

def createTestLedgerWithDuplicates(testBookFile: str):
    createTestLedger(testBookFile)
    with openLedger(testBookFile) as ledger:
        expensesAcc = ledger.findAccountByName("Expenses")
        savingsAcc = ledger.findAccountByName("Savings")
        imbalanceAcct = ledger.getRootAccount().createBankAccount("Imbalance-EUR")

        expensesAcc.addEntry("10", "some description", imbalanceAcct)
        savingsAcc.addEntry("-10", "some description", imbalanceAcct)
        ledger.save()

