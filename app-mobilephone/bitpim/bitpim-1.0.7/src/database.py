### BITPIM
###
### Copyright (C) 2004 Roger Binns <rogerb@rogerbinns.com>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: database.py 4697 2008-08-24 21:21:14Z djpham $

"""Interface to the database"""
from __future__ import with_statement
import os
import copy
import time
import sha
import random

import apsw

import common
###
### The first section of this file deals with typical objects used to
### represent data items and various methods for wrapping them.
###



class basedataobject(dict):
    """A base object derived from dict that is used for various
    records.  Existing code can just continue to treat it as a dict.
    New code can treat it as dict, as well as access via attribute
    names (ie object["foo"] or object.foo).  attribute name access
    will always give a result includes None if the name is not in
    the dict.

    As a bonus this class includes checking of attribute names and
    types in non-production runs.  That will help catch typos etc.
    For production runs we may be receiving data that was written out
    by a newer version of BitPim so we don't check or error."""
    # which properties we know about
    _knownproperties=[]
    # which ones we know about that should be a list of dicts
    _knownlistproperties={'serials': ['sourcetype', '*']}
    # which ones we know about that should be a dict
    _knowndictproperties={}

    if __debug__:
        # in debug code we check key name and value types

        def _check_property(self,name,value=None):
            # check it
            assert isinstance(name, (str, unicode)), "keys must be a string type"
            assert name in self._knownproperties or name in self._knownlistproperties or name in self._knowndictproperties, "unknown property named '"+name+"'"
            if value is None: return
            if name in getattr(self, "_knownlistproperties"):
                assert isinstance(value, list), "list properties ("+name+") must be given a list as value"
                # each list member must be a dict
                for v in value:
                    self._check_property_dictvalue(name,v)
                return
            if name in getattr(self, "_knowndictproperties"):
                assert isinstance(value, dict), "dict properties ("+name+") must be given a dict as value"
                self._check_property_dictvalue(name,value)
                return
            # the value must be a basetype supported by apsw/SQLite
            assert isinstance(value, (str, unicode, buffer, int, long, float)), "only serializable types supported for values"

        def _check_property_dictvalue(self, name, value):
            assert isinstance(value, dict), "item(s) in "+name+" (a list) must be dicts"
            assert name in self._knownlistproperties or name in self._knowndictproperties
            if name in self._knownlistproperties:
                for key in value:
                    assert key in self._knownlistproperties[name] or '*' in self._knownlistproperties[name], "dict key "+key+" as member of item in list "+name+" is not known"
                    v=value[key]
                    assert isinstance(v, (str, unicode, buffer, int, long, float)), "only serializable types supported for values"
            elif name in self._knowndictproperties:
                for key in value:
                    assert key in self._knowndictproperties[name] or '*' in self._knowndictproperties[name], "dict key "+key+" as member of dict in item "+name+" is not known"
                    v=value[key]
                    assert isinstance(v, (str, unicode, buffer, int, long, float)), "only serializable types supported for values"
                
                
        def update(self, items):
            assert isinstance(items, dict), "update only supports dicts" # Feel free to fix this code ...
            for k in items:
                self._check_property(k, items[k])
            super(basedataobject, self).update(items)

        def __getitem__(self, name):
            # check when they are retrieved, not set.  I did try
            # catching the append method, but the layers of nested
            # namespaces got too confused
            self._check_property(name)
            v=super(basedataobject, self).__getitem__(name)
            self._check_property(name, v)
            return v

        def __setitem__(self, name, value):
            self._check_property(name, value)
            super(basedataobject,self).__setitem__(name, value)

        def __setattr__(self, name, value):
            # note that we map setattr to update the dict
            self._check_property(name, value)
            self.__setitem__(name, value)

        def __getattr__(self, name):
            if name not in self._knownproperties and name not in self._knownlistproperties and  name not in self._knowndictproperties:
                raise AttributeError(name)
            self._check_property(name)
            if name in self.keys():
                return self[name]
            return None

        def __delattr__(self, name):
            self._check_property(name)
            if name in self.keys():
                del self[name]

    else:
        # non-debug mode - we don't do any attribute name/value type
        # checking as the data may (legitimately) be from a newer
        # version of the program.
        def __setattr__(self, name, value):
            # note that we map setattr to update the dict
            super(basedataobject,self).__setitem__(name, value)

        def __getattr__(self, name):
            # and getattr checks the dict
            if name not in self._knownproperties and name not in self._knownlistproperties and  name not in self._knowndictproperties:
                raise AttributeError(name)
            if name in self.keys():
                return self[name]
            return None

        def __delattr__(self, name):
            if name in self.keys():
                del self[name]

    # various methods for manging serials
    def GetBitPimSerial(self):
        "Returns the BitPim serial for this item"
        if "serials" not in self:
            raise KeyError("no bitpim serial present")
        for v in self.serials:
            if v["sourcetype"]=="bitpim":
                return v["id"]
        raise KeyError("no bitpim serial present")

    # rng seeded at startup
    _persistrandom=random.Random()
    _shathingy=None
    def _getnextrandomid(self, item):
        """Returns random ids used to give unique serial numbers to items

        @param item: any object - its memory location is used to help randomness
        @returns: a 20 character hexdigit string
        """
        if basedataobject._shathingy is None:
            basedataobject._shathingy=sha.new()
            basedataobject._shathingy.update(`basedataobject._persistrandom.random()`)
        basedataobject._shathingy.update(`id(self)`)
        basedataobject._shathingy.update(`basedataobject._persistrandom.random()`)
        basedataobject._shathingy.update(`id(item)`)
        return basedataobject._shathingy.hexdigest()

    
    def EnsureBitPimSerial(self):
        "Ensures this entry has a serial"
        if self.serials is None:
            self.serials=[]
        for v in self.serials:
            if v["sourcetype"]=="bitpim":
                return
        self.serials.append({'sourcetype': "bitpim", "id": self._getnextrandomid(self.serials)})

class dataobjectfactory:
    "Called by the code to read in objects when it needs a new object container"
    def __init__(self, dataobjectclass=basedataobject):
        self.dataobjectclass=dataobjectclass

    if __debug__:
        def newdataobject(self, values={}):
            v=self.dataobjectclass()
            if len(values):
                v.update(values)
            return v
    else:
        def newdataobject(self, values={}):
            return self.dataobjectclass(values)


def extractbitpimserials(dict):
    """Returns a new dict with keys being the bitpim serial for each
    row.  Each item must be derived from basedataobject"""

    res={}
    
    for record in dict.itervalues():
        res[record.GetBitPimSerial()]=record

    return res

def ensurebitpimserials(dict):
    """Ensures that all records have a BitPim serial.  Each item must
    be derived from basedataobject"""
    for record in dict.itervalues():
        record.EnsureBitPimSerial()

def findentrywithbitpimserial(dict, serial):
    """Returns the entry from dict whose bitpim serial matches serial"""
    for record in dict.itervalues():
        if record.GetBitPimSerial()==serial:
            return record
    raise KeyError("not item with serial "+serial+" found")

def ensurerecordtype(dict, factory):
    for key,record in dict.iteritems():
        if not isinstance(record, basedataobject):
            dict[key]=factory.newdataobject(record)
        


# a factory that uses dicts to allocate new data objects
dictdataobjectfactory=dataobjectfactory(dict)




###
### Actual database interaction is from this point on
###


# Change this to True to see what is going on under the hood.  It
# will produce a lot of output!
TRACE=False

def ExclusiveWrapper(method):
    """Wrap a method so that it has an exclusive lock on the database
    (noone else can read or write) until it has finished"""

    # note that the existing threading safety checks in apsw will
    # catch any thread abuse issues.
    def _transactionwrapper(*args, **kwargs):
        # arg[0] should be a Database instance
        assert isinstance(args[0], Database)
        with args[0]:
            return method(*args, **kwargs)

    setattr(_transactionwrapper, "__doc__", getattr(method, "__doc__"))
    return _transactionwrapper

def sqlquote(s):
    "returns an sqlite quoted string (the return value will begin and end with single quotes)"
    return "'"+s.replace("'", "''")+"'"

def idquote(s):
    """returns an sqlite quoted identifier (eg for when a column name is also an SQL keyword

    The value returned is quoted in square brackets"""
    return '['+s+']'

class IntegrityCheckFailed(Exception): pass

class Database:

    # Make this class a context manager so it can be used with WITH blocks
    def __enter__(self):
        self.excounter+=1
        self.transactionwrite=False
        if self.excounter==1:
            if TRACE:
                print "BEGIN EXCLUSIVE TRANSACTION"
            self.cursor.execute("BEGIN EXCLUSIVE TRANSACTION")
            self._schemacache={}
        return self

    def __exit__(self, ex_type, ex_value, tb):
        self.excounter-=1
        if self.excounter==0:
            w=self.transactionwrite
            if tb is None:
                # no exception, so commit
                cmd="COMMIT TRANSACTION" if w else "END TRANSACTION"
            else:
                # an exception occurred, so rollback
                cmd="ROLLBACK TRANSACTION" if w else "END TRANSACTION"
            if TRACE:
                print cmd
            self.cursor.execute(cmd)

    def __del__(self):
        # connections have to be closed now
        self.connection.close(True)

    def __init__(self, filename, virtualtables=None):
        """
        @param filename: database filename
        @param virtualtables: a list of dict specifying the virtual tables
            Each dict is expected to have the following keys:
            'tablename': the name of the virtual table
            'modulename': the name of the module that implements this virtual
                table
            'moduleclass': the ModuleBase subclass that implements this
                virtual table
            'args': arguments passed to instantiaion of the module class
        """
        self.connection=apsw.Connection(filename)
        self.cursor=self.connection.cursor()
        # first tell sqlite to use the pre 3.4 format.  this will allow downgrades
        self.cursor.execute("PRAGMA legacy_file_format=1") # nb you don't get an error for unknown pragmas
        # we always do an integrity check second
        icheck=[]
        print "database integrity check"
        for row in self.cursor.execute("PRAGMA integrity_check"):
            icheck.extend(row)
        print "database integrity check complete"
        icheck="\n".join(icheck)
        if icheck!="ok":
            raise IntegrityCheckFailed(icheck)
        # exclusive lock counter
        self.excounter=0
        # this should be set to true by any code that writes - it is
        # used by the exclusivewrapper to tell if it should do a
        # commit/rollback or just a plain end
        self.transactionwrite=False
        # a cache of the table schemas
        self._schemacache={}
        self.sql=self.cursor.execute
        self.sqlmany=self.cursor.executemany
        if TRACE:
            self.cursor.setexectrace(self._sqltrace)
            self.cursor.setrowtrace(self._rowtrace)
        if virtualtables is not None:
            # virtual tables are specified
            for vtable in virtualtables:
                # register the module
                self.connection.createmodule(vtable['modulename'],
                                             vtable['moduleclass'](*vtable['args']))
                if not self.doestableexist(vtable['tablename']):
                    # and declare the virtual table
                    self.sql('CREATE VIRTUAL TABLE %s USING %s;'%(idquote(vtable['tablename']),
                                                                  idquote(vtable['modulename'])))

    def _sqltrace(self, cmd, bindings):
        print "SQL:",cmd
        if bindings:
            print " bindings:",bindings
        return True

    def _rowtrace(self, *row):
        print "ROW:",row
        return row

    def sql(self, statement, params=()):
        "Executes statement and return a generator of the results"
        # this is replaced in init
        assert False

    def sqlmany(self, statement, params):
        "execute statements repeatedly with params"
        # this is replaced in init
        assert False
            
    def doestableexist(self, tablename):
        if tablename in self._schemacache:
            return True
        return bool(self.sql("select count(*) from sqlite_master where type='table' and name=%s" % (sqlquote(tablename),)).next()[0])

    def getcolumns(self, tablename, onlynames=False):
        res=self._schemacache.get(tablename,None)
        if res is None:
            res=[]
            for colnum,name,type, _, default, primarykey in self.sql("pragma table_info("+idquote(tablename)+")"):
                if primarykey:
                    type+=" primary key"
                res.append([colnum,name,type])
            self._schemacache[tablename]=res
        if onlynames:
            return [name for colnum,name,type in res]
        return res

    @ExclusiveWrapper
    def savemajordict(self, tablename, dict, timestamp=None):
        """This is the entrypoint for saving a first level dictionary
        such as the phonebook or calendar.

        @param tablename: name of the table to use
        @param dict: The dictionary of record.  The key must be the uniqueid for each record.
                   The @L{extractbitpimserials} function can do the conversion for you for
                   phonebook and similar formatted records.
        @param timestamp: the UTC time in seconds since the epoch.  This is 
        """

        if timestamp is None:
            timestamp=time.time()

        # work on a shallow copy of dict
        dict=dict.copy()
        
        # make sure the table exists first
        if not self.doestableexist(tablename):
            # create table and include meta-fields
            self.transactionwrite=True
            self.sql("create table %s (__rowid__ integer primary key, __timestamp__, __deleted__ integer, __uid__ varchar)" % (idquote(tablename),))

        # get the latest values for each guid ...
        current=self.getmajordictvalues(tablename)
        # compare what we have, and update/mark deleted as appropriate ...
        deleted=[k for k in current if k not in dict]
        new=[k for k in dict if k not in current]
        modified=[k for k in dict if k in current] # only potentially modified ...

        # deal with modified first
        dl=[]
        for i,k in enumerate(modified):
            if dict[k]==current[k]:
                # unmodified!
                del dict[k]
                dl.append(i)
        dl.reverse()
        for i in dl:
            del modified[i]

        # add deleted entries back into dict
        for d in deleted:
            assert d not in dict
            dict[d]=current[d]
            dict[d]["__deleted__"]=1
            
        # now we only have new, changed and deleted entries left in dict

        # examine the keys in dict
        dk=[]
        for k in dict.keys():
            # make a copy since we modify values, but it doesn't matter about deleted since we own those
            if k not in deleted:
                dict[k]=dict[k].copy()
            for kk in dict[k]:
                if kk not in dk:
                    dk.append(kk)
        # verify that they don't start with __
        assert len([k for k in dk if k.startswith("__") and not k=="__deleted__"])==0
        # get database keys
        dbkeys=self.getcolumns(tablename, onlynames=True)
        # are any missing?
        missing=[k for k in dk if k not in dbkeys]
        if len(missing):
            creates=[]
            # for each missing key, we have to work out if the value
            # is a list or dict type (which we indirect to another table)
            for m in missing:
                islist=None
                isdict=None
                isnotindirect=None
                for r in dict.keys():
                    record=dict[r]
                    v=record.get(m,None)
                    if v is None:
                        continue
                    if isinstance(v, list):
                        islist=record
                    elif isinstance(v,type({})):
                        isdict=record
                    else:
                        isnotindirect=record
                    # in devel code, we check every single value
                    # in production, we just use the first we find
                    if not __debug__:
                        break
                if islist is None and isdict is None and isnotindirect is None:
                    # they have the key but no record has any values, so we ignore it
                    del dk[dk.index(m)]
                    continue
                # don't do this type abuse at home ...
                if int(islist is not None)+int(isdict is not None)+int(isnotindirect is not None)!=int(True):
                    # can't have it more than one way
                    raise ValueError("key %s for table %s has values with inconsistent types. eg LIST: %s, DICT: %s, NOTINDIRECT: %s" % (m,tablename,`islist`,`isdict`,`isnotindirect`))
                if islist is not None:
                    creates.append( (m, "indirectBLOB") )
                    continue
                if isdict:
                    creates.append( (m, "indirectdictBLOB"))
                    continue
                if isnotindirect is not None:
                    creates.append( (m, "valueBLOB") )
                    continue
                assert False, "You can't possibly get here!"
            if len(creates):
                self._altertable(tablename, creates, [], createindex=1)

        # write out indirect values
        dbtkeys=self.getcolumns(tablename)
        # for every indirect, we have to replace the value with a pointer
        for _,n,t in dbtkeys:
            if t in ("indirectBLOB", "indirectdictBLOB"):
                indirects={}
                for r in dict.keys():
                    record=dict[r]
                    v=record.get(n,None)
                    if v is not None:
                        if not len(v): # set zero length lists/dicts to None
                            record[n]=None
                        else:
                            if t=="indirectdictBLOB":
                                indirects[r]=[v] # make it a one item dict list
                            else:
                                indirects[r]=v
                if len(indirects):
                    self.updateindirecttable(tablename+"__"+n, indirects)
                    for r in indirects.keys():
                        dict[r][n]=indirects[r]

        # and now the main table
        for k in dict.keys():
            record=dict[k]
            record["__uid__"]=k
            rk=[x for x,y in record.items() if y is not None]
            rk.sort()
            cmd=["insert into", idquote(tablename), "( [__timestamp__],"]
            cmd.append(",".join([idquote(r) for r in rk]))
            cmd.extend([")", "values", "(?,"])
            cmd.append(",".join(["?" for r in rk]))
            cmd.append(")")
            self.sql(" ".join(cmd), [timestamp]+[record[r] for r in rk])
            self.transactionwrite=True
        
    def updateindirecttable(self, tablename, indirects):
        # this is mostly similar to savemajordict, except we only deal
        # with lists of dicts, and we find existing records with the
        # same value if possible

        # does the table even exist?
        if not self.doestableexist(tablename):
            # create table and include meta-fields
            self.sql("create table %s (__rowid__ integer primary key)" % (idquote(tablename),))
            self.transactionwrite=True
        # get the list of keys from indirects
        datakeys=[]
        for i in indirects.keys():
            assert isinstance(indirects[i], list)
            for v in indirects[i]:
                assert isinstance(v, dict)
                for k in v.keys():
                    if k not in datakeys:
                        assert not k.startswith("__")
                        datakeys.append(k)
        # get the keys from the table
        dbkeys=self.getcolumns(tablename, onlynames=True)
        # are any missing?
        missing=[k for k in datakeys if k not in dbkeys]
        if len(missing):
            self._altertable(tablename, [(m,"valueBLOB") for m in missing], [], createindex=2)
        # for each row we now work out the indirect information
        for r in indirects:
            res=tablename+","
            for record in indirects[r]:
                cmd=["select __rowid__ from", idquote(tablename), "where"]
                params=[]
                coals=[]
                for d in datakeys:
                    v=record.get(d,None)
                    if v is None:
                        coals.append(idquote(d))
                    else:
                        if cmd[-1]!="where":
                            cmd.append("and")
                        cmd.extend([idquote(d), "= ?"])
                        params.append(v)
                assert cmd[-1]!="where" # there must be at least one non-none column!
                if len(coals)==1:
                    cmd.extend(["and",coals[0],"isnull"])
                elif len(coals)>1:
                    cmd.extend(["and coalesce(",",".join(coals),") isnull"])

                found=None
                for found in self.sql(" ".join(cmd), params):
                    # get matching row
                    found=found[0]
                    break
                if found is None:
                    # add it
                    cmd=["insert into", idquote(tablename), "("]
                    params=[]
                    for k in record:
                        if cmd[-1]!="(":
                            cmd.append(",")
                        cmd.append(k)
                        params.append(record[k])
                    cmd.extend([")", "values", "("])
                    cmd.append(",".join(["?" for p in params]))
                    cmd.append("); select last_insert_rowid()")
                    found=self.sql(" ".join(cmd), params).next()[0]
                    self.transactionwrite=True
                res+=`found`+","
            indirects[r]=res
                        
    @ExclusiveWrapper
    def getmajordictvalues(self, tablename, factory=dictdataobjectfactory,
                           at_time=None):

        if not self.doestableexist(tablename):
            return {}

        res={}
        uids=[u[0] for u in self.sql("select distinct __uid__ from %s" % (idquote(tablename),))]
        schema=self.getcolumns(tablename)
        for colnum,name,type in schema:
            if name=='__deleted__':
                deleted=colnum
            elif name=='__uid__':
                uid=colnum
        # get all relevant rows
        if isinstance(at_time, (int, float)):
            sql_string="select * from %s where __uid__=? and __timestamp__<=%f order by __rowid__ desc limit 1" % (idquote(tablename), float(at_time))
        else:
            sql_string="select * from %s where __uid__=? order by __rowid__ desc limit 1" % (idquote(tablename),)
        indirects={}
        for row in self.sqlmany(sql_string, [(u,) for u in uids]):
            if row[deleted]:
                continue
            record=factory.newdataobject()
            for colnum,name,type in schema:
                if name.startswith("__") or type not in ("valueBLOB", "indirectBLOB", "indirectdictBLOB") or row[colnum] is None:
                    continue
                if type=="valueBLOB":
                    record[name]=row[colnum]
                    continue
                assert type=="indirectBLOB" or type=="indirectdictBLOB"
                if name not in indirects:
                    indirects[name]=[]
                indirects[name].append( (row[uid], row[colnum], type) )
            res[row[uid]]=record
        # now get the indirects
        for name,values in indirects.iteritems():
            for uid,v,type in values:
                fieldvalue=self._getindirect(v)
                if fieldvalue:
                    if type=="indirectBLOB":
                        res[uid][name]=fieldvalue
                    else:
                        res[uid][name]=fieldvalue[0]
        return res

    def _getindirect(self, what):
        """Gets a list of values (indirect) as described by what
        @param what: what to get - eg phonebook_serials,1,3,5,
                      (note there is always a trailing comma)
        """

        tablename,rows=what.split(',', 1)
        schema=self.getcolumns(tablename)
        
        res=[]
        for row in self.sqlmany("select * from %s where __rowid__=?" %
                                (idquote(tablename),), [(int(long(r)),) for r in rows.split(',') if len(r)]):
            record={}
            for colnum,name,type in schema:
                if name.startswith("__") or type not in ("valueBLOB", "indirectBLOB", "indirectdictBLOB") or row[colnum] is None:
                    continue
                if type=="valueBLOB":
                    record[name]=row[colnum]
                    continue
                assert type=="indirectBLOB" or type=="indirectdictBLOB"
                assert False, "indirect in indirect not handled"
            assert len(record),"Database._getindirect has zero len record"
            res.append(record)
        assert len(res), "Database._getindirect has zero len res"
        return res
        
    def _altertable(self, tablename, columnstoadd, columnstodel, createindex=0):
        """Alters the named table by deleting the specified columns, and
        adding the listed columns

        @param tablename: name of the table to alter
        @param columnstoadd: a list of (name,type) of the columns to add
        @param columnstodel: a list name of the columns to delete
        @param createindex: what sort of index to create.  0 means none, 1 means on just __uid__ and 2 is on all data columns
        """
        # indexes are automatically dropped when table is dropped so we don't need to
        dbtkeys=[x for x in self.getcolumns(tablename) \
                 if x[1] not in columnstodel]
        # clean out cache entry since we are about to invalidate it
        del self._schemacache[tablename]
        self.transactionwrite=True
        cmd=["create", "temporary", "table", idquote("backup_"+tablename),
             "(",
             ','.join(['%s %s'%(idquote(n), t) for _,n,t in dbtkeys]),
             ")"]
        self.sql(" ".join(cmd))
        # copy the values into the temporary table
        self.sql("insert into %s select %s from %s" % (idquote("backup_"+tablename),
                                                       ','.join([idquote(n) for _,n,_ in dbtkeys]),
                                                       idquote(tablename)))
        # drop the source table
        self.sql("drop table %s" % (idquote(tablename),))
        # recreate the source table with new columns
        del cmd[1] # remove temporary
        cmd[2]=idquote(tablename) # change tablename
        cmd[-2]=','.join(['%s %s'%(idquote(n), t) for _,n,t in dbtkeys]+\
                         ['%s %s'%(idquote(n), t) for n,t in columnstoadd]) # new list of columns
        self.sql(" ".join(cmd))
        # create index if needed
        if createindex:
            if createindex==1:
                cmd=["create index", idquote("__index__"+tablename), "on", idquote(tablename), "(__uid__)"]
            elif createindex==2:
                cmd=["create index", idquote("__index__"+tablename), "on", idquote(tablename), "("]
                cols=[]
                for _,n,t in dbtkeys:
                    if not n.startswith("__"):
                        cols.append(idquote(n))
                for n,t in columnstoadd:
                    cols.append(idquote(n))
                cmd.extend([",".join(cols), ")"])
            else:
                raise ValueError("bad createindex "+`createindex`)
            self.sql(" ".join(cmd))
        # put values back in
        cmd=["insert into", idquote(tablename), '(',
             ','.join([idquote(n) for _,n,_ in dbtkeys]),
             ")", "select * from", idquote("backup_"+tablename)]
        self.sql(" ".join(cmd))
        self.sql("drop table "+idquote("backup_"+tablename))

    @ExclusiveWrapper
    def deleteold(self, tablename, uids=None, minvalues=3, maxvalues=5, keepoldest=93):
        """Deletes old entries from the database.  The deletion is based
        on either criterion of maximum values or age of values matching.

        @param uids: You can limit the items deleted to this list of uids,
             or None for all entries.
        @param minvalues: always keep at least this number of values
        @param maxvalues: maximum values to keep for any entry (you
             can supply None in which case no old entries will be removed
             based on how many there are).
        @param keepoldest: values older than this number of days before
             now are removed.  You can also supply None in which case no
             entries will be removed based on age.
        @returns: number of rows removed,number of rows remaining
             """
        if not self.doestableexist(tablename):
            return (0,0)
        
        timecutoff=0
        if keepoldest is not None:
            timecutoff=time.time()-(keepoldest*24*60*60)
        if maxvalues is None:
            maxvalues=sys.maxint-1

        if uids is None:
            uids=[u[0] for u in self.sql("select distinct __uid__ from %s" % (idquote(tablename),))]

        deleterows=[]

        for uid in uids:
            deleting=False
            for count, (rowid, deleted, timestamp) in enumerate(
                self.sql("select __rowid__,__deleted__, __timestamp__ from %s where __uid__=? order by __rowid__ desc" % (idquote(tablename),), [uid])):
                if count<minvalues:
                    continue
                if deleting:
                    deleterows.append(rowid)
                    continue
                if count>=maxvalues or timestamp<timecutoff:
                    deleting=True
                    if deleted:
                        # we are ok, this is an old value now deleted, so we can remove it
                        deleterows.append(rowid)
                        continue
                    # we don't want to delete current data (which may
                    # be very old and never updated)
                    if count>0:
                        deleterows.append(rowid)
                    continue

        self.sqlmany("delete from %s where __rowid__=?" % (idquote(tablename),), [(r,) for r in deleterows])

        return len(deleterows), self.sql("select count(*) from "+idquote(tablename)).next()[0]

    @ExclusiveWrapper
    def savelist(self, tablename, values):
        """Just save a list of items (eg categories).  There is no versioning or transaction history.

        Internally the table has two fields.  One is the actual value and the other indicates if
        the item is deleted.
        """

        # a tuple of the quoted table name
        tn=(idquote(tablename),)
        
        if not self.doestableexist(tablename):
            self.sql("create table %s (__rowid__ integer primary key, item, __deleted__ integer)" % tn)

        # some code to demonstrate my lack of experience with SQL ....
        delete=[]
        known=[]
        revive=[]
        for row, item, dead in self.sql("select __rowid__,item,__deleted__ from %s" % tn):
            known.append(item)
            if item in values:
                # we need this row
                if dead:
                    revive.append((row,))
                continue
            if dead:
                # don't need this entry and it is dead anyway
                continue
            delete.append((row,))
        create=[(v,) for v in values if v not in known]

        # update table as appropriate
        self.sqlmany("update %s set __deleted__=0 where __rowid__=?" % tn, revive)
        self.sqlmany("update %s set __deleted__=1 where __rowid__=?" % tn, delete)
        self.sqlmany("insert into %s (item, __deleted__) values (?,0)" % tn, create)
        if __debug__:
            vdup=values[:]
            vdup.sort()
            vv=self.loadlist(tablename)
            vv.sort()
            assert vdup==vv

    @ExclusiveWrapper
    def loadlist(self, tablename):
        """Loads a list of items (eg categories)"""
        if not self.doestableexist(tablename):
            return []
        return [v[0] for v in self.sql("select item from %s where __deleted__=0" % (idquote(tablename),))]
        
    @ExclusiveWrapper
    def getchangescount(self, tablename):
        """Return the number of additions, deletions, and modifications
        made to this table over time.
        Expected fields containted in this table: __timestamp__,__deleted__,
        __uid__
        Assuming that both __rowid__ and __timestamp__ values are both ascending
        """
        if not self.doestableexist(tablename):
            return {}
        tn=idquote(tablename)
        # get the unique dates of changes
        sql_cmd='select distinct __timestamp__ from %s' % tn
        # setting up the return dict
        res={}
        for t in self.sql(sql_cmd):
            res[t[0]]={ 'add': 0, 'del': 0, 'mod': 0 }
        # go through the table and count the changes
        existing_uid={}
        sql_cmd='select __timestamp__,__uid__,__deleted__ from %s order by __timestamp__ asc' % tn
        for e in self.sql(sql_cmd):
            tt=e[0]
            uid=e[1]
            del_flg=e[2]
            if existing_uid.has_key(uid):
                if del_flg:
                    res[tt]['del']+=1
                    del existing_uid[uid]
                else:
                    res[tt]['mod']+=1
            else:
                existing_uid[uid]=None
                res[tt]['add']+=1
        return res

class ModuleBase(object):
    """Base class to implement a specific Virtual Table module with apsw.
    For more info:
    http://www.sqlite.org/cvstrac/wiki/wiki?p=VirtualTables
    http://www.sqlite.org/cvstrac/wiki/wiki?p=VirtualTableMethods
    http://www.sqlite.org/cvstrac/wiki/wiki?p=VirtualTableBestIndexMethod
    """
    def __init__(self, field_names):
        self.connection=None
        self.table_name=None
        # the first field is ALWAYS __rowid__ to be consistent with Database
        self.field_names=('__rowid__',)+field_names
    def Create(self, connection, modulename, databasename, vtablename, *args):
        """Called when the virtual table is created.
        @param connection: an instance of apsw.Connection
        @param modulename: string name of the module being invoked
        @param databasename: string name of this database
        @param vtablename: string name of this new virtual table
        @param args: additional arguments sent from the CREATE VIRTUAL TABLE
            statement
        @returns: a tuple of 2 values: an sql string describing the table, and
            an object implementing it: Me!
        """
        self.table_name=vtablename
        fields=['__rowid__ integer primary key']
        for field in self.field_names[1:]:
            fields.append(idquote(field)+' valueBLOB')
        fields='(%s)'%','.join(fields)
        return ('create table %s %s;'%(idquote(vtablename), fields), self)

    def Connect(self, connection, modulename, databasename, vtablename, *args):
        """Connect to an existing virtual table, by default it is identical
        to Create
        """
        return self.Create(connection, modulename, databasename, vtablename,
                           *args)

    def Destroy(self):
        """Release a connection to a virtual table and destroy the underlying
        table implementation.  By default, we do nothing.
        """
        pass
    def Disconnect(self):
        """Release a connection to a virtual table.  By default, we do nothing.
        """
        pass

    def BestIndex(self, constraints, orderby):
        """Provide information on how to best access this table.
        Must be overriden by subclass.
        @param constraints: a tuple of (column #, op) defining a constraints
        @param orderby: a tuple of (column #, desc) defining the order by
        @returns a tuple of up to 5 values:
            0: aConstraingUsage: a tuple of the same size as constraints.
                Each item is either None, argv index(int), or (argv index, omit(Bool)).
            1: idxNum(int)
            2: idxStr(string)
            3: orderByConsumed(Bool)
            4: estimatedCost(float)
        """
        raise NotImplementedError

    def Begin(self):
        pass
    def Sync(self):
        pass
    def Commit(self):
        pass
    def Rollback(self):
        pass

    def Open(self):
        """Create/prepare a cursor used for subsequent reading.
        @returns: the implementor object: Me!
        """
        return self
    def Close(self):
        """Close a cursor previously created by Open
        By default, do nothing
        """
        pass
    def Filter(self, idxNum, idxStr, argv):
        """Begin a search of a virtual table.
        @param idxNum: int value passed by BestIndex
        @param idxStr: string valued passed by BestIndex
        @param argv: constraint parameters requested by BestIndex
        @returns: None
        """
        raise NotImplementedError
    def Eof(self):
        """Determines if the current cursor points to a valid row.
        The Sqlite doc is wrong on this.
        @returns: True if NOT valid row, False otherwise
        """
        raise NotImplementedError
    def Column(self, N):
        """Find the value for the N-th column of the current row.
        @param N: the N-th column
        @returns: value of the N-th column
        """
        raise NotImplementedError
    def Next(self):
        """Move the cursor to the next row.
        @returns: None
        """
        raise NotImplementedError
    def Rowid(self):
        """Return the rowid of the current row.
        @returns: the rowid(int) of the current row.
        """
        raise NotImplementedError
    def UpdateDeleteRow(self, rowid):
        """Delete row rowid
        @param rowid:
        @returns: None
        """
        raise NotImplementedError
    def UpdateInsertRow(self, rowid, fields):
        """Insert a new row of data into the table
        @param rowid: if not None, use this rowid.  If None, create a new rowid
        @param fields: a tuple of the field values in the order declared in
            Create/Connet
        @returns: rowid of the new row.
        """
        raise NotImplementedError
    def UpdateChangeRow(self, rowid, newrowid, fields):
        """Change the row of the current rowid with the new rowid and new values
        @param rowid: rowid of the current row
        @param newrowid: new rowid
        @param fields: a tuple of the field values in the order declared in
            Create/Connect
        @returns: rowid of the new row
        """
        raise NotImplementedError

if __name__=='__main__':
    import common
    import sys
    import time
    import os

    sys.excepthook=common.formatexceptioneh


    # our own hacked version for testing
    class phonebookdataobject(basedataobject):
        # no change to _knownproperties (all of ours are list properties)
        _knownlistproperties=basedataobject._knownlistproperties.copy()
        _knownlistproperties.update( {'names': ['title', 'first', 'middle', 'last', 'full', 'nickname'],
                                      'categories': ['category'],
                                      'emails': ['email', 'type'],
                                      'urls': ['url', 'type'],
                                      'ringtones': ['ringtone', 'use'],
                                      'addresses': ['type', 'company', 'street', 'street2', 'city', 'state', 'postalcode', 'country'],
                                      'wallpapers': ['wallpaper', 'use'],
                                      'flags': ['secret'],
                                      'memos': ['memo'],
                                      'numbers': ['number', 'type', 'speeddial'],
                                      # serials is in parent object
                                      })
        _knowndictproperties=basedataobject._knowndictproperties.copy()
        _knowndictproperties.update( {'repeat': ['daily', 'orange']} )

    phonebookobjectfactory=dataobjectfactory(phonebookdataobject)
    
    # use the phonebook out of the examples directory
    try:
        execfile(os.getenv("DBTESTFILE", "examples/phonebook-index.idx"))
    except UnicodeError:
        common.unicode_execfile(os.getenv("DBTESTFILE", "examples/phonebook-index.idx"))

    ensurerecordtype(phonebook, phonebookobjectfactory)

    phonebookmaster=phonebook

    def testfunc():
        global phonebook, TRACE, db

        # note that iterations increases the size of the
        # database/journal and will make each one take longer and
        # longer as the db/journal gets bigger
        if len(sys.argv)>=2:
            iterations=int(sys.argv[1])
        else:
            iterations=1
        if iterations >1:
            TRACE=False

        db=Database("testdb")


        b4=time.time()
        

        for i in xrange(iterations):
            phonebook=phonebookmaster.copy()
            
            # write it out
            db.savemajordict("phonebook", extractbitpimserials(phonebook))

            # check what we get back is identical
            v=db.getmajordictvalues("phonebook")
            assert v==extractbitpimserials(phonebook)

            # do a deletion
            del phonebook[17] # james bond @ microsoft
            db.savemajordict("phonebook", extractbitpimserials(phonebook))
            # and verify
            v=db.getmajordictvalues("phonebook")
            assert v==extractbitpimserials(phonebook)

            # modify a value
            phonebook[15]['addresses'][0]['city']="Bananarama"
            db.savemajordict("phonebook", extractbitpimserials(phonebook))
            # and verify
            v=db.getmajordictvalues("phonebook")
            assert v==extractbitpimserials(phonebook)

        after=time.time()

        print "time per iteration is",(after-b4)/iterations,"seconds"
        print "total time was",after-b4,"seconds for",iterations,"iterations"

        if iterations>1:
            print "testing repeated reads"
            b4=time.time()
            for i in xrange(iterations*10):
                db.getmajordictvalues("phonebook")
            after=time.time()
            print "\ttime per iteration is",(after-b4)/(iterations*10),"seconds"
            print "\ttotal time was",after-b4,"seconds for",iterations*10,"iterations"
            print
            print "testing repeated writes"
            x=extractbitpimserials(phonebook)
            k=x.keys()
            b4=time.time()
            for i in xrange(iterations*10):
                # we remove 1/3rd of the entries on each iteration
                xcopy=x.copy()
                for l in range(i,i+len(k)/3):
                    del xcopy[k[l%len(x)]]
                db.savemajordict("phonebook",xcopy)
            after=time.time()
            print "\ttime per iteration is",(after-b4)/(iterations*10),"seconds"
            print "\ttotal time was",after-b4,"seconds for",iterations*10,"iterations"



    if len(sys.argv)==3:
        # also run under hotspot then
        def profile(filename, command):
            import hotshot, hotshot.stats, os
            file=os.path.abspath(filename)
            profile=hotshot.Profile(file)
            profile.run(command)
            profile.close()
            del profile
            howmany=100
            stats=hotshot.stats.load(file)
            stats.strip_dirs()
            stats.sort_stats('time', 'calls')
            stats.print_stats(100)
            stats.sort_stats('cum', 'calls')
            stats.print_stats(100)
            stats.sort_stats('calls', 'time')
            stats.print_stats(100)
            sys.exit(0)

        profile("dbprof", "testfunc()")

    else:
        testfunc()
        

