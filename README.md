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

TODO
----

Right now this is a proof of concept, and there are many enhancements needed:

 - Use OAuth so we don't have to prompt for a password each time.

 [pygdata]: http://code.google.com/p/gdata-python-client/