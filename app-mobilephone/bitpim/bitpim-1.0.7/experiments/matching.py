#!/usr/bin/env python

# Do string matching giving a confidence score.

import difflib
import Levenshtein

# according to doc, should call set_seq2 once and then keep changing
# seq1

def dlmatch(s1, s2):
    "how well does s2 match s1?"
    s=difflib.SequenceMatcher()
    s.set_seq2(s1)
    s.set_seq1(s2)
    return int(s.ratio()*100)

def lvmatch(s1, s2):
    "how well does s2 match s1?"
    return int(Levenshtein.jaro_winkler(s1,s2)*100)

def srmatch(s1, s2):
    s3=s2.split()
    s3.reverse()
    return max(lvmatch(s1,s2), lvmatch(s1," ".join(s3)))

inp="""
John Smith
JohnSmith
John Smythe
John Q Smith
Smith John
JQ Smith
Smith J
Matrix Revolutions
Matty Ranger
Smith John Q
John Smi
Smithy
John
Joe Blow
Jo Bloggs
Joe Bloggs
Mary Miggins
John Q Bloggs
Verizon
VZW
American Airlines"""

inp=[x for x in inp.split("\n") if len(x)]
for one in inp:
    print "=================="
    print one
    print
    l=[]
    for two in inp:
        l.append( (srmatch(one, two), lvmatch(one, two), dlmatch(one,two), two) )
    l.sort()
    l.reverse()
    for srscore, lvscore,dlscore,name in l:
        print "%3d %3d %3d %s" % (srscore, lvscore,dlscore,name)
    print
