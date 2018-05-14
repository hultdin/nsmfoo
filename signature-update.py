#!/usr/bin/python

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
