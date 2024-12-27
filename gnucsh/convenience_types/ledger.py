# pyright: reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownArgumentType=false, reportMissingTypeStubs=false

from typing import cast

from piecash import Account, Book, create_book, open_book

from gnucsh.convenience_types.base_account import BaseAccount


class Ledger:
    """
    Class representing a single GnuCash file. This is a convenience wrapper
    around the `piecash.Book` class.
    """

    backingBook: Book
    """ Backing instance of `piecash.Book` that the Ledge wrapps. """

    def __init__(self, book: Book):
        self.backingBook = book

    def findAccountByName(self, targetName: str) -> BaseAccount:
        if ":" in targetName:
            return BaseAccount(self.backingBook.accounts(fullname=targetName))
        else:
            return BaseAccount(self.backingBook.accounts(name=targetName))

    def getAllAccounts(self):
        allAccounts: list[Account] = self.backingBook.accounts
        finalAccounts: list[BaseAccount] = []
        for acc in allAccounts:
            finalAccounts.append(BaseAccount(acc))
        return finalAccounts

    def getRootAccount(self):
        return BaseAccount(cast(Account, self.backingBook.root_account))

    def save(self):
        self.backingBook.save()

    def flush(self):
        self.backingBook.flush()

    # add context manager that close the session when leaving
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.backingBook.__exit__(exc_type, exc_val, exc_tb)


def openLedger(file: str) -> Ledger:
    return Ledger(
        cast(Book, open_book(file, readonly=False, open_if_lock=True))
    )


def createLedger(file: str) -> Ledger:
    return Ledger(create_book(file, overwrite=True))
