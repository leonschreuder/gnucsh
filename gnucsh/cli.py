import argparse
import re
from os.path import exists
from typing import cast

from gnucsh.convenience_types.ledger import openLedger


def main():

    parser = argparse.ArgumentParser()
    _ = parser.add_argument("bookPath", help="Path to the GnuCach db")
    _ = parser.add_argument(
        "account",
        nargs="?",
        help="Account to list (optional). Lists all account names otherwise.",
    )
    _ = parser.add_argument(
        "-t",
        "--transfer",
        help="Change the transfer account on the selected transactions to "
        + "the one provided.",
    )
    _ = parser.add_argument(
        "-f",
        "--filter",
        help="Regex filter. Valid both for listing accounts and transactions.",
    )
    _ = parser.add_argument(
        "-d",
        "--duplicates",
        help="Provide an account and search for duplicates "
        + "(same date + description)",
    )
    args: argparse.Namespace = parser.parse_args()
    bookPath = cast(str, args.bookPath)
    inputAccount = cast(str | None, args.account)
    newTransferAccountName = cast(str | None, args.transfer)
    filter = cast(str | None, args.filter)
    duplicatesAccount = cast(str | None, args.duplicates)

    if not exists(bookPath):
        raise ValueError(
            "Provided path to GnuCash db was not found: " + bookPath
        )

    if inputAccount is not None:
        if newTransferAccountName is not None:
            changeTransferAccount(
                bookPath, inputAccount, newTransferAccountName, filter
            )
        elif duplicatesAccount is not None:
            unifyDuplicates(bookPath, inputAccount, duplicatesAccount)
        else:
            listTransactions(bookPath, inputAccount, filter)
    else:
        listAccounts(bookPath, filter)


def changeTransferAccount(
    bookPath: str,
    inputAccount: str,
    newTransferAccountName: str,
    filter: str | None,
):
    with openLedger(bookPath) as ledger:
        accountContainingTransactions = ledger.findAccountByName(inputAccount)
        print("## Account:" + accountContainingTransactions.name)
        newTransferAccount = ledger.findAccountByName(newTransferAccountName)

        foundEntries = (
            accountContainingTransactions.findEntriesWithDescription(filter)
        )

        for e in foundEntries:
            print(e)

        user_input = input(
            "Are you sure you want to change the Transfer account "
            + "of the above entries to {}? [Y/n]".format(
                newTransferAccount.fullname
            )
        )
        if user_input.lower() == "y":
            for e in foundEntries:
                e.otherAccount.setAccount(newTransferAccount.backingAccount)
            _ = ledger.flush()
            _ = ledger.save()
        else:
            print("Canceling.")


def unifyDuplicates(
    bookPath: str, mainAccountName: str, otherAccountName: str
):
    with openLedger(bookPath) as ledger:
        mainAccount = ledger.findAccountByName(mainAccountName)
        otherAccount = ledger.findAccountByName(otherAccountName)

        duplicates = mainAccount.findDuplicates(otherAccount)
        if len(duplicates) < 1:
            print("no duplicates found")
            return

        for mainEntry, otherEntry in duplicates:
            print("----------")
            print("+ main: " + str(mainEntry))
            print("- other:" + str(otherEntry))

        user_input = input(
            "Are you sure you want to link the main entries to the"
            + " '{}' and remove the 'other' entries? [Y/n]".format(
                otherAccount.fullname
            )
        )

        if user_input.lower() == "y":
            for mainEntry, otherEntry in mainAccount.findDuplicates(
                otherAccount
            ):
                mainEntry.otherAccount.setAccount(otherAccount.backingAccount)
                otherAccount.removeEntry(otherEntry)
            ledger.save()


def listAccounts(bookPath: str, filter: str | None = None):
    if filter is None:
        print("### All Accounts ###")
    else:
        print("### Listing Accounts matching '" + filter + "' ###")

    with openLedger(bookPath) as ledger:
        for acc in ledger.getAllAccounts():
            if filter is None:
                print(acc.fullname)
            else:
                if re.search(filter, acc.fullname):
                    print(acc.fullname)


def listTransactions(
    bookPath: str, accountName: str, filter: str | None = None
):
    with openLedger(bookPath) as ledger:
        accountToList = ledger.findAccountByName(accountName)

        print(
            "###  Account:'{}'  filter:'{}'  ###".format(
                accountToList.name, str(filter)
            )
        )

        for entry in accountToList.findEntriesWithDescription(filter):
            print(entry)


if __name__ == "__main__":
    main()
