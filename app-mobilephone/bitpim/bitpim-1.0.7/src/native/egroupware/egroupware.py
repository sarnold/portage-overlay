### BITPIM
###
### Copyright (C) 2004 Roger Binns <rogerb@rogerbinns.com>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: egroupware.py 1770 2004-11-22 06:53:49Z rogerb $

"""Be at one with eGroupware

We talk to eGroupware using its xmlrpc interface.  Unfortunately the interface
has several quality issues, so we try to work around them in this code.
"""

import xmlrpclib
import urlparse
import time
import datetime

def getsession(url, user, password, domain="default"):

    # fixup whatever the user max have given us
    scheme, location, path, query, fragment = urlparse.urlsplit(url)

    if scheme is None and location is None and query is None:
        url="http://"+url
    
    if url[-1]!="/": url+="/"
    url+="xmlrpc.php"

    sp=xmlrpclib.ServerProxy(url)

    res=sp.system.login({"username": user, "password": password, "domain": domain})

    if "sessionid" not in res or "kp3" not in res:
        raise Exception("Invalid username or password")

    scheme, location, path, query, fragment = urlparse.urlsplit(url)

    if location.find("@")>=0:
        location=location[location.find("@")+1:]

    newurl=urlparse.urlunsplit( (scheme, "%s:%s@%s" % (res["sessionid"], res["kp3"], location), path, query, fragment) )
    return Session(xmlrpclib.ServerProxy(newurl), res)

class Session:

    def __init__(self, sp, ifo):
        self.sp=sp
        self.__ifo=ifo

    def __del__(self):
        self.sp.system.logout(self.__ifo)
        self.sp=None
        self.__ifo=None

    def getyearcalendar(self, year):
        return getcalendar((year,), (year,))

    def getcalendar(self, start=(), end=()):
        if len(start)!=6 or len(end)!=6:
            t=time.localtime()
            startdefs=(t[0], 1, 1, 0,0,0)
            enddefs=(t[0],12,31,23,59,60)
            start=start+startdefs[len(start):]
            end=end+enddefs[len(end):]
        start="%04d-%02d-%02dT%02d:%02d:%02d" % start
        end="%04d-%02d-%02dT%02d:%02d:%02d" % end
        for item in self.sp.calendar.bocalendar.search({"start": start, "end": end}):
            for k in item.keys():
                if isinstance(item[k], xmlrpclib.DateTime):
                    v=str(item[k])
                    v=[int(x) for x in v[0:4], v[5:7], v[8:10], v[11:13], v[14:16], v[17:19]]
                    if v==[0,0,0,0,0,0]:
                        del item[k]
                    else:
                        item[k]=datetime.datetime(*v)
            yield item

    def doescontactexist(self, id):
        try:
            return self.sp.addressbook.boaddressbook.read({'id': id})
        except xmlrpclib.Fault, f:
            # in theory only fault 10 - Entry does not (longer) exist!
            # should be looked for.  Unfortunately egroupware has a
            # bug and returns fault 9 - Access denied if the id
            # doesn't exist.  So we consider any failure to mean
            # that the id doesn't exist.  Reported as SF bug #1057984
            print "eg contact doesn't exist, fault", f
            return False

    def getcontacts(self):
        "returns all contacts"
        # internally we read them a group at a time
        offset=0 
        limit=5

        # NB an offset of zero causes egroupware to return ALL contacts ignoring limit!
        # This has been filed as bug 1040738 at SourceForge against eGroupware.  It
        # won't hurt unless you have huge number of contacts as egroupware will try
        # to return all of them at once.  Alternatively make the simple fix as in
        # the bug report

        while True:
            contacts=self.sp.addressbook.boaddressbook.search({'start': offset, 'limit': limit})
            if len(contacts)==0:
                raise StopIteration()
            for i in contacts:
                yield i
            if len(contacts)<limit:
                raise StopIteration()
            offset+=len(contacts)

    def writecontact(self, contact):
        "Returns the id of the contact"
        # egroupware returns True if the contact was written successfully using the
        # existing id, otherwise it returns the new id
        res=self.sp.addressbook.boaddressbook.write(contact)
        if res is True:
            return contact['id']
        return res

    def getcontactspbformat(self):
        "returns contacts in a format suitable for the BitPim phonebook importer"
        # eGroupware gives a nice shine in the UI, but the underlying data is
        # somewhat messy
        for c in self.getcontacts():
            res={}
            # egroupware format is very similar to vCard
            res['Name']=c['fn']
            res['First Name']=c['n_given']
            res['Middle Name']=c['n_middle']
            res['Last Name']=c['n_family']
            res['UniqueSerial-id']=c['id']
            res['UniqueSerial-sourcetype']='egroupware'
            # addresses
            for t,prefix in ("business", "adr_one"), ("home", "adr_two"):
                a={}
                # egroupware has street 2 and 3 in the ui, but doesn't expose them
                # via xmlrpc - reported as SF bug # 1043862
                for p2,k in ("_street", "street"), ("_locality", "city"), ("_region", "state"), \
                        ("_postalcode", "postalcode"), ("_countryname", "country"):
                    if len(c.get(prefix+p2,"")): a[k]=c[prefix+p2]
                if t=="business" and len(c.get("org_name", "")): a['company']=c["org_name"]
                if len(a):
                    a['type']=t
                    aa="Address"
                    if aa in res:
                        aa+="2"
                        assert aa not in res
                    res[aa]=a
            # categories
            cats=[]
            ccats=c.get("cat_id", "")
            if len(ccats): # could be empty string or a dict
                for cat in ccats:
                    cats.append(ccats[cat])
                if len(cats):
                    res["Categories"]=cats
            # email - we ignore the silly egroupware email type field
            suf=""
            if len(c.get("email","")):
                res["Email Address"]={'email': c['email'], 'type': 'business'}
                suf="2"
            if len(c.get("email_home", "")):
                res["Email Address"+suf]={'email': c['email_home'], 'type': 'home'}
            # phone numbers
            res["Home Phone"]=c['tel_home']
            res["Mobile Phone"]=c['tel_cell'] # nb: in eGroupware this is business cell
            res["Business Fax"]=c['tel_fax']
            res["Pager"]=c['tel_pager'] # nb: in eGroupware this is business pager
            res["Business Phone"]=c['tel_work']
            # various other fields
            res['Notes']=c['note']
            res['Business Web Page']=c['url']

            # filter out empty fields
            res=dict([(k,v) for k,v in res.items() if len(v)])
            yield res

    def getcategories(self):
        "Get the list of categories"
        # egroupware returns a dict with each key being an asciized integer
        # id.  The same field is present in the dict value, so we just return
        # the values
        return [v for k,v in self.sp.addressbook.boaddressbook.categories(True).items()]
    
            
if __name__=='__main__':
    import sys
    import common
    s=getsession(*sys.argv[1:])
    for v in s.getcategories():
        print common.prettyprintdict(v)
    #for n,i in enumerate(s.getcontacts()):
    #    print n,common.prettyprintdict(i)
        
        #print n,i.get('id',""),i.get('n_given', ""),i.get('n_family', "")
    
