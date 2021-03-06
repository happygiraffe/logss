#!/usr/bin/python
#
# Copyright 2011 Dominic Mitchell. All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
# 1. Redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in the
# documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY DOMINIC MITCHELL ''AS IS'' AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL DOMINIC MITCHELL OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
# PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY
# OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE
# USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH
# DAMAGE.

"""A simple web server that can receive one request and then terminate.

This is useful for handling OAuth setup requests.
"""


__author__ = 'Dominic Mitchell <dom@happygiraffe.net>'


import cgi
import socket
import BaseHTTPServer


class ParamsReceiverServer(BaseHTTPServer.HTTPServer):
  """A web server that spins up just to act as a callback URL.

  When it receives a response, it exits, returning back to the previous
  flow of control.  This is very useful for OAuth callbacks.

  Methods:
    my_url: The URL to use as a callback.
    serve_until_result: The main web serving loop.

  Extra properties:
    result: The query parameters from the callback URL.
  """

  class ParamsReceiverHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
      """Don't log anything."""
      pass

    def do_GET(self):
      """Capture the query string and return."""
      self.server.result = self.path
      msg = """
      <h1>All Done</h1>
      <p>Thanks!  You may close this window now.</p>
      """
      self.send_response(200)
      self.send_header('Content-Length', str(len(msg)))
      self.end_headers()
      print >>self.wfile, msg

  def __init__(self, handler_class=ParamsReceiverHandler):
    self.result = None
    self.port = self.get_random_port()
    server_address = ('', self.port)
    # Darned old-style classes.
    BaseHTTPServer.HTTPServer.__init__(self, server_address, handler_class)

  def get_random_port(self):
    """Get a random port number to listen on."""
    # Calling bind to port zero asks the kernel to allocate a port number
    # for us.  Once it's done so, that's ours until the kernel loops around
    # port numbers again.  So long as we've called listen by then, it's fine.
    sock = socket.socket()
    sock.bind(('', 0))
    port = sock.getsockname()[1]
    sock.close()
    return port

  def my_url(self):
    """What URL is this server listening on?"""
    return 'http://%s:%d' % (socket.getfqdn(), self.port)

  def serve_until_result(self):
    """Keep serving until a query string has been captured."""
    while not self.result:
      self.handle_request()


def main():
  httpd = ParamsReceiverServer()
  print httpd.my_url()
  httpd.serve_until_result()

  print 'result: %s' % str(httpd.result)

if __name__ == '__main__':
  main()
