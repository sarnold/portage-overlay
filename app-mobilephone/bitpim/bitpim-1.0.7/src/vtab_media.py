### BITPIM
###
### Copyright (C) 2007 Joe Pham <djpham@bitpim.org>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: vtab_media.py 4155 2007-03-17 04:07:42Z djpham $

"""
An apsw compatible module that implements a virtual table that stores media
data as native system files.
"""
# System modules
import glob
import os
import os.path

# BitPim moduless
import database

class Media(database.ModuleBase):
    """
    Module to implements a virtual table that stores media data as native system
    files.
    The table has 2 fiels: __rowid__ and mediadata
    This class maintains its own rowid, cursor, and constraints parameters.
    The data of each row is stored in a file named Fxxxxxxx, where
    xxxxxxx is the rowid starting with 1 ie (F0000001, F0000002, etc)
    """

    def __init__(self, pathname):
        """
        @params pathname: full path in which to stores data files
        """
        super(Media, self).__init__(('data',))
        # make sure the path exists
        if not os.path.exists(pathname):
            os.makedirs(pathname)
        self.pathname=os.path.abspath(pathname)
        self.rowidfilename=os.path.join(self.pathname, 'rowid')
        self.getnextrowid()
        self.filenames=[]
        self.cursor=None

    def getnextrowid(self):
        """
        Return the next row ID from a file called rowid
        """
        try:
            id=file(self.rowidfilename, 'rt').read()
            self.rowid=int(id)
        except IOError:
            # file does not exist
            self.rowid=1
            self.saverowid(1)
    def incrementrowid(self):
        # increment the next row ID by 1
        self.rowid+=1
        self.saverowid(self.rowid)
    def saverowid(self, id):
        file(self.rowidfilename, 'wt').write(str(id))
    def filenamefromid(self, id):
        # return a full path name based on the row ID
        return os.path.join(self.pathname, 'F%07d'%id)
    def idfromfilename(self, filename):
        return int(os.path.basename(filename)[1:])

    def BestIndex(self, constraints, orderby):
        """
        Provide information on how to best access this table.
        Must be overriden by subclass.
        @params constraints: a tuple of (column #, op) defining a constraints
        @params orderby: a tuple of (column #, desc) defining the order by
        @returns a tuple of up to 5 values:
            0: aConstraingUsage: a tuple of the same size as constraints.
                Each item is either None, argv index(int), or (argv index, omit(Bool)).
            1: idxNum(int)
            2: idxStr(string)
            3: orderByConsumed(Bool)
            4: estimatedCost(float)

        Todo: store the constraints for subsequent evaluation, and tell
            sqlite to pass the constraints parameters to Filter.
        """
        pass
    def Filter(self, idxNum, idxStr, argv):
        """
        Begin a search of a virtual table.
        @params idxNum: int value passed by BestIndex
        @params idxStr: string valued passed by BestIndex
        @params argv: constraint parameters requested by BestIndex
        @returns: None

        Todo: evaluate actual constraints, will let sqlite do the orderby.
        """
        self.filenames=glob.glob(os.path.join(self.pathname,
                                              'F[0-9][0-9][0-9][0-9][0-9][0-9][0-9]'))
        if self.filenames:
            self.cursor=0
        else:
            self.cursor=None
    def Eof(self):
        """
        Determines if the current cursor points to a valid row.
        @returns: False if valid row, True otherwise
        """
        return self.cursor is None or self.cursor>=len(self.filenames)
    def Column(self, N):
        """
        Find the value for the N-th column of the current row.
        @params N: the N-th column
        @returns: value of the N-th column
        We only have 2 columns: __rowid__ and mediadata
        """
        filename=self.filenames[self.cursor]
        if N==0:
            # __rowid__
            return self.idfromfilename(filename)
        else:
            # mediadata
            return buffer(file(filename, 'rb').read())
    def Next(self):
        """
        Move the cursor to the next row.
        @returns: None
        """
        self.cursor+=1
    def Rowid(self):
        """
        Return the rowid of the current row.
        @returns: the rowid(int) of the current row.
        """
        return self.Column(0)
    def UpdateDeleteRow(self, rowid):
        """
        Delete row rowid
        @params rowid: rowid to delete
        @returns: None
        """
        # delete the file
        os.remove(self.filenamefromid(rowid))
    def UpdateInsertRow(self, rowid, fields):
        """
        Insert a new row of data into the table
        @params rowid: if not None, use this rowid.  If None, create a new rowid
        @params fields: a tuple of the field values in the order declared in
            Create/Connet
        @returns: rowid of the new row.
        """
        if rowid is None:
            rowid=self.rowid
            self.incrementrowid()
        file(self.filenamefromid(rowid), 'wb').write(fields[1])
        return rowid
    def UpdateChangeRow(self, rowid, newrowid, fields):
        """
        Change the row of the current rowid with the new rowid and new values
        @params rowid: rowid of the current row
        @params newrowid: new rowid
        @params fields: a tuple of the field values in the order declared in
            Create/Connect
        @returns: rowid of the new row
        """
        os.remove(self.filenamefromid(rowid))
        file(self.filenamefromid(newrowid), 'wb').write(fields[1])
        return newrowid
