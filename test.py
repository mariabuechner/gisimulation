import urllib2
import numpy as np
import csv



url_material = \
'http://x-server.gmca.aps.anl.gov/cgi/www_dbli.exe?x0hdb=amorphous%2Batoms'
page=urllib2.urlopen(url_material).read()
#try:
#    page=urllib2.urlopen(url_material).read()
#except urllib2.URLError as err:
#    if tabel exists:
#        print('No internet connection, reading from table stored in "rhos.csv"')
#    else:
#        print('enter rho manually')
# Format of string, using \r\n to seperate lines
#    Header
#    Ac              *Amorphous*     rho=10.05     /Ac/
#    Ag              *Amorphous*     rho=10.5      /Ag/


page = page.splitlines() # Split in lines
page = [row for row in page if '*Amorphous*' in row] # Remove header
page = [row.split(' ') for row in page] # Split strings
page = [filter(None, row) for row in page] # Remove spaces
for row in page:
    del row[1] # delete second column '*Amorphous*'
    del row[-1] # delete last column '/name/'
#materials = [row[0] for row in page]
#rhos = [np.float(row[1].split('=')[1]) for row in page]

page = [[row[0],np.float(row[1].split('=')[1])] for row in page]

# save current file
with open("rhos.csv", "wb") as f:
    writer = csv.writer(f)
    writer.writerows(page)

page = dict(page)
