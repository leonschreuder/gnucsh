# pyright: reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownArgumentType=false, reportMissingTypeStubs=false

import datetime
from typing import cast
from typing_extensions import override
from piecash.core.account import Account
from piecash.core.transaction import CallableList, Split, Transaction


class EntryAccount:
    description: str
    value: str
    account_path: str

    backingAccount: Account
    _split: Split

    def __init__(self, split : Split):
        self._split = split
        self.backingAccount = cast(Account, split.account)
        
        self.value = str(split.value)
        self.description = self.backingAccount.description
        self.account_path = self.backingAccount.fullname

    def setAccountPath(self, newPath: str):
        self.backingAccount.name = newPath

    def setAccount(self, acc: Account):
        self._split.account = acc


class TransactionType:
    DEPOSITE = 1
    WITHDRAWAL = 2


class Entry:
    """ A class representing a simplified entry in the Ledger. """
    
    date: datetime.date

    value: str
    """ How much money $$$ """

    description :str
    """ The text provided with the transaction. """

    account_path: str
    """ Account to, or from which, the is being sent. """

    type: int
    """ If it's a DEPOSITE or a WITHDRAWAL. Also represented in the value being positive or negative. """

    thisAccount: EntryAccount
    """
    For withdrawls, thisAccount is the source account. For deposits,
    thisAccount is the target of the transaction.
    """

    otherAccount: EntryAccount
    """
    For withdrawls, otherAccount where the money is going. For deposits,
    otherAccount is where the money is coming from.
    """

    backingSplit : Split

    def __init__(self, split : Split):
        self.backingSplit = split
        transaction = cast(Transaction, split.transaction)
        account = cast(Account, split.account)

        self.description = transaction.description
        self.date = transaction.post_date

        # I don't think I will need it, but I don't want to have errors go unnoticed
        entrySplits = cast(CallableList, transaction.splits)
        if len(entrySplits) != 2:
            raise ValueError("Expected only 2 accounts. Please implement missing logic. Problematic entry:\n {}  {}".format(self.date, self.description))

        # usually there are two 'splits' so entryAccounts per
        # transaction/entry. The first denotes where to it was sent and the
        # second where from it was withdrawn.
        accountA = EntryAccount(entrySplits[0])
        accountB = EntryAccount(entrySplits[1])

        # it is more convenient to represent the transactions as having a
        # thisAccount, and an otherAccount. That way, we don't have to check
        # which is which all the time.

        # if the path is the same as the first entry, this was a deposite.
        if accountA.account_path == account.fullname:
            self.thisAccount = accountA
            self.otherAccount = accountB
            self.type = TransactionType.DEPOSITE

        else:
            self.thisAccount = accountB
            self.otherAccount = accountA

            # the path is not the same as the first entry, we assume the second
            # one is (as one has to be). So it was a withdrawal.
            self.type = TransactionType.WITHDRAWAL

        # take the positive value in the first entry
        self.value = self.thisAccount.value

        # use the second account's path to describe where it whent
        self.account_path = self.otherAccount.account_path


    @override
    def __str__(self) -> str:
        dateWidth=11
        amountWidth=8
        descriptionWidth=135
        formattedDate = self.date.strftime("%Y-%m-%d")
        positiveValueIndented = (" " + self.value) if not self.value.startswith("-") else self.value
        descriptionWithElipsis = (self.description[:(descriptionWidth-4)] + '...') if len(self.description) > descriptionWidth  else self.description
        return "{} {} {} {}".format(formattedDate.ljust(dateWidth), positiveValueIndented.ljust(amountWidth), descriptionWithElipsis.ljust(descriptionWidth), self.otherAccount.account_path)


