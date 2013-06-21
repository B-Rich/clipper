#!/usr/bin/python
import sys
import os
import re
from optparse import OptionParser
import CppHeaderParser

def Usage():
    print( "Usage: hpp2pyx.py [options] hppFilename pyxFilename\n")
    return 1

def build_header(hppFilename,pyx):
    pyx("""print "Python bindings for %s"\n\n""" % hppFilename)
    pyx("""import sys
import struct
from ctypes import *
import copy
import unicodedata
import time
from cython import *

from cython.operator cimport dereference as deref

cdef extern from "Python.h":
    Py_INCREF(object o)
    object Py_BuildValue(char *format, ...)
    object PyBuffer_FromMemory(void *ptr, int size)
    #int PyArg_ParseTuple(object struct,void* ptr)
    char* PyString_AsString(object string)
    int PyArg_VaParse(object args,  char *format, ...)
    int PyArg_Parse(object args,  char *format, ...)
    int PyObject_AsReadBuffer(object obj,  void* buffer, int* buffer_len)
    object PyBuffer_FromObject(object base, int offset, int size)
    object PyBuffer_FromReadWriteObject(object base, int offset, int size)
    PyBuffer_New(object o)

""")

def build_deps(hppFilename,pyx):
    pyx("""cdef extern from "stdio.h":
    cdef void printf(char*,...)

""")
    pyx("""cdef extern from "stdlib.h":
    cdef void* malloc(unsigned int size)
    cdef void* free(void* p)
    char *strdup(char *str)
    int strcpy(void* str, void* src)
    int memcpy(void* str, void* src, int size)

""")
    pyx("""from libcpp.vector cimport vector

""")

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

    build_header(hppFilename,pyx)
    build_deps(hppFilename,pyx)

    indentSpace=""
    for thisNS in cppHeader.namespaces:
        pyx("# Namespace: %s\n" % thisNS)
        pyx("cdef extern from \""+hppFilename+"\" namespace \""+thisNS+"\":\n\n")

        for thisEnum in cppHeader.enums:
            indentSpace="  "
            # print("\nEnum: %s\n" % thisEnum)
            enumNS=re.search('(\A\w+)',thisEnum["namespace"]).group(0)
            if enumNS == thisNS:
                pyx(indentSpace+"# Enum: %s\n" % thisEnum["name"] )
                pyx(indentSpace+"cdef enum "+thisEnum["name"]+":\n")
                indentSpace="    "
                for i in range(0,len(thisEnum["values"])):
                    if i > 0:
                        pyx(indentSpace+", ")
                    else:
                        pyx(indentSpace)
                    pyx(thisEnum["values"][i]["name"]+"=")
                    pyx("%d" % thisEnum["values"][i]["value"])
                    pyx("\n")
                pyx("\n")

        for thisTypedef in cppHeader.typedefs_order:
            indentSpace="  "
            typedefMatch=re.search('(\A\w+)::(\w+)',thisTypedef)
            (typedefNS,typedefName)=(typedefMatch.group(1),typedefMatch.group(2))
            if typedefNS == thisNS:
                print("# %s %s" % (thisTypedef,cppHeader.typedefs[thisTypedef]))
                pyx(indentSpace+"# ctypedef %s::%s %s\n" % (typedefNS,typedefName,cppHeader.typedefs[thisTypedef]))

        for thisClass in cppHeader.classes:
            indentSpace="  "
            if cppHeader.classes[thisClass]["namespace"] == thisNS:
                pyx(indentSpace+"# Class: %s\n" % thisClass )
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



