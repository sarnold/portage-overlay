#!/usr/bin/env python

# Analyse a log file

import sys


def dolines(f):
    state=None
    last=None

    for line in f:
        if line[0]=='[':
            if state is not None:
                dumpstate(state)
                state=None
            if line.find('<<<  URB')>0:
                state={'dir': 'in', 'data': []}
                continue
            elif line.find('>>>  URB')>0:
                state={'dir': 'out', 'data': []}
                continue
            else:
                if line.find('UsbSnoop')>0:
                    continue
                print "ignoring",line
                continue
        if state is None:
            print "what is",line
            continue
        if line.find('-- ')==0:
            state['urb']=line[3:-2]
            continue
        if line.startswith('    '):
            state['data'].append(line[4:])
            continue
        if line.startswith('  '):
            eq=line.find('=')
            state[line[:eq].strip()]=line[eq+1:].strip()
            continue

def dumpstate(state):
    if state['urb']=='URB_FUNCTION_BULK_OR_INTERRUPT_TRANSFER':
        if state['dir']=='out' and state['TransferFlags'].find('DIRECTION_IN')>0:
            if state['TransferBufferLength']!='00000040':
                print state
    
        

dolines(open(sys.argv[1], "r"))

    
