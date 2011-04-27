#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Log a row to a Google Spreadsheet."""


__author__ = 'Dominic Mitchell <dom@happygiraffe.net>'


import pickle
import optparse
import os
import sys

import gdata.gauth
import gdata.spreadsheets.client

import oneshot


# OAuth bits.  We use “anonymous” to behave as an unregistered application.
# http://code.google.com/apis/accounts/docs/OAuth_ref.html#SigningOAuth
CONSUMER_KEY = 'anonymous'
CONSUMER_SECRET = 'anonymous'
# The bits we actually need to access.
SCOPES = ['https://spreadsheets.google.com/feeds/']


class Error(Exception):
  pass


class TokenStore(object):
  """Store and retreive OAuth access tokens."""

  def __init__(self, token_file=None):
    default = os.path.expanduser('~/.%s.tok' % os.path.basename(sys.argv[0]))
    self.token_file = token_file or default

  def ReadToken(self):
    """Read in the stored auth token object.

    Returns:
      The stored token object, or None.
    """
    try:
      with open(self.token_file, 'rb') as fh:
        return pickle.load(fh)
    except IOError, e:
      return None

  def WriteToken(self, tok):
    """Write the token object to a file."""
    with open(self.token_file, 'wb') as fh:
      os.fchmod(fh.fileno(), 0600)
      pickle.dump(tok, fh)


class ClientAuthorizer(object):
  """Add authorization to a client."""

  def __init__(self, consumer_key=CONSUMER_KEY,
               consumer_secret=CONSUMER_SECRET, scopes=None,
               token_store=None, logger=None):
    """Construct a new ClientAuthorizer."""
    self.consumer_key = consumer_key
    self.consumer_secret = consumer_secret
    self.scopes = scopes or list(SCOPES)
    self.token_store = token_store or TokenStore()
    self.logger = self.LogToStdout

  def LogToStdout(self, msg):
    print msg

  def FetchAccessToken(self, client):
    # http://code.google.com/apis/gdata/docs/auth/oauth.html#Examples
    httpd = oneshot.ParamsReceiverServer()

    # TODO Find a way to pass "xoauth_displayname" parameter.
    request_token = client.GetOAuthToken(
        self.scopes, httpd.my_url(), self.consumer_key, self.consumer_secret)
    url = request_token.generate_authorization_url()
    self.logger('Please visit this URL to authorize: %s' % url)
    httpd.serve_until_result()
    gdata.gauth.AuthorizeRequestToken(request_token, httpd.result)
    return client.GetAccessToken(request_token)

  def EnsureAuthToken(self, client):
    """Ensure client.auth_token is valid.

    If a stored token is available, it will be used.  Otherwise, this goes
    through the OAuth rituals described at:

    http://code.google.com/apis/gdata/docs/auth/oauth.html

    As a side effect, this also reads and stores the token in a file.
    """
    access_token = self.token_store.ReadToken()
    if not access_token:
      access_token = self.FetchAccessToken(client)
      self.token_store.WriteToken(access_token)
    client.auth_token = access_token


# The next three classes are overrides to add missing functionality in the
# python-gdata-client.

class MyListEntry(gdata.spreadsheets.data.ListEntry):

  def CustomFields(self):
    """Return the names of all child elements in the GSX namespace."""
    ns = gdata.spreadsheets.data.GSX_NAMESPACE
    return [el.tag for el in self.get_elements(namespace=ns)]


class MyListsFeed(gdata.spreadsheets.data.ListsFeed):

  entry = [MyListEntry]

  def ColumnNames(self):
    if not self.entry:
      return []
    return self.entry[0].CustomFields()


class MySpreadsheetsClient(gdata.spreadsheets.client.SpreadsheetsClient):
  """Add in support for List feeds."""

  LISTS_URL = 'https://spreadsheets.google.com/feeds/list/%s/%s/private/full'

  def get_list_feed(self, key, wksht_id='default', **kwargs):
    return self.get_feed(self.LISTS_URL % (key, wksht_id),
                         desired_class=MyListsFeed, **kwargs)

  GetListFeed = get_list_feed

  def insert_row(self, data, key, wksht_id='default'):
    new_entry = MyListEntry()
    for k, v in data.iteritems():
      new_entry.set_value(k, v)
    return self.post(new_entry, self.LISTS_URL % (key, wksht_id))

  InsertRow = insert_row


class SpreadsheetInserter(object):
  """A utility to insert rows into a spreadsheet."""

  def __init__(self, debug=False):
    self.client = MySpreadsheetsClient()
    self.client.http_client.debug = debug
    self.client.source = os.path.basename(sys.argv[0])
    self.key = None
    self.wkey = None

  def Authenticate(self, logger=None):
    client_authz = ClientAuthorizer(logger=logger)
    client_authz.EnsureAuthToken(self.client)

  def SetKey(self, key, name):
    """Set the key value, or if None, look up name and set key from that."""
    self.key = key or self.FindKeyOfSpreadsheet(name)

  def SetWorksheetKey(self, worksheet_name):
    self.wkey = self.FindKeyOfWorksheet(worksheet_name)

  def ExtractKey(self, entry):
    # This is what spreadsheetExample seems to do…
    return entry.id.text.split('/')[-1]

  def FindKeyOfEntryNamed(self, feed, name, kind='spreadsheet'):
    entry = [e for e in feed.entry if e.title.text == name]
    if not entry:
      raise Error('Can\'t find %s named %s', kind, name)
    if len(entry) > 1:
      raise Error('More than one %s named %s', kind, name)
    return self.ExtractKey(entry[0])

  def FindKeyOfSpreadsheet(self, name):
    spreadsheets = self.client.GetSpreadsheets()
    return self.FindKeyOfEntryNamed(spreadsheets, name)

  def FindKeyOfWorksheet(self, name):
    if name == 'default':
      return name
    worksheets = self.client.GetWorksheets(self.key)
    return self.FindKeyOfEntryNamed(worksheets, name, 'worksheet')

  def ColumnNamesHaveData(self, cols):
    """Are these just names, or do they have data (:)?"""
    return len([c for c in cols if ':' in c]) > 0

  def InsertRow(self, data):
    self.client.InsertRow(data, self.key, wksht_id=self.wkey)

  def InsertFromColumns(self, cols):
    # Data is mixed into column names.
    data = dict(c.split(':', 1) for c in cols)
    self.InsertRow(data)

  def InsertFromFileHandle(self, cols, fh):
    for line in fh:
      vals = line.rstrip().split(None, len(cols) - 1)
      data = dict(zip(cols, vals))
      self.InsertRow(data)

  def ListColumns(self):
    list_feed = self.client.GetListFeed(self.key, wksht_id=self.wkey)
    return sorted(list_feed.ColumnNames())


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
  return parser


def main():
  parser = DefineFlags()
  (opts, args) = parser.parse_args()
  if (not opts.name and not opts.key) or (opts.name and opts.key):
    parser.error('You must specify either --name or --key')

  inserter = SpreadsheetInserter(debug=opts.debug)
  inserter.Authenticate()
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
