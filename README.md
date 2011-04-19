logss
=====

This is a small tool to log data to a Google Spreadsheet.  Google Spreadsheets are very handy for manipulating data, but it's less easy to insert data programmatically.

In order to use this, you'll need the [python gdata client][pygdata] in `PYTHONPATH`, e.g.

    $ export PYTHONPATH="/opt/google/gdata-2.0.14/src"
    $ python logss.py --name "Spreadsheet Name" col1:val1 col2:val2 …

You can insert multiple rows at once by piping on stdin, whilst specifying just the column names.

    $ cat data
    val1 val2
    val3 val4
    $ python logss.py --name 'Spreadsheet Name' col1 col2 < data

If you need to know what the valid column names are, leave off the data from the command line.

    $ python logss.py --name "Spreadsheet Name"
    col1
    col2

Note that `logss` uses OAuth, so the first time that you use it, you will be prompted with an URL to visit in order to allow `logss` access to your google docs.

TODO
----

 - Add a `setup.py` to allow installation.

 [pygdata]: http://code.google.com/p/gdata-python-client/