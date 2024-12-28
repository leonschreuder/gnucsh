# gnucsh

[![codecov](https://codecov.io/gh/leonschreuder/gnucsh/branch/main/graph/badge.svg?token=gnucsh_token_here)](https://codecov.io/gh/leonschreuder/gnucsh)
[![CI](https://github.com/leonschreuder/gnucsh/actions/workflows/main.yml/badge.svg)](https://github.com/leonschreuder/gnucsh/actions/workflows/main.yml)

This is a convenience CLI for a few batch operations in gnucash I needed at
some point.

```bash
# list all accounts:
gnucsh mybook.gnucsh

# list transactions for the specified account
gnucsh mybook.gnucsh My:Account

# list transactions for the specified account that match the (regex) filter
gnucsh mybook.gnucsh My:Account -f "Some Store"

# Change the listed transactions' transfer account, to the provided account
gnucsh mybook.gnucsh My:Account -f "Some Store" -t "My:Other

# WARNING: There is a better way to do this. See below
# Tries to find duplicate entries shared between the two accounts, links them and removes the duplicate
gnucsh mybook.gnucsh My:Account -d My:Other
```

The command to unify duplicates was meant to solve the situation where you have
a checking and a savings account for example, and they are both synced from
your bank with online transactions. Gnucash does not understand that you moved
money from one to the other, and sees two unlinked transactions. If you link
them to the correct account, then the entries are listed twice in each account.
A better way to deal with this however, is to create a third "transfer" account
and link both transactions to it. This transfer account will add up to zero
(thereby verifying everything is linked correctly) and you don't have to delete
any transactions.

## Install it from PyPI

```bash
pip install gnucsh
```

## Usage

```py
from gnucsh import BaseClass
from gnucsh import base_function

BaseClass().base_method()
base_function()
```

```bash
$ python -m gnucsh
#or
$ gnucsh
```

## Development

Read the [CONTRIBUTING.md](CONTRIBUTING.md) file.
