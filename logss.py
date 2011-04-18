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


class SpreadsheetInserter(object):
  """A utility to insert rows into a spreadsheet."""

  def __init__(self, debug=False):
    self.client = gdata.spreadsheet.service.SpreadsheetsService()
    self.client.debug = debug
    self.client.source = os.path.basename(sys.argv[0])
    self.key = None
    self.wkey = None

  def Authenticate(self, username, password):
    # TODO: OAuth.  We must be able to do this without a password.
    self.client.ClientLogin(username, password)

  def SetKey(self, key, name):
    """Set the key value, or if None, look up name and set key from that."""
    self.key = key or self.FindKeyOfSpreadsheet(name)

  def SetWorksheetKey(self, worksheet_name):
    self.wkey = self.FindKeyOfWorksheet(worksheet_name)

  def ExtractKey(self, entry):
    # This is what spreadsheetExample seems to do…
    return entry.id.text.split('/')[-1]

  def FindKeyOfSpreadsheet(self, name):
    spreadsheets = self.client.GetSpreadsheetsFeed()
    spreadsheet = [s for s in spreadsheets.entry if s.title.text == name]
    if not spreadsheet:
      raise Error('Can\'t find spreadsheet named %s', name)
    if len(spreadsheet) > 1:
      raise Error('More than one spreadsheet named %s', name)
    return self.ExtractKey(spreadsheet[0])

  def FindKeyOfWorksheet(self, name):
    if name == 'default':
      return name
    worksheets = self.client.GetWorksheetsFeed(self.key)
    worksheet = [w for w in worksheets.entry if w.title.text == name]
    if not worksheet:
      raise Error('Can\'t find worksheet named %s', name)
    if len(worksheet) > 1:
      raise Error('Many worksheets named %s', name)
    return self.ExtractKey(worksheet[0])

  def ColumnNamesHaveData(self, cols):
    """Are these just names, or do they have data (:)?"""
    return len([c for c in cols if ':' in c]) > 0

  def InsertFromColumns(self, cols):
    # Data is mixed into column names.
    data = dict(c.split(':', 1) for c in cols)
    self.client.InsertRow(data, self.key, wksht_id=self.wkey)

  def InsertFromFileHandle(self, cols, fh):
    for line in fh:
      vals = line.rstrip().split()
      data = dict(zip(cols, vals))
      self.client.InsertRow(data, self.key, wksht_id=self.wkey)

  def ListColumns(self):
    list_feed = self.client.GetListFeed(self.key, wksht_id=self.wkey)
    return sorted(list_feed.entry[0].custom.keys())


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

  inserter = SpreadsheetInserter(debug=opts.debug)

  password = getpass.getpass('Password for %s: ' % opts.username)
  inserter.Authenticate(opts.username, password)

  inserter.SetKey(opts.key, opts.name)
  inserter.SetWorksheetKey(opts.worksheet)

  if len(args) > 1:
    cols = args
    if inserter.ColumnNamesHaveData(cols):
      inserter.InsertFromColumns(cols)
    else:
      # Read from stdin, pipe data to spreadsheet.
      inserter.InsertFromFileHandle(cols, sys.stdin)
  else:
    print('\n'.join(inserter.ListColumns()))
  return 0


if __name__ == '__main__':
  sys.exit(main())
