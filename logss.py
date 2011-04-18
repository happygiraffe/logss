#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Log a row to a Google Spreadsheet."""

__author__ = 'Dominic Mitchell <dom@happygiraffe.net>'


import getpass
import optparse
import os
import sys

import gdata.spreadsheet.service


class Error(Exception):
  pass


def Authenticate(client, username):
  # TODO: OAuth.  We must be able to do this without a password.
  client.ClientLogin(username,
                     getpass.getpass('Password for %s: ' % username))


def ExtractKey(entry):
  # This is what spreadsheetExample seems to do…
  return entry.id.text.split('/')[-1]


def FindKeyOfSpreadsheet(client, name):
  spreadsheets = client.GetSpreadsheetsFeed()
  spreadsheet = [s for s in spreadsheets.entry if s.title.text == name]
  if not spreadsheet:
    raise Error('Can\'t find spreadsheet named %s', name)
  if len(spreadsheet) > 1:
    raise Error('More than one spreadsheet named %s', name)
  return ExtractKey(spreadsheet[0])


def FindKeyOfWorksheet(client, key, name):
  if name == 'default':
    return name
  worksheets = client.GetWorksheetsFeed(key)
  worksheet = [w for w in worksheets.entry if w.title.text == name]
  if not worksheet:
    raise Error('Can\'t find worksheet named %s', name)
  if len(worksheet) > 1:
    raise Error('Many worksheets named %s', name)
  return ExtractKey(worksheet[0])


def ColumnNamesHaveData(cols):
  """Are these just names, or do they have data (:)?"""
  return len([c for c in cols if ':' in c]) > 0


def DefineFlags():
  usage = u"""usage: %prog [options] [col1:va1 …]"""
  desc = """
Log data into a Google Spreadsheet.

With no further arguments, a list of column names will be printed to stdout.

Otherwise, remaining arguments should be of the form `columnname:value'.
One row will be added for each invocation of this program.

If you just specify column names (without a value), then data will be read
from stdin in whitespace delimited form, and mapped to each column name
in order.
  """
  parser = optparse.OptionParser(usage=usage, description=desc)
  parser.add_option('--debug', dest='debug', action='store_true',
                    help='Enable debug output', default=False)
  parser.add_option('--key', dest='key',
                    help='The key of the spreadsheet to update '
                    '(the value of the key= parameter in the URL)')
  parser.add_option('--name', dest='name',
                    help='The name of the spreadsheet to update')
  parser.add_option('--worksheet', dest='worksheet',
                    help='The name of the worksheet to update',
                    default='default')
  parser.add_option('-u', '--username', dest='username',
                    help='Which username to log in as (default: %default)',
                    default='%s@gmail.com' % getpass.getuser())
  return parser


def main():
  parser = DefineFlags()
  (opts, args) = parser.parse_args()
  if (not opts.name and not opts.key) or (opts.name and opts.key):
    parser.error('You must specify either --name or --key')

  client = gdata.spreadsheet.service.SpreadsheetsService()
  client.debug = opts.debug
  client.source = os.path.basename(sys.argv[0])
  Authenticate(client, opts.username)

  key = opts.key or FindKeyOfSpreadsheet(client, opts.name)
  wkey = FindKeyOfWorksheet(client, key, opts.worksheet)
  if len(args) > 1:
    cols = args
    if ColumnNamesHaveData(cols):
      # Data is mixed into column names.
      data = dict(c.split(':', 1) for c in cols)
      client.InsertRow(data, key, wksht_id=wkey)
    else:
      # Read from stdin, pipe data to spreadsheet.
      for line in sys.stdin:
        vals = line.rstrip().split()
        data = dict(zip(cols, vals))
        client.InsertRow(data, key, wksht_id=wkey)
  else:
    list_feed = client.GetListFeed(key, wksht_id=wkey)
    for col in sorted(list_feed.entry[0].custom.keys()):
      print col
  return 0


if __name__ == '__main__':
  sys.exit(main())
