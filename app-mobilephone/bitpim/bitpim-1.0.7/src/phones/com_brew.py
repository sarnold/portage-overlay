### BITPIM
###
### Copyright (C) 2003-2004 Roger Binns <rogerb@rogerbinns.com>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: com_brew.py 4783 2010-01-14 00:09:41Z djpham $

"""Implements the "Brew" filesystem protocol"""

import os
import p_brew
import time
import cStringIO
import com_phone
import prototypes
import common

class BrewNotSupported(Exception):
    """This phone not supported"""
    pass

class BrewCommandException(Exception):
    def __init__(self, errnum, str=None):
        if str is None:
            str="Brew Error 0x%02x" % (errnum,)
        Exception.__init__(self, str)
        self.errnum=errnum

class BrewNoMoreEntriesException(BrewCommandException):
    def __init__(self, errnum=0x1c):
        BrewCommandException.__init__(self, errnum, "No more directory entries")

class BrewNoSuchDirectoryException(BrewCommandException):
    def __init__(self, errnum=0x08):
        BrewCommandException.__init__(self, errnum, "No such directory")

class BrewNoSuchFileException(BrewCommandException):
    def __init__(self, errnum=0x06):
        BrewCommandException.__init__(self, errnum, "No such file")

class BrewBadPathnameException(BrewCommandException):
    def __init__(self, errnum=0x1a):
        BrewCommandException.__init__(self, errnum, "Bad pathname")

class BrewFileLockedException(BrewCommandException):
    def __init__(self, errnum=0x0b):
        BrewCommandException.__init__(self, errnum, "File is locked")

class BrewNameTooLongException(BrewCommandException):
    def __init__(self, errnum=0x0d):
        BrewCommandException.__init__(self, errnum, "Name is too long")

class BrewDirectoryExistsException(BrewCommandException):
    def __init__(self, errnum=0x07):
        BrewCommandException.__init__(self, errnum, "Directory already exists")

class BrewBadBrewCommandException(BrewCommandException):
    def __init__(self, errnum=0x100):
        BrewCommandException.__init__(self, errnum, "The phone did not recognise the brew command")

class BrewMalformedBrewCommandException(BrewCommandException):
    def __init__(self, errnum=0x101):
        BrewCommandException.__init__(self, errnum, "The parameters in the last brew command were invalid")

class BrewAccessDeniedException(BrewCommandException):
    def __init__(self, errnum=0x04, filename=None):
        BrewCommandException.__init__(self, errnum, "Access Denied. Access to the file/directory may be blocked on this phone")

class BrewFileSystemFullException(BrewCommandException):
    def __init__(self, errnum=0x16, filename=None):
        BrewCommandException.__init__(self, errnum, "The phone has run out of space to store any more files")

class BrewStatFileException(BrewCommandException):
    def __init__(self, errnum, filename):
        BrewCommandException.__init__(self, errnum,
                                      "Stat File %s errno %d"%(filename, errnum))


modeignoreerrortypes=com_phone.modeignoreerrortypes+(BrewCommandException,common.CommsDataCorruption)

class _DirCache:
    """This is a class that lets you do various filesystem manipulations and
    it remembers the data.  Typical usage would be if you make changes to
    files (adding, removing, rewriting) and then have to keep checking if
    files exist, add sizes etc.  This class saves the hassle of rereading
    the directory every single time.  Note that it will only see changes
    you make via this class.  If you go directly to the Brew class then
    those won't be seen.
    """
    def __init__(self, target):
        "@param target: where operations should be done after recording them here"
        self.__target=target
        self.__cache={}

    def rmfile(self, filename):
        res=self.__target.rmfile(filename)
        node=self._getdirectory(brewdirname(filename))
        if node is None: # we didn't have it
            return
        del node[brewbasename(filename)]
        return res

    def stat(self, filename):
        node=self._getdirectory(brewdirname(filename), ensure=True)
        return node.get(brewbasename(filename), None)

    def readfile(self, filename):
        node=self._getdirectory(brewdirname(filename), ensure=True)
        file=node.get(brewbasename(filename), None)
        if file is None:
            raise BrewNoSuchFileException()
        # This class only populates the 'data' portion of the file obj when needed
        data=file.get('data', None)
        if data is None:
            data=self.__target.getfilecontents(filename)
            file['data']=data
        return data

    def writefile(self, filename, contents):
        res=self.__target.writefile(filename, contents)
        node=self._getdirectory(brewdirname(filename), ensure=True)
        # we can't put the right date in since we have no idea
        # what the timezone (or the time for that matter) on the
        # phone is
        stat=node.get(brewbasename(filename), {'name': filename, 'type': 'file', 'date': (0, "")})
        stat['size']=len(contents)
        stat['data']=contents
        node[brewbasename(filename)]=stat
        return res

    def _getdirectory(self, dirname, ensure=False):
        if not ensure:
            return self.__cache.get(dirname, None)
        node=self.__cache.get(dirname, None)
        if node is not None: return node
        node={}
        fs=self.__target.getfilesystem(dirname)
        for filename in fs.keys():
            node[brewbasename(filename)]=fs[filename]
        self.__cache[dirname]=node
        return node

class DebugBrewProtocol:
    """ Emulate a phone file system using a local file system.  This is used
    when you may not have access to a physical phone, but have a copy of its
    file system.
    """
    MODEBREW="modebrew"
    _fs_path=''
    def __init__(self):
        pass
    def getfirmwareinformation(self):
        self.log("Getting firmware information")
    def explore0c(self):
        self.log("Trying stuff with command 0x0c")
    def offlinerequest(self, reset=False, delay=0):
        self.log("Taking phone offline")
        if reset:
            self.log("Resetting phone")
    def modemmoderequest(self):
        self.log("Attempting to put phone in modem mode")
    def mkdir(self, name):
        self.log("Making directory '"+name+"'")
        os.mkdir(os.path.join(self._fs_path, name))
    def mkdirs(self, directory):
        if len(directory)<1:
            return
        dirs=directory.split('/')
        for i in range(0,len(dirs)):
            try:
                self.mkdir("/".join(dirs[:i+1]))  # basically mkdir -p
            except:
                pass
    def rmdir(self,name):
        self.log("Deleting directory '"+name+"'")
        try:
            os.rmdir(os.path.join(self._fs_path, name))
        except:
            # convert to brew exception
            raise BrewNoSuchDirectoryException
    def rmfile(self,name):
        self.log("Deleting file '"+name+"'")
        try:
            os.remove(os.path.join(self._fs_path, name))
        except:
            # convert to brew exception
            raise BrewNoSuchFileException
    def rmdirs(self, path):
        self.progress(0,1, "Listing child files and directories")
        all=self.getfilesystem(path, 100)
        keys=all.keys()
        keys.sort()
        keys.reverse()
        count=0
        for k in keys:
            self.progress(count, len(keys), "Deleting "+k)
            count+=1
            if all[k]['type']=='directory':
                self.rmdir(k)
            else:
                self.rmfile(k)
        self.rmdir(path)

    def listfiles(self, dir=''):
        results={}
        self.log("Listing files in dir: '"+dir+"'")
        results={}
        _pwd=os.path.join(self._fs_path, dir)
        for _root,_dir,_file in os.walk(_pwd):
            break
        try:
            for f in _file:
                _stat=os.stat(os.path.join(_pwd, f))
                _date=_stat[8]
                _name=dir+'/'+f
                _timestr=''
                try:
                    # date is not always present in filesystem
                    _timestr=time.strftime("%x %X", time.gmtime(_date))
                except:
                    pass
                results[_name]={ 'name': _name, 'type': 'file', 'size': _stat[6],
                                 'date': (_date, _timestr) }
        except:
            pass # will happen if the directory does not exist
        return results
        
    def listsubdirs(self, dir='', recurse=0):
        results={}
        self.log("Listing subdirs in dir: '"+dir+"'")
        _pwd=os.path.join(self._fs_path, dir)
        for _root,_dir,_file in os.walk(_pwd):
            break
        for d in _dir:
            if len(dir):
                d=dir+"/"+d
            results[d]={ 'name': d, 'type': 'directory' }
            if recurse>0:
                results.update(self.listsubdirs(d, recurse-1))
        return results

    def getfilesystem(self, dir="", recurse=0):
        results={}
        _file=[]
        _dir=[]
        self.log("Listing dir '"+dir+"'")
        _pwd=os.path.join(self._fs_path, dir)
        for _root,_dir,_file in os.walk(_pwd):
            break
        for f in _file:
            _stat=os.stat(os.path.join(_pwd, f))
            _date=_stat[8]
            _name=dir+'/'+f
            _timestr=''
            try:
                # date is not always present in filesystem
                _timestr=time.strftime("%x %X", time.gmtime(_date))
            except:
                pass
            results[_name]={ 'name': _name, 'type': 'file', 'size': _stat[6],
                             'date': (_date, _timestr) }
        for d in _dir:
            _name=dir+'/'+d
            results[_name]={ 'name': _name, 'type': 'directory' }
            if recurse>0:
                results.update(self.getfilesystem(_name, recurse-1))
        return results

    def statfile(self, name):
        try:
            _stat=os.stat(os.path.join(self._fs_path, name))
            _date=_stat[8]
            results={ 'name': name, 'type': 'file', 'size': _stat[6], 'datevalue': 0x0DEB0DEB,
                      'date': (_date,
                               time.strftime("%x %X", time.gmtime(_date))) }
            return results
        except:
            # File does not exist, bail
            return None

    def writefile(self, name, contents):
        self.log("Writing file '"+name+"' bytes "+`len(contents)`)
        file(os.path.join(self._fs_path, name), 'wb').write(contents)

    def getfilecontents(self, name, use_cache=False):
        self.log("Getting file contents '"+name+"'")
        try:
            if name[0]=='/':
                return file(os.path.join(self._fs_path, name[1:]), 'rb').read()
            return file(os.path.join(self._fs_path, name), 'rb').read()
        except:
            raise BrewNoSuchFileException

    def get_brew_esn(self):
        # fake an ESN for debug mode
        return "DEBUGESN"
    def _setmodebrew(self):
        self.log('_setmodebrew: in mode BREW')
        return True
    def sendbrewcommand(self, request, responseclass, callsetmode=True):
        return NotImplementedError
    def log(self, s):
        print s
    def logdata(self, s, data, klass=None):
        print s

    def exists(self, path):
        return os.path.exists(os.path.join(self._fs_path, path))

    DirCache=_DirCache

class RealBrewProtocol:
    "Talk to a phone using the 'brew' protocol"

    MODEBREW="modebrew"
    brewterminator="\x7e"

    # phone uses Jan 6, 1980 as epoch.  Python uses Jan 1, 1970.  This is difference
    _brewepochtounix=315964800

    def __init__(self):
        # reset default encoding
        p_brew.PHONE_ENCODING=p_brew.DEFAULT_PHONE_ENCODING

    def getfirmwareinformation(self):
        self.log("Getting firmware information")
        req=p_brew.firmwarerequest()
        res=self.sendbrewcommand(req, p_brew.firmwareresponse)

    def get_brew_esn(self):
        # return the ESN of this phone
        return '%0X'%self.sendbrewcommand(p_brew.ESN_req(),
                                          p_brew.ESN_resp).esn

    def explore0c(self):
        self.log("Trying stuff with command 0x0c")
        req=p_brew.testing0crequest()
        res=self.sendbrewcommand(req, p_brew.testing0cresponse)

    def offlinerequest(self, reset=False, delay=0):
        time.sleep(delay)
        req=p_brew.setmoderequest()
        req.request=1
        self.log("Taking phone offline")
        self.sendbrewcommand(req, p_brew.setmoderesponse)
        time.sleep(delay)
        if reset:
            req=p_brew.setmoderequest()
            req.request=2
            self.log("Resetting phone")
            self.sendbrewcommand(req, p_brew.setmoderesponse)
            
    def modemmoderequest(self):
        # Perhaps we should modify sendbrewcommand to have an option to
        # not be picky about response.
        self.log("Attempting to put phone in modem mode")
        req=p_brew.setmodemmoderequest()
        buffer=prototypes.buffer()
        req.writetobuffer(buffer, logtitle="modem mode request")
        data=buffer.getvalue()
        data=common.pppescape(data+common.crcs(data))+common.pppterminator
        self.comm.write(data)
        # Response could be text or a packet
        self.comm.readsome(numchars=5)
        self.mode=self.MODENONE # Probably should add a modem mode

    def mkdir(self, name):
        self.log("Making directory '"+name+"'")
        if self.isdir(name):
            raise BrewDirectoryExistsException
        req=p_brew.mkdirrequest()
        req.dirname=name
        try:
            self.sendbrewcommand(req, p_brew.mkdirresponse)
        except BrewDirectoryExistsException:
            # sometime the phone returns this, which is OK
            pass

    def mkdirs(self, directory):
        if len(directory)<1:
            return
        dirs=directory.split('/')
        for i in range(0,len(dirs)):
            try:
                self.mkdir("/".join(dirs[:i+1]))  # basically mkdir -p
            except:
                pass


    def rmdir(self,name):
        self.log("Deleting directory '"+name+"'")
        req=p_brew.rmdirrequest()
        req.dirname=name
        self.sendbrewcommand(req, p_brew.rmdirresponse)

    def rmfile(self,name):
        self.log("Deleting file '"+name+"'")
        req=p_brew.rmfilerequest()
        req.filename=name
        self.sendbrewcommand(req, p_brew.rmfileresponse)
        file_cache.clear(name)

    def rmdirs(self, path):
        self.progress(0,1, "Listing child files and directories")
        all=self.getfilesystem(path, 100)
        keys=all.keys()
        keys.sort()
        keys.reverse()
        count=0
        for k in keys:
            self.progress(count, len(keys), "Deleting "+k)
            count+=1
            if all[k]['type']=='directory':
                self.rmdir(k)
            else:
                self.rmfile(k)
        self.rmdir(path)

    def exists(self, path):
        # Return True if this path (dir/file) exists
        return bool(self.statfile(path))

    def isdir(self, path):
        # Return True if path refers to an existing dir
        if not self.statfile(path):
            # if it doesn't exist, bail
            return False
        # just try a list dirs command and see if it bombs out
        req=p_brew.listdirectoriesrequest(dirname=path)
        try:
            self.sendbrewcommand(req, p_brew.listdirectoriesresponse)
        except (BrewCommandException, BrewBadPathnameException,
                BrewNoSuchDirectoryException,
                BrewAccessDeniedException):
            return False
        except:
            if __debug__:
                raise
            return False
        return True

    def isfile(self, filename):
        # return True if filename is a file
        if not self.statfile(filename):
            return False
        # if it exists and not a dir, then it must be a file!
        return not self.isdir(filename)

    def basename(self, path):
        # return the basename of the path, does not check on whether the path
        # exists.
        _dirs=[x for x in path.split('/') if x]
        if _dirs:
            return _dirs[-1]
        return ''

    def dirname(self, filename):
        # return the dir name of the filename, does not check on whether
        # the file exists.
        _dirs=[x for x in filename.split('/') if x]
        if len(_dirs)<2:
            # either / or /name
            return '/'
        return '/'.join(_dirs[:-1])

    def join(self, *args):
        # join the dir/file components and return the full path name
        return '/'.join([x.strip('/') for x in args if x])

    def listsubdirs(self, dir='', recurse=0):
        results={}
        self.log("Listing subdirs in dir: '"+dir+"'")
        self.log("X recurse="+`recurse`)

        req=p_brew.listdirectoryrequest()
        req.dirname=dir
        for i in xrange(10000):
            try:
                req.entrynumber=i
                res=self.sendbrewcommand(req,p_brew.listdirectoryresponse)
                # sometimes subdir can already include the parent directory
                f=res.subdir.rfind("/")
                if f>=0:
                    subdir=res.subdir[f+1:]
                else:
                    subdir=res.subdir
                if len(dir):
                    subdir=dir+"/"+subdir
                self.log("subdir="+subdir)
                results[subdir]={ 'name': subdir, 'type': 'directory' }
            except BrewNoMoreEntriesException:
                break
            except (BrewBadPathnameException, BrewAccessDeniedException):
                self.log('Failed to list dir '+dir)
                return {}
        if recurse:
            for k,_subdir in results.items():
                results.update(self.listsubdirs(_subdir['name'], recurse-1))
        return results

    def hassubdirs(self, dir=''):
        self.log('Checking for subdirs in dir: "'+dir+'"')
        req=p_brew.listdirectoryrequest()
        req.dirname=dir
        req.entrynumber=0
        try:
            res=self.sendbrewcommand(req,p_brew.listdirectoryresponse)
            # there's at least one subdir
            return True
        except BrewNoMoreEntriesException:
            return False
        except:
            if __debug__:
                raise
            return False

    def listfiles(self, dir=''):
        results={}
        self.log("Listing files in dir: '"+dir+"'")

        _broken_date=hasattr(self.protocolclass, 'broken_filelist_date') and \
                      self.protocolclass.broken_filelist_date
        req=p_brew.listfilerequest()
        req.dirname=dir
        # self.log("file listing 0x0b command")
        for i in xrange(10000):
            try:
                req.entrynumber=i
                res=self.sendbrewcommand(req,p_brew.listfileresponse)
                results[res.filename]={ 'name': res.filename, 'type': 'file',
                                        'size': res.size }
                if not _broken_date:
                    if res.date<=0:
                        results[res.filename]['date']=(0, "")
                    else:
                        try:
                            date=res.date+self._brewepochtounix
                            results[res.filename]['date']=(date, time.strftime("%x %X", time.localtime(date)))
                        except:
                            # invalid date - see SF bug #833517
                            results[res.filename]['date']=(0, "")
            except BrewNoMoreEntriesException:
                break
            except (BrewBadPathnameException, BrewAccessDeniedException):
                self.log('Failed to list files in dir '+dir)
                return {}
        if _broken_date:
            for _key,_entry in results.items():
                _stat=self.statfile(_key)
                if _stat:
                    _entry['date']=_stat.get('date', (0, ''))
                else:
                    _entry['date']=(0, '')
        return results

    def getfilesystem(self, dir="", recurse=0):
        self.log("Getting file system in dir '"+dir+"'")
        results=self.listsubdirs(dir)
        subdir_list=[x['name'] for k,x in results.items()]
        results.update(self.listfiles(dir))
        if recurse:
            for _subdir in subdir_list:
                results.update(self.getfilesystem(_subdir, recurse-1))
        return results

    def statfile(self, name):
        # return the status of the file
        try:
            self.log('stat file '+name)
            req=p_brew.statfilerequest()
            req.filename=name
            res=self.sendbrewcommand(req, p_brew.statfileresponse)
            results={ 'name': name, 'type': 'file', 'size': res.size,
                      'datevalue': res.date }
            if res.date<=0:
                results['date']=(0, '')
            else:
                try:
                    date=res.date+self._brewepochtounix
                    results['date']=(date, time.strftime("%x %X", time.localtime(date)))
                except:
                    # invalid date - see SF bug #833517
                    results['date']=(0, '')
            return results
        except (BrewCommandException, BrewNoSuchFileException):
            # File does not exist, bail
            return None
        except:
            # something happened, we don't have any info on this file
            if __debug__:
                raise
            return None

    def setfileattr(self, filename, date):
        # sets the date and time of the file on the phone
        self.log('set file date '+filename +`date`)
        req=p_brew.setfileattrrequest()
        # convert date to GPS time
        req.date=date-self._brewepochtounix
        req.filename=filename
        self.sendbrewcommand(req, p_brew.setfileattrresponse)

    def writefile(self, name, contents):
        start=time.time()
        self.log("Writing file '"+name+"' bytes "+`len(contents)`)
        desc="Writing "+name
        req=p_brew.writefilerequest()
        req.filesize=len(contents)
        req.data=contents[:0x100]
        req.filename=name
        self.sendbrewcommand(req, p_brew.writefileresponse)
        # do remaining blocks
        numblocks=len(contents)/0x100
        count=0
        for offset in range(0x100, len(contents), 0x100):
            req=p_brew.writefileblockrequest()
            count+=1
            if count>=0x100: count=1
            if count % 5==0:
                self.progress(offset>>8,numblocks,desc)
            req.blockcounter=count
            req.thereismore=offset+0x100<len(contents)
            block=contents[offset:]
            l=min(len(block), 0x100)
            block=block[:l]
            req.data=block
            self.sendbrewcommand(req, p_brew.writefileblockresponse)
        end=time.time()
        if end-start>3:
            self.log("Wrote "+`len(contents)`+" bytes at "+`int(len(contents)/(end-start))`+" bytes/second")


    def getfilecontents(self, file, use_cache=False):
        if use_cache:
            node=self.statfile(file)
            if node and file_cache.hit(file, node['date'][0], node['size']):
                self.log('Reading from cache: '+file)
                _data=file_cache.data(file)
                if _data:
                    return _data
                self.log('Cache file corrupted and discarded')

        start=time.time()
        self.log("Getting file contents '"+file+"'")
        desc="Reading "+file

        data=cStringIO.StringIO()

        req=p_brew.readfilerequest()
        req.filename=file
        
        res=self.sendbrewcommand(req, p_brew.readfileresponse)
    
        filesize=res.filesize
        data.write(res.data)

        counter=0
        while res.thereismore:
            counter+=1
            if counter>0xff:
                counter=0x01
            if counter%5==0:
                self.progress(data.tell(), filesize, desc)
            req=p_brew.readfileblockrequest()
            req.blockcounter=counter
            res=self.sendbrewcommand(req, p_brew.readfileblockresponse)
            data.write(res.data)

        self.progress(1,1,desc)
        
        data=data.getvalue()

        # give the download speed if we got a non-trivial amount of data
        end=time.time()
        if end-start>3:
            self.log("Read "+`filesize`+" bytes at "+`int(filesize/(end-start))`+" bytes/second")
        
        if filesize!=len(data):
            self.log("expected size "+`filesize`+"  actual "+`len(data)`)
            self.raisecommsexception("Brew file read is incorrect size", common.CommsDataCorruption)
        if use_cache and node:
            file_cache.add(file, node.get('date', [0])[0], data)
        return data

    DirCache=_DirCache

    def _setmodebrew(self):
        req=p_brew.memoryconfigrequest()
        respc=p_brew.memoryconfigresponse
        try:
            self.sendbrewcommand(req, respc, callsetmode=False)
            return True
        except modeignoreerrortypes:
            pass
        
        for baud in 0, 38400,115200:
            if baud:
                if not self.comm.setbaudrate(baud):
                    continue
            try:
                self.sendbrewcommand(req, respc, callsetmode=False)
                return True
            except modeignoreerrortypes:
                pass

        # send AT$CDMG at various speeds
        for baud in (0, 115200, 19200, 230400):
            if baud:
                if not self.comm.setbaudrate(baud):
                    continue
            print "Baud="+`baud`

            try:
                for line in self.comm.sendatcommand("+GMM"):
                    if line.find("SPH-A700")>0:
                        raise BrewNotSupported("This phone is not supported by BitPim", self.desc)
            except modeignoreerrortypes:
                self.log("No response to AT+GMM")
            except:
                print "GMM Exception"
                self.mode=self.MODENONE
                self.comm.shouldloop=True
                raise

            try:
                self.comm.write("AT$QCDMG\r\n")
            except:
                # some issue during writing such as user pulling cable out
                self.mode=self.MODENONE
                self.comm.shouldloop=True
                raise
            try:
                # if we got OK back then it was success
                if self.comm.readsome().find("OK")>=0:
                    break
            except modeignoreerrortypes:
                self.log("No response to setting QCDMG mode")

        # verify if we are in DM mode
        for baud in 0,38400,115200:
            if baud:
                if not self.comm.setbaudrate(baud):
                    continue
            try:
                self.sendbrewcommand(req, respc, callsetmode=False)
                return True
            except modeignoreerrortypes:
                pass
        return False

    def sendbrewcommand(self, request, responseclass, callsetmode=True):
        if callsetmode:
            self.setmode(self.MODEBREW)
        buffer=prototypes.buffer()
        request.writetobuffer(buffer, logtitle="sendbrewcommand")
        data=buffer.getvalue()
        data=common.pppescape(data+common.crcs(data))+common.pppterminator
        firsttwo=data[:2]
        try:
            # we logged above, and below
            data=self.comm.writethenreaduntil(data, False, common.pppterminator, logreaduntilsuccess=False) 
        except modeignoreerrortypes:
            self.mode=self.MODENONE
            self.raisecommsdnaexception("manipulating the filesystem")
        self.comm.success=True
        origdata=data
        
        # sometimes there is junk at the begining, eg if the user
        # turned off the phone and back on again.  So if there is more
        # than one 7e in the escaped data we should start after the
        # second to last one
        d=data.rfind(common.pppterminator,0,-1)
        if d>=0:
            self.log("Multiple packets in data - taking last one starting at "+`d+1`)
            self.logdata("Original data", origdata, None)
            data=data[d+1:]

        # turn it back to normal
        data=common.pppunescape(data)

        # take off crc and terminator
        crc=data[-3:-1]
        data=data[:-3]
        # check the CRC at this point to see if we might have crap at the beginning
        calccrc=common.crcs(data)
        if calccrc!=crc:
            # sometimes there is other crap at the begining
            d=data.find(firsttwo)
            if d>0:
                self.log("Junk at begining of packet, data at "+`d`)
                self.logdata("Original data", origdata, None)
                self.logdata("Working on data", data, None)
                data=data[d:]
                # recalculate CRC without the crap
                calccrc=common.crcs(data)
            # see if the crc matches now
            if calccrc!=crc:
                self.logdata("Original data", origdata, None)
                self.logdata("Working on data", data, None)
                raise common.CommsDataCorruption("Brew packet failed CRC check", self.desc)
        
        # log it
        self.logdata("brew response", data, responseclass)

        if firsttwo=="Y\x0c" and data==firsttwo:
            # we are getting an echo - the modem port has been selected
            # instead of diagnostics port
            raise common.CommsWrongPort("The port you are using is echoing data back, and is not valid for Brew data.  Most likely you have selected the modem interface when you should be using the diagnostic interface.", self.desc)

        # look for errors
        if data[0]=="Y" and data[2]!="\x00":  # Y is 0x59 which is brew command prefix
                err=ord(data[2])
                if err==0x1c:
                    raise BrewNoMoreEntriesException()
                if err==0x08:
                    raise BrewNoSuchDirectoryException()
                if err==0x06:
                    raise BrewNoSuchFileException()
                if err==0x1a:
                    raise BrewBadPathnameException()
                if err==0x0b:
                    raise BrewFileLockedException()
                if err==0x0d:
                    raise BrewNameTooLongException()
                if err==0x07:
                    raise BrewDirectoryExistsException()
                if err==0x04:
                    raise BrewAccessDeniedException()
                if err==0x16:
                    raise BrewFileSystemFullException()
                raise BrewCommandException(err)
        # Starting with the vx8100/9800 verizon started to block access to some file and directories
        # it reports a bad command packet as the error when it really means access denied
        if ord(data[0])==0x13:
            if firsttwo[0]=="Y" or firsttwo[0]=="\x4b": # brew command
                raise BrewAccessDeniedException()
            else:
                raise BrewBadBrewCommandException()
        if ord(data[0])==0x14:
            raise BrewMalformedBrewCommandException()

        # access denied error
        if ord(data[0])==0x4b and ord(data[2])==0x1c:
            raise BrewAccessDeniedException()

        # parse data
        buffer=prototypes.buffer(data)
        res=responseclass()
        try:
            res.readfrombuffer(buffer, autolog=False)
        except:
            # we had an exception so log the data even if protocol log
            # view is not available
            self.log(formatpacketerrorlog("Error decoding response", origdata, data, responseclass))
            raise
        return res

class RealBrewProtocol2(RealBrewProtocol):
    """Talk to a phone using the 'brew' protocol
    This class uses the new filesystem commands which are supported
    by newer qualcomm chipsets used in phones like the LG vx8100
    """

    def exists(self, name):
        try:
            self.statfile(name)
        except BrewNoSuchFileException:
            return False
        return True

    def reconfig_directory(self):
        # not sure how important this is or even what it really does
        # but the product that was reverse engineered from sent this after 
        # rmdir and mkdir, although it seems to work without it on the 8100
        req=p_brew.new_reconfigfilesystemrequest()
        self.sendbrewcommand(req, p_brew.new_reconfigfilesystemresponse)

    def rmfile(self,name):
        self.log("Deleting file '"+name+"'")
        if self.exists(name):
            req=p_brew.new_rmfilerequest()
            req.filename=name
            self.sendbrewcommand(req, p_brew.new_rmfileresponse)
        file_cache.clear(name)

    def rmdir(self,name):
        self.log("Deleting directory '"+name+"'")
        if self.exists(name):
            req=p_brew.new_rmdirrequest()
            req.dirname=name
            self.sendbrewcommand(req, p_brew.new_rmdirresponse)
            self.reconfig_directory()

    def mkdir(self, name):
        self.log("Making directory '"+name+"'")
        if self.exists(name):
            raise BrewDirectoryExistsException
        req=p_brew.new_mkdirrequest()
        req.dirname=name
        self.sendbrewcommand(req, p_brew.new_mkdirresponse)
        self.reconfig_directory()

    def openfile(self, name, mode, flags=p_brew.new_fileopen_flag_existing):
        self.log("Open file '"+name+"'")
        req=p_brew.new_openfilerequest(filename=name, mode=mode,
                                       flags=flags)
        res=self.sendbrewcommand(req, p_brew.new_openfileresponse)
        return res.handle

    def closefile(self, handle):
        self.log("Close file")
        req=p_brew.new_closefilerequest(handle=handle)
        self.sendbrewcommand(req, p_brew.new_closefileresponse)

    def writefile(self, name, contents):
        start=time.time()
        self.log("Writing file '"+name+"' bytes "+`len(contents)`)
        desc="Writing "+name
        size=len(contents)       
        exists=self.exists(name)
        if exists:
            info=self.statfile(name)
            current_size=info['size']
        else:
            current_size=0
        try:
            block_size = self.protocolclass.BREW_WRITE_SIZE
        except AttributeError:
            block_size = p_brew.BREW_WRITE_SIZE
        # if the current file is longer than the new one we have to 
        # delete it because the write operation does not truncate it
        if exists and size<current_size:
            self.rmfile(name)
            exists=False
        if exists:
            handle=self.openfile(name, p_brew.new_fileopen_mode_write, p_brew.new_fileopen_flag_existing)
        else:
            handle=self.openfile(name, p_brew.new_fileopen_mode_write, p_brew.new_fileopen_flag_create)
        try:
            remain=size
            pos=0
            count=0
            while remain:
                req=p_brew.new_writefilerequest()
                req.handle=handle
                if remain > block_size:
                    req.bytes=block_size
                else:
                    req.bytes=remain
                req.position=size-remain
                req.data=contents[req.position:(req.position+req.bytes)]
                count=(count&0xff)+1
                if count % 5==0:
                    self.progress(req.position,size,desc)
                res=self.sendbrewcommand(req, p_brew.new_writefileresponse)
                if res.bytes!=req.bytes:
                    self.raisecommsexception("Brew file write error", common.CommsDataCorruption)
                remain-=req.bytes
        finally: # MUST close handle to file
            self.closefile(handle)
        self.progress(1,1,desc)
        end=time.time()
        if end-start>3:
            self.log("Wrote "+`len(contents)`+" bytes at "+`int(len(contents)/(end-start))`+" bytes/second")

    def getfilecontents(self, file, use_cache=False):
        node=self.statfile(file)
        if use_cache:
            if node and file_cache.hit(file, node['date'][0], node['size']):
                self.log('Reading from cache: '+file)
                _data=file_cache.data(file)
                if _data:
                    return _data
                self.log('Cache file corrupted and discarded')
        try:
            block_size = self.protocolclass.BREW_READ_SIZE
        except AttributeError:
            block_size = p_brew.BREW_READ_SIZE
        start=time.time()
        self.log("Getting file contents '"+file+"'")
        desc="Reading "+file
        data=cStringIO.StringIO()
        handle=self.openfile(file, p_brew.new_fileopen_mode_read)
        try:
            filesize=node['size']
            read=0
            counter=0
            req=p_brew.new_readfilerequest(handle=handle, bytes=block_size)
            while True:
                counter=(counter&0xff)+1
                if counter%5==0:
                    self.progress(data.tell(), filesize, desc)
                req.position=read
                res=self.sendbrewcommand(req, p_brew.new_readfileresponse)
                if res.bytes:
                    data.write(res.data)
                    read+=res.bytes
                else:
                    break
                if read==filesize:
                    break
        finally: # MUST close handle to file
            self.closefile(handle)
        self.progress(1,1,desc)
        data=data.getvalue()
        # give the download speed if we got a non-trivial amount of data
        end=time.time()
        if end-start>3:
            self.log("Read "+`filesize`+" bytes at "+`int(filesize/(end-start))`+" bytes/second")
        if filesize!=len(data):
            self.log("expected size "+`filesize`+"  actual "+`len(data)`)
            self.raisecommsexception("Brew file read is incorrect size", common.CommsDataCorruption)
        if use_cache and node:
            file_cache.add(file, node.get('date', [0])[0], data)
        return data

    def getfilecontents2(self, filename, start, size):
        # read and return data a block of data from the specified file
        try:
            block_size = self.protocolclass.BREW_READ_SIZE
        except AttributeError:
            block_size = p_brew.BREW_READ_SIZE
        self.log("Getting file contents2 '"+filename+"'")
        desc="Reading "+filename
        data=cStringIO.StringIO()
        handle=self.openfile(filename, p_brew.new_fileopen_mode_read)
        _readsize=start+size
        try:
            read=start
            counter=0
            while True:
                counter+=1
                if counter%5==0:
                    self.progress(read, _readsize, desc)
                req=p_brew.new_readfilerequest()
                req.handle=handle
                req.bytes=block_size
                req.position=read
                res=self.sendbrewcommand(req, p_brew.new_readfileresponse)
                if res.bytes:
                    data.write(res.data)
                    read+=res.bytes
                else:
                    break
                if read>=_readsize:
                    break
        finally: # MUST close handle to file
            self.closefile(handle)
        self.progress(1,1,desc)
        return data.getvalue()[:size]

    def _get_dir_handle(self, dirname):
        # return the handle to the specified dir
        req=p_brew.new_opendirectoryrequest(dirname=dirname if dirname else "/")
        res=self.sendbrewcommand(req, p_brew.new_opendirectoryresponse)
        if res.handle:
            return res.handle
        # dir does not exist
        raise BrewNoSuchDirectoryException

    def _close_dir(self, handle):
        req=p_brew.new_closedirectoryrequest(handle=handle)
        res=self.sendbrewcommand(req, p_brew.new_closedirectoryresponse)

    def listsubdirs(self, dir='', recurse=0):
        self.log("Listing subdirs in dir: '"+dir+"'")
        self.log("X recurse="+`recurse`)
        return self.getfilesystem(dir, recurse, files=0)

    def listfiles(self, dir=''):
        self.log("Listing files in dir: '"+dir+"'")
        return self.getfilesystem(dir, recurse=0, directories=0)

    def getfilesystem(self, dir="", recurse=0, directories=1, files=1):
        results={}
        self.log("Listing dir '"+dir+"'")
        handle=self._get_dir_handle(dir)
        dirs={}
        count=0
        try:
            # get all the directory entries from the phone
            req=p_brew.new_listentryrequest(handle=handle)
            for i in xrange(1, 10000):
                req.entrynumber=i
                res=self.sendbrewcommand(req, p_brew.new_listentryresponse)
                if len(res.entryname) == 0: # signifies end of list
                    break
                if len(dir):
                    direntry=dir+"/"+res.entryname
                else:
                    direntry=res.entryname
                if files and (res.type==0 or res.type == 0x0f): # file or special file
                    results[direntry]={ 'name': direntry, 'type': 'file', 'size': res.size, 'special': res.type==0xf }
                    try:
                        if res.date<=0:
                            results[direntry]['date']=(0, "")
                        else:
                            results[direntry]['date']=(res.date, time.strftime("%x %X", time.localtime(res.date)))
                    except:
                        results[direntry]['date']=(0, "")
                elif directories and (res.type and res.type != 0x0f): # directory
                    results[direntry]={ 'name': direntry, 'type': 'directory' }
                    if recurse>0:
                        dirs[count]=direntry
                        count+=1
        finally: # we MUST close the handle regardless or we wont be able to list the filesystem
            # reliably again without rebooting it
            self._close_dir(handle)
        # recurse the subdirectories
        for i in range(count):
            results.update(self.getfilesystem(dirs[i], recurse-1))
        return results

    def statfile(self, name):
        # return the status of the file
        self.log('stat file '+name)
        req=p_brew.new_statfilerequest()
        req.filename=name
        res=self.sendbrewcommand(req, p_brew.new_statfileresponse)
        if res.error==2:    # ENOENT
            raise BrewNoSuchFileException
        elif res.error==0x13: # ENODEV
            # locked system file. example: /dev.null
            raise BrewFileLockedException
        elif res.error != 0:
            raise BrewStatFileException(res.error, name)
##        if res.error==2 or res.error==0x13 or res.error!=0:
##            return None
        if res.type==1 or res.type==0x86:
            # files on external media have type 0x86
            results={ 'name': name, 'type': 'file', 'size': res.size }
        else:
            results={ 'name': name, 'type': 'directory' }
        try:
            if res.created_date<=0:
                results['date']=(0, '')
            else:
                results['date']=(res.created_date, time.strftime("%x %X", time.localtime(res.created_date)))
        except:
            # the date value got screwed up, just ignore it.
            results['date']=(0, '')
        return results

phone_path=os.environ.get('PHONE_FS', None)
if __debug__ and phone_path:
    DebugBrewProtocol._fs_path=os.path.normpath(phone_path)
    BrewProtocol=DebugBrewProtocol
else:
    BrewProtocol=RealBrewProtocol
del phone_path

def formatpacketerrorlog(str, origdata, data, klass):
    # copied from guiwidgets.LogWindow.logdata
    hd=""
    if data is not None:
        hd="Data - "+`len(data)`+" bytes\n"
        if klass is not None:
            try:
                hd+="<#! %s.%s !#>\n" % (klass.__module__, klass.__name__)
            except:
                klass=klass.__class__
                hd+="<#! %s.%s !#>\n" % (klass.__module__, klass.__name__)
        hd+=common.datatohexstring(data)
    if origdata is not None:
        hd+="\nOriginal Data - "+`len(data)`+" bytes\n"+common.datatohexstring(origdata)
    return str+" "+hd

def brewbasename(str):
    "returns basename of str"
    if str.rfind("/")>0:
        return str[str.rfind("/")+1:]
    return str

def brewdirname(str):
    "returns dirname of str"
    if str.rfind("/")>0:
        return str[:str.rfind("/")]
    return str


class SPURIOUSZERO(prototypes.BaseProtogenClass):
    """This is a special class used to consume the spurious zero in some p_brew.listfileresponse

    The three bytes are formatted as follows:

       - An optional 'null' byte (this class)
       - A byte specifying how long the directory name portion is, including trailing slash
       - A byte specifying the length of the whole name
       - The bytes of the filename (which includes the full directory name)

    Fun and games ensue because files in the root directory have a zero length directory
    name, so we have some heuristics to try and distinguish if the first byte is the
    spurious zero or not

    Also allow for zero length filenames.
    
    """
    def __init__(self, *args, **kwargs):
        super(SPURIOUSZERO,self).__init__(*args, **kwargs)
        
        self._value=None
        if self._ismostderived(SPURIOUSZERO):
            self._update(args, kwargs)

    def _update(self, args, kwargs):
        super(SPURIOUSZERO, self)._update(args, kwargs)
        
        self._complainaboutunusedargs(SPURIOUSZERO, kwargs)

        if len(args):
            raise TypeError("Unexpected arguments "+`args`)

    def readfrombuffer(self, buf):
         self._bufferstartoffset=buf.getcurrentoffset()

         # there are several cases this code has to deal with
         #
         # The data is ordered like this:
         #
         # optional spurious zero (sz)
         # dirlen
         # fulllen
         # name
         #
         # These are the various possibilities.  The first two
         # are a file in the root directory (dirlen=0), with the other
         # two being a file in a subdirectory  (dirlen>0). fulllen
         # is always >0
         #
         # A:    dirlen=0 fulllen name
         # B: sz dirlen=0 fulllen name
         # C:    dirlen>0 fulllen name
         # D: sz dirlen>0 fulllen name

         while True:  # this is just used so we can break easily

             # CASE C
             if buf.peeknextbyte()!=0:
                 self._value=-1
                 break

             # CASE B
             if buf.peeknextbyte(1)==0:
                 # If the filename is empty, we should see two zeros
                 if buf.howmuchmore()==2:
                     break
                 self._value=buf.getnextbyte() # consume sz
                 break
             
             # A & D are harder to distinguish since they both consist of a zero
             # followed by non-zero.  Consequently we examine the data for
             # consistency

             all=buf.peeknextbytes(min(max(2+buf.peeknextbyte(1), 3+buf.peeknextbyte(2)), buf.howmuchmore()))

             # are the values consistent for D?
             ddirlen=ord(all[1])
             dfulllen=ord(all[2])

             if ddirlen<dfulllen and ddirlen<len(all)-3 and all[3+ddirlen-1]=='/':
                 self._value=buf.getnextbyte() # consume sz
                 break

             # case C, do nothing
             self._value=-2
             break
             
         self._bufferendoffset=buf.getcurrentoffset()

class EXTRAZERO(prototypes.BaseProtogenClass):
    """This is a special class used to consume the spurious zero in some p_brew.listfileresponse or p_brew.listdirectoryresponse

    The two bytes are formatted as follows:

       - An optional 'null' byte (this class)
       - A byte specifying the length of the whole name
       - The bytes of the filename (which includes the full directory name)

    Allow for zero length filenames.
    
    """
    def __init__(self, *args, **kwargs):
        super(EXTRAZERO,self).__init__(*args, **kwargs)
        
        self._value=None
        if self._ismostderived(EXTRAZERO):
            self._update(args, kwargs)

    def _update(self, args, kwargs):
        super(EXTRAZERO, self)._update(args, kwargs)
        
        self._complainaboutunusedargs(EXTRAZERO, kwargs)

        if len(args):
            raise TypeError("Unexpected arguments "+`args`)

    def readfrombuffer(self, buf):
         self._bufferstartoffset=buf.getcurrentoffset()

         # there are several cases this code has to deal with
         #
         # The data is ordered like this:
         #
         # optional spurious zero (sz)
         # fulllen
         # name
         #
         # These are the various possibilities.  The first two
         # are a file in the root directory (dirlen=0), with the other
         # two being a file in a subdirectory  (dirlen>0). fulllen
         # is always >0
         #
         # A:    fulllen=0
         # B: ez fulllen=0
         # C:    fulllen>0 name
         # D: ez fulllen>0 name

         while True:  # this is just used so we can break easily

             # CASE C
             if buf.peeknextbyte()!=0:
                 self._value=-1
                 break
             
             # CASE A
             if buf.howmuchmore()==1:
                 self._value=-1
                 break # Really a zero length file

             # CASE B or D
             self._value=buf.getnextbyte() # consume sz

             break
             
         self._bufferendoffset=buf.getcurrentoffset()

    def writetobuffer(self, buf):
        raise NotImplementedError()

    def packetsize(self):
         raise NotImplementedError()

    def getvalue(self):
        "Returns the string we are"

        if self._value is None:
            raise prototypes.ValueNotSetException()
        return self._value

file_cache=None

class EmptyFileCache(object):
    def __init__(self, bitpim_path):
        self._path=None
        self._cache_file_name=None
        self._data={ 'file_index': 0 }
        self.esn=None
    def hit(self, file_name, datetime, data_len):
        return False
    def data(self, file_name):
        return None
    def add(self, file_name, datetime, data):
        pass
    def clear(self, file_name):
        pass
    def set_path(self, bitpim_path):
        try:
            print 'setting path to',`bitpim_path`
            if not bitpim_path:
                raise ValueError
            # set the paths
            self.__class__=FileCache
            self._path=os.path.join(bitpim_path, 'cache')
            self._cache_file_name=os.path.join(self._path,
                                               self._cache_index_file_name)
            self._check_path()
            self._read_index()
            self._write_index()
        except:
            self.__class__=EmptyFileCache

class FileCache(object):
    _cache_index_file_name='index.idx'
    current_version=1
    def __init__(self, bitpim_path):
        self._path=os.path.join(bitpim_path, 'cache')
        self._cache_file_name=os.path.join(self._path,
                                           self._cache_index_file_name)
        self._data={ 'file_index': 0 }
        self.esn=None
        try:
            if not bitpim_path:
                raise ValueError
            self._check_path()
            self._read_index()
            self._write_index()
        except:
            # something's wrong, disable caching
            self.__class__=EmptyFileCache

    def _check_path(self):
        try:
            os.makedirs(self._path)
        except:
            pass
        if not os.path.isdir(self._path):
            raise Exception("Bad cache directory: '"+self._path+"'")

    def _read_index(self):
        self._check_path()
        d={ 'result': {} }
        try:
            common.readversionedindexfile(self._cache_file_name, d, None,
                                          self.current_version)
            self._data.update(d['result'])
        except:
            print 'failed to read cache index file'

    def _write_index(self):
        self._check_path()
        common.writeversionindexfile(self._cache_file_name, self._data,
                                     self.current_version)

    def _entry(self, file_name):
        k=self._data.get(self.esn, None)
        if k:
            return k.get(file_name, None)

    def hit(self, file_name, datetime, data_len):
        try:
            e=self._entry(file_name)
            if e:
                return e['datetime']==datetime and \
                       e['size']==data_len
            return False
        except:
            if __debug__:
                raise
            return False

    def data(self, file_name):
        try:
            e=self._entry(file_name)
            if e:
                _data=file(os.path.join(self._path, e['cache']), 'rb').read()
                if len(_data)==e['size']:
                    return _data
        except IOError:
            return None
        except:
            if __debug__:
                raise
            return None

    def add(self, file_name, datetime, data):
        try:
            if self.esn:
                e=self._entry(file_name)
                if not e:
                    # entry does not exist, create a new one
                    self._data.setdefault(self.esn, {})[file_name]={}
                    e=self._data[self.esn][file_name]
                    e['cache']='F%05d'%self._data['file_index']
                    self._data['file_index']+=1
                # entry exists, just update the data
                e['datetime']=datetime
                e['size']=len(data)
                _cache_file_name=os.path.join(self._path, e['cache'])
                try:
                    file(_cache_file_name, 'wb').write(data)
                    self._write_index()
                except IOError:
                    # failed to write to cache file, drop this entry
                    self._read_index()
        except:
            if __debug__:
                raise

    def clear(self, file_name):
        try:
            # clear this entry if it exists
            e=self._entry(file_name)
            if e:
                try:
                    # remove the cache file
                    os.remove(os.path.join(self._path, e['cache']))
                except:
                    pass
                # and remove the entry
                del self._data[self.esn][file_name]
                self._write_index()
        except:
            if __debug__:
                raise

    def set_path(self, bitpim_path):
        try:
            if not bitpim_path:
                raise ValueError
            # set the paths
            self.__class__=FileCache
            self._path=os.path.join(bitpim_path, 'cache')
            self._cache_file_name=os.path.join(self._path,
                                               self._cache_index_file_name)
            self._check_path()
            self._read_index()
            self._write_index()
        except:
            self.__class__=EmptyFileCache
