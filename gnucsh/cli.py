import csv
import re
from dataclasses import dataclass
from datetime import date, datetime

import click

from gnucsh.convenience_types.base_account import BaseAccount
from gnucsh.convenience_types.ledger import openLedger


@click.command()
@click.argument("book_path", type=str)
@click.argument("account", required=False, type=str)
@click.option(
    "-t",
    "--transfer",
    type=str,
    help="Change the transfer account on the selected"
    + " transactions to the one provided.",
)
@click.option(
    "-f",
    "--filter",
    type=str,
    help="Regex filter. Valid both for listing accounts and transactions.",
)
@click.option(
    "-d",
    "--duplicates",
    type=str,
    help="Provide an account and search for"
    + " duplicates (same date + description).",
)
@click.option(
    "-i",
    "--importfile",
    type=str,
    help="Provide a CSV file to import to the database",
)
def main(
    book_path: str,
    account: str | None,
    transfer: str | None,
    filter: str | None,
    duplicates: str | None,
    importfile: str | None,
):

    if account is not None:
        if transfer is not None:
            changeTransferAccount(book_path, account, transfer, filter)
        elif duplicates is not None:
            unifyDuplicates(book_path, account, duplicates)
        elif importfile is not None:
            importCsv(book_path, importfile, account)
        else:
            listTransactions(book_path, account, filter)
    else:
        listAccounts(book_path, filter)


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


@dataclass
class EntryData:
    date: date
    description: str
    amount: str
    transferAcct: BaseAccount


# date
# description
# notes
# account
# amount
# -amount
# transfer
def importCsv(bookPath: str, csvFile: str, accountName: str):
    with open(csvFile, mode="r") as file:
        opendCsv = csv.DictReader(file, delimiter=";", skipinitialspace=True)
        with openLedger(bookPath) as ledger:
            account = ledger.findAccountByName(accountName)
            clearedEntries: list[EntryData] = []

            for csvDict in opendCsv:
                # print(line)
                dateValue = getColumnOrRaise(csvDict, "date")
                customDate = dateStringToDate(dateValue)

                description = getColumnOrRaise(csvDict, "description")

                transferName = getColumnOrRaise(csvDict, "transfer")
                transferAcct = ledger.findAccountByName(transferName)

                amount = csvDict.get("amount")
                negAmount = csvDict.get("-amount")
                if amount is None and negAmount is None:
                    raise ValueError("Missing 'amount' or '-amount' column.")
                resolvedAmount: str
                if negAmount is not None:
                    resolvedAmount = str(-float(negAmount))
                else:
                    resolvedAmount = str(amount)

                clearedEntries.append(
                    EntryData(
                        description=description,
                        amount=resolvedAmount,
                        date=customDate,
                        transferAcct=transferAcct,
                    )
                )

            # Only add entries to the db after all the values are checked. That
            # way, if there is an error in a later line, no partial add has
            # occured.
            for entryData in clearedEntries:
                account.addEntry(
                    entryData.amount,
                    entryData.description,
                    entryData.transferAcct,
                    entryData.date,
                )
            ledger.save()


def getColumnOrRaise(dict: dict[str, str], name: str) -> str:
    value = dict.get(name)
    if value is None:
        raise ValueError(f"Missing '{name}' column.")
    return value


def dateStringToDate(dateString: str) -> date:
    return datetime.strptime(dateString, "%Y-%m-%d").date()


if __name__ == "__main__":
    main()
