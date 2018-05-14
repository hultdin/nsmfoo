#!/usr/bin/python

'''
This python script generates SQL statements that can be used to update the signature table if the alert description 
looks like "Snort Alert [1:1337:1]", i.e. there is no description matching the sid in the database. 

grep 1337 /etc/suricata/sid-msg.map | signature-update.py
'''

import sys
import re

def main(argv):
  if not sys.stdin.isatty():
    for line in sys.stdin:
      match = re.match(r'^(\d+)\s+\|\|\s+(.*?)(?:\s+\|\|\s+.*)??$', line)
      if match:
        print 'UPDATE signature SET sig_name = "%s" WHERE sig_sid = %i;' % (match.group(2), int(match.group(1)))
      else:
        print >> sys.stderr, 'ERROR: Failed to parse "' + line + '"'
  else:
    print 'Feed me with signatures via stdin and I will oink...'

if __name__ == '__main__':
  exit(main(sys.argv))
