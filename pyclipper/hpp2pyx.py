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
# from libcpp.bool cimport bool
ctypedef char bool

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

    print("Building header...")
    build_header(hppFilename,pyx)
    print("Building deps...")
    build_deps(hppFilename,pyx)

    indentSpace=""
    for thisNS in cppHeader.namespaces:
        pyx("# Namespace: %s\n" % thisNS)
        pyx("cdef extern from \""+hppFilename+"\" namespace \""+thisNS+"\":\n\n")

        for thisEnum in cppHeader.enums:
            indentSpace="  "
            print("Enum: %s" % thisEnum['name'])
            enumNS=re.search('(\A\w+)',thisEnum["namespace"]).group(0)
            if enumNS == thisNS:
                pyx(indentSpace+"# Enum: %s\n" % thisEnum["name"] )
                pyx(indentSpace+"cdef enum "+thisEnum["name"]+":\n")
                indentSpace="    "
                for i in range(0,len(thisEnum["values"])):
                    pyx(indentSpace)
                    pyx(thisEnum["values"][i]["name"]+"=")
                    pyx("%d" % thisEnum["values"][i]["value"])
                    if i < len(thisEnum["values"])-1:
                        pyx(",")
                    pyx("\n")
                pyx("\n")

        for thisTypedef in cppHeader.typedefs_order:
            indentSpace="  "
            typedefMatch=re.search('(\A\w+)::(\w+)',thisTypedef)
            (typedefNS,typedefName)=(typedefMatch.group(1),typedefMatch.group(2))
            if typedefNS == thisNS and not re.search('::',cppHeader.typedefs[thisTypedef]):
                # print("# %s %s" % (thisTypedef,cppHeader.typedefs[thisTypedef]))
                # pyx(indentSpace+"# ctypedef %s::%s %s\n" % (typedefNS,typedefName,cppHeader.typedefs[thisTypedef]))
                pyx(indentSpace)
                if re.search('::',cppHeader.typedefs[thisTypedef]):
                    pyx("#1 ")
                pyx("ctypedef "+cppHeader.typedefs[thisTypedef]+" "+typedefName+"\n")
            else:
                typedefMatch=re.search('std::vector<([^>]+)>',cppHeader.typedefs[thisTypedef])
                typedefNameSearchTxt="\A"+thisNS+"::(\w+)"
                typedefNameFiltered=re.search(typedefNameSearchTxt,thisTypedef)
                if typedefMatch:
                    if typedefNameFiltered:
                        pyx(indentSpace+"ctypedef vector["+typedefMatch.group(1)+"] "+typedefNameFiltered.group(1)+"\n")
                    else:
                        pyx(indentSpace+"ctypedef vector["+typedefMatch.group(1)+"] "+thisTypedef+"\n")
                else:
                    pyx("#2 ctypedef "+cppHeader.typedefs[thisTypedef]+" "+typedefName+"\n")

        def print_struct(indSpace="  ",structName=""):
            pyx(indSpace+"cdef struct "+structName+":\n")
            for entry in cppHeader.classes[structName]['properties']['public']:
                entryType=entry['type']
                # print("   Checking '%s'"%entryType)
                for tdkey in cppHeader.typedefs.keys():
                    tdval=cppHeader.typedefs[tdkey]
                    matchString="\A"+cppHeader.classes[structName]['namespace']+"::(\w+)"
                    namespaceMatch=re.search(matchString,tdkey)
                    # print("        '%s' '%s' '%s'"%(tdkey,tdval,matchString))
                    if tdval == entryType:
                        # print("         Matched '%s' == '%s'"%(tdval,entryType))
                        if namespaceMatch:
                            # print("               Matched!")
                            entryType=namespaceMatch.group(1)
                            # entryType=tdkey
                pyx(indSpace+"  "+entryType+" "+entry['name']+"\n")

        def print_class(indSpace="  ",className=""):
            pyx(indSpace+"cdef cppclass %s:\n" % className )
            for thisPublicMethod in cppHeader.classes[className]["methods"]["public"]:
                if thisPublicMethod['constructor']:
                    pyx(indSpace+"  "+thisPublicMethod['name']+"()\n")
                elif thisPublicMethod['destructor']:
                    pyx(indSpace+"  # "+thisPublicMethod['debug']+"\n")
                else:
                    rtnType=thisPublicMethod['rtnType']
                    matchString="\A"+thisPublicMethod['namespace']+"(\w+)"
                    namespaceMatch=re.search(matchString,rtnType)
                    if namespaceMatch:
                        rtnType=namespaceMatch.group(1)
                    pyx(indSpace+"  "+rtnType+" "
                        +thisPublicMethod['name']+"(") 
                    # )
                    for i in range(0,len(thisPublicMethod['parameters'])):
                        thisParam=thisPublicMethod['parameters'][i]
                        if i>0:
                            pyx(",")
                        rtnType=thisParam['type']
                        matchString="\A"+thisPublicMethod['namespace']+"(\w+)"
                        namespaceMatch=re.search(matchString,rtnType)
                        if namespaceMatch:
                            rtnType=namespaceMatch.group(1)
                        pyx(rtnType+" "+thisParam['name'])
                    # (
                    pyx(")\n")
                
        # struct is cppHeader.classes['IntPoint']['methods']['public'][0]['returns_fundamental']
        for thisClass in cppHeader.classes:
            indentSpace="  "
            if cppHeader.classes[thisClass]["namespace"] == thisNS:
                print("Processing "+thisClass)
                if cppHeader.classes[thisClass]['declaration_method'] == 'struct':
                    print_struct(indSpace=indentSpace,structName=thisClass)
                else:
                    print_class(indSpace=indentSpace,className=thisClass)

    pyx("\n# EOF\n")
    pyxFile.close()

    return True

if __name__ == '__main__':
    # sys.exit(main(sys.argv))
    main()



