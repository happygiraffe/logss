#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Log a row to a Google Spreadsheet."""

__author__ = 'Dominic Mitchell <dom@happygiraffe.net>'


import getpass
import sys

import gdata.spreadsheet.service


WHOM = 'dom@happygiraffe.net'


class Error(Exception):
  pass


def Authenticate(client):
  # TODO: OAuth.  We must be able to do this without a password.
  client.ClientLogin(WHOM, getpass.getpass('Password for %s: ' % WHOM))


def ExtractKey(entry):
  # This is what spreadsheetExample seems to do…
  return entry.id.text.split('/')[-1]


def FindKeyOfSheet(client, name):
  spreadsheets = client.GetSpreadsheetsFeed()
  spreadsheet = [s for s in spreadsheets.entry if s.title.text == name]
  if not spreadsheet:
    raise Error('Can\'t find spreadsheet named %s', name)
  return ExtractKey(spreadsheet[0])


def main(argv):
  spreadsheet_name = argv[1]

  client = gdata.spreadsheet.service.SpreadsheetsService()
  Authenticate(client)

  key = FindKeyOfSheet(client, spreadsheet_name)

  # TODO: print column names if no args given.
  # TODO: auto-detect column names, and apply to args in order.
  args = dict(x.split('=', 1) for x in argv[2:])
  client.InsertRow(args, key)
  return 0


if __name__ == '__main__':
  sys.exit(main(sys.argv))
