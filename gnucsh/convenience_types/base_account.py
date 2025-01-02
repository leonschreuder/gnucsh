# pyright: reportUnknownVariableType=false, reportUnknownMemberType=false
# pyright: reportMissingTypeStubs=false, reportUnknownArgumentType=false

import re
import warnings
from datetime import date
from typing import cast

from piecash import Account, Split
from piecash.core.transaction import Decimal, Transaction
from piecash.sa_extra import DeclarativeBase
from typing_extensions import Self

from gnucsh.convenience_types.entry import Entry


class BaseAccount:
    """
    Type safe wrapper around `piecash.Account`, which also provides a more
    convenient api to create sub-elements.
    """

    backingAccount: Account
    """ Backing instance of `piecash.Account` that the BaseAccount wrapps. """

    fullname: str
    name: str

    def __init__(self, piecashAccount: Account):
        self.backingAccount = piecashAccount
        self.fullname = piecashAccount.fullname
        self.name = piecashAccount.name

    def createBankAccount(self, name: str):
        return self.createAccount(name, "BANK")

    def createExpencesAccount(self, name: str):
        return self.createAccount(name, "EXPENSE")

    def createAccount(self, name: str, type: str):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            return BaseAccount(
                Account(
                    parent=self.backingAccount,
                    name=name,
                    type=type,
                    commodity=self.backingAccount.commodity,
                )
            )

    def addEntry(
        self,
        value: str,
        description: str,
        base: Self,
        entryDate: date | None = None,
    ):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            postDate = entryDate if entryDate is not None else date.today()

            valueNum = Decimal(value)
            _ = Transaction(
                currency=self.backingAccount.commodity,
                description=description,
                post_date=postDate,
                splits=[
                    Split(value=valueNum, account=self.backingAccount),
                    Split(value=-valueNum, account=base.backingAccount),
                ],
            )

    def findEntriesWithDescription(self, matcher: str | None) -> list[Entry]:
        foundEntries: list[Entry] = []
        for e in self.getEntries():
            if matcher is None:
                foundEntries.append(e)
            else:
                if re.search(matcher, e.description) is not None:
                    foundEntries.append(e)
        return foundEntries

    def removeEntry(self, entry: Entry):
        cast(DeclarativeBase, self.backingAccount).book.delete(
            entry.backingSplit.transaction
        )

    def getEntries(self) -> list[Entry]:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            entries: list[Entry] = []
            for sp in cast(list[Split], self.backingAccount.splits):
                # "split" means an entry in the log. Convert it to a more
                # convenient helper class.
                entries.append(Entry(sp))
            return entries

    def findDuplicates(self, otherAccount: Self):
        foundPairs: list[tuple[Entry, Entry]] = []
        mainAccountEntries = self.getEntries()
        otherAccountEntries = otherAccount.getEntries()
        for mainEntry in mainAccountEntries:
            for otherEntry in otherAccountEntries:
                if (
                    mainEntry.date == otherEntry.date
                    and mainEntry.description == otherEntry.description
                    and mainEntry.otherAccount.backingAccount
                    != otherEntry.thisAccount.backingAccount
                    and otherEntry.otherAccount.backingAccount
                    != mainEntry.thisAccount.backingAccount
                ):
                    foundPairs.append((mainEntry, otherEntry))
        return foundPairs
