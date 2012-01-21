#!/usr/bin/env python

import sys



if True:
    # make a dummy image
    width=297
    height=503

    f=open(sys.argv[1], "w")
    f.write("P3\n%d %d\n255\n" % (width, height))

    for row in range(height):
        f.write("# row %d\n" % (row,))
        for col in range(width):
            if row<10 or row+10>=height:
                # block on each side
                r,g,b=200,200,200
            else:
                r,g,b=(row+col)%256,row%256,(row*col)%256
            f.write(" %d %d %d " % (r,g,b))
        f.write("\n")

    f.close()


    
