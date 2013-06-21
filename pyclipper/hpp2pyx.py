#!/usr/bin/python
import sys
import os
import re
from optparse import OptionParser
import CppHeaderParser

def Usage():
    print( "Usage: hpp2pyx.py [options] hppFilename pyxFilename\n")
    return 1

def main():
    parser = OptionParser(usage="usage: %prog [options] hppFilename")
    # parser.add_option("--hppfile",dest="hppFilename",default=None,help="HPP Input Filename")
    # parser.add_option("--pyxfile",dest="pyxFilename",default=None,help="Cython PYX Output Filename")

    (options,args) = parser.parse_args()
    if len(args) != 2:
        parser.error("Please provide an input HPP filename and output PYX filename.")
    hppFilename = args[0]
    pyxFilename = args[1]

    if hppFilename is None or pyxFilename is None:
        return Usage()

    try:
        cppHeader = CppHeaderParser.CppHeader(hppFilename)
    except CppHeaderParser.CppParseError, e:
        print e
        sys.exit(1)

    pyxFile = open( pyxFilename, "w")
    pyx = pyxFile.write

    for thisClass in cppHeader.classes:
        pyx("# Class: %s\n" % thisClass )
        for thisMethod in cppHeader.classes[thisClass]["methods"]:
            pyx("#  Method: %s\n" % thisMethod )
            for thisFunction in cppHeader.classes[thisClass]["methods"][thisMethod]:
              pyx("#    Function: %s\n" % thisFunction["name"])
              for thisPart in thisFunction:
                pyx("#      Part: %s\n" % thisPart)
                if thisPart is "parent":
                    pyx("### Don't follow parent.\n")
                elif thisPart is "parameters" and thisFunction["parameters"] is not None:
                    for thisParam in thisFunction["parameters"]:
                        pyx("#          Parameter: %s\n" % thisParam)
                else:
                    pyx("#          %s\n" % thisFunction[thisPart])

    pyxFile.close()

    return True

if __name__ == '__main__':
    # sys.exit(main(sys.argv))
    main()



