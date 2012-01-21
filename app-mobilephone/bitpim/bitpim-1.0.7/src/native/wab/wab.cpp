#include <windows.h>
#include <wab.h>
#include <stdio.h>
#include <stdarg.h>

#include "pywab.h"

char *errorstring=NULL;
ULONG errorcode=0;

static HMODULE themodule;

static void errorme(HRESULT hr, const char *format, ...)
{
  va_list arglist;
  va_start(arglist, format);
  char *tmp=(char*)malloc(4096);
  vsnprintf(tmp, 4096, format, arglist);
  va_end(arglist);

  LPSTR sysmsg=NULL;
  errorcode=hr;
  FormatMessage(FORMAT_MESSAGE_ALLOCATE_BUFFER | 
		FORMAT_MESSAGE_FROM_SYSTEM | 
		FORMAT_MESSAGE_IGNORE_INSERTS,
		NULL,
		GetLastError(),
		MAKELANGID(LANG_NEUTRAL, SUBLANG_DEFAULT),
		(LPSTR)&sysmsg,
		0,
		NULL );

  if (!errorstring)
    errorstring=(char*)malloc(16384);

  snprintf(errorstring, 16384, "%s: HResult: %lu  System message %s", tmp, hr, sysmsg?sysmsg:"<NULL>");
  free(tmp);
  LocalFree(sysmsg);
}

wabmodule::~wabmodule()
{
  if(refcount->Release())
    {
      addrbook->Release();
      wabobject->Release();  
      FreeLibrary(hModule);
      delete refcount;
      refcount=0;
    }
}

wabmodule::wabmodule(const wabmodule &rhs) :
  hModule(rhs.hModule), openfn(rhs.openfn), addrbook(rhs.addrbook),
  wabobject(rhs.wabobject), refcount(rhs.refcount)
{
  refcount->AddRef();
}

wabmodule* Initialize(bool enableprofiles, const char *filename)
{
  HMODULE hModule=0;
  LPWABOPEN openfn=0;
  LPADRBOOK lpaddrbook=0;
  LPWABOBJECT lpwabobject=0;

  TCHAR  szWABDllPath[MAX_PATH];
  const TCHAR* loadeddllname=NULL;
  {
    DWORD  dwType = 0;
    ULONG  cbData = sizeof(szWABDllPath);
    HKEY hKey = NULL;
    
    *szWABDllPath = '\0';
    
    // First we look under the default WAB DLL path location in the
    // Registry. 
    // WAB_DLL_PATH_KEY is defined in wabapi.h
    //
    if (ERROR_SUCCESS == RegOpenKeyEx(HKEY_LOCAL_MACHINE, WAB_DLL_PATH_KEY, 0, KEY_READ, &hKey))
      RegQueryValueEx( hKey, "", NULL, &dwType, (LPBYTE) szWABDllPath, &cbData);
    
    if(hKey) RegCloseKey(hKey);
    
    // if the Registry came up blank, we do a loadlibrary on the wab32.dll
    // WAB_DLL_NAME is defined in wabapi.h
    //
    loadeddllname=(lstrlen(szWABDllPath)) ? szWABDllPath : WAB_DLL_NAME;
    hModule = LoadLibrary(loadeddllname);
    if(!hModule)
      {
	errorme(0, "Failed to load WAB library %s", loadeddllname);
	return NULL;
      }
    themodule=hModule;
  }

  // get the entry point 
  //
  openfn = (LPWABOPEN) GetProcAddress(hModule, "WABOpen");
  if(!openfn)
    {
      errorme(0, "Failed to find function WABOpen in dll %s", loadeddllname);
      FreeLibrary(hModule);
    }
	
  // open the file
  {
    WAB_PARAM wp={0};
    wp.cbSize=sizeof(WAB_PARAM);
    if (!filename) filename="";
    wp.szFileName=(TCHAR*)filename;
    if(enableprofiles)
      wp.ulFlags=WAB_ENABLE_PROFILES;

    HRESULT hr=openfn(&lpaddrbook, &lpwabobject, &wp, 0);
    if (HR_FAILED(hr))
    {
      errorme(hr, "Failed to open address book %s", strlen(filename)?filename:"<default>");
      FreeLibrary(hModule);
      return false;
    }
  }

  // it worked - return results
  return new wabmodule(hModule, openfn, lpaddrbook, lpwabobject);
}

void wabmodule::FreeObject(LPSRowSet rows)
{
  if (!rows) return;
  for (unsigned int row=0; row<rows->cRows; row++)
    wabobject->FreeBuffer(rows->aRow[row].lpProps);
  wabobject->FreeBuffer(rows);
}

void wabmodule::FreeObject(LPSPropTagArray pa)
{
  wabobject->FreeBuffer(pa);
}

entryid* wabmodule::getpab()
{
  ULONG cbpabeid;
  LPENTRYID pabeid;
  HRESULT hr=addrbook->GetPAB(&cbpabeid, &pabeid);
  if (HR_FAILED(hr))
    {
      errorme(hr, "Failed to get Personal Address Book entryid");
      return NULL;
    }
  entryid* eid=new entryid(pabeid, cbpabeid);
  wabobject->FreeBuffer(pabeid);
  return eid;
}

wabobject* wabmodule::openobject(const entryid& eid)
{
  ULONG objtype;
  LPUNKNOWN iface;

  HRESULT hr=addrbook->OpenEntry(eid.getlen(), eid.getdata(), NULL, MAPI_BEST_ACCESS, &objtype, &iface);
  if (HR_FAILED(hr))
    {
      errorme(hr, "Failed to openentry");
      return NULL;
    }
  
  return new class wabobject(*this, objtype, iface); // quite why 'class' has to be there, i don't know
}

wabobject::~wabobject()
{
  iface->Release();
}

wabobject::wabobject(const wabmodule& mod, ULONG t, LPUNKNOWN i)
  : iface(i), type(t), module(mod)
{
}

wabtable* wabobject::getcontentstable(unsigned long flags)
{
  if(type!=MAPI_ABCONT)
    {
      errorme(0, "Object is not a container");
      return NULL;
    }
  LPMAPITABLE table;
  HRESULT hr=((LPABCONT)iface)->GetContentsTable(flags, &table);
  if (HR_FAILED(hr))
    {
      errorme(hr, "Failed to GetContentsTable");
      return NULL;
    }
  return new wabtable(module, table);
}

wabtable::~wabtable()
{
  table->Release();
}

int wabtable::getrowcount()
{
  ULONG l;
  HRESULT hr=table->GetRowCount(0, &l);
  if (HR_FAILED(hr))
    {
      errorme(hr, "Failed to get rowcount");
      return -1;
    }
  return (int)l;
}

wabrow* wabtable::getnextrow()
{
  LPSRowSet rowset;
  HRESULT hr=table->QueryRows(1,0, &rowset);
  if (HR_FAILED(hr))
    {
      errorme(hr, "Failed to get next row");
      return NULL;
    }
  return new wabrow(module, rowset);
}

// returns true on success
bool wabtable::enableallcolumns()
{
  LPSPropTagArray props;
  HRESULT hr=table->QueryColumns(TBL_ALL_COLUMNS, &props);
  if (HR_FAILED(hr))
    {
      errorme(hr, "Failed to get list of all columns");
      return false;
    }
  hr=table->SetColumns(props, 0);
  module.FreeObject(props);
  if (HR_FAILED(hr))
    {
      errorme(hr, "Failed to turn on all columns");
      return false;
    }
  return true;
}

bool wabtable::enablecolumns(proptagarray &pta)
{
  // we do some nasty voodo here.  SPropTagArray is actually a ULONG of
  // how many members and then that many ULONGS (the underlying property
  // type) all nicely wrapped in a structure.  We just use one huge
  // array which will have the same memory layout
  HRESULT hr=table->SetColumns( (LPSPropTagArray) pta.array, 0);
  if (HR_FAILED(hr))
    {
      errorme(hr, "Failed to turn on specied %lu columns", pta.array[0]);
      return false;
    }
  return true;
}

wabrow::~wabrow()
{
  module.FreeObject(rowset);
}

bool wabrow::IsEmpty()
{
  return rowset->cRows==0;
}

// see mapitypes.h for these names and ranges

static struct { ULONG id; const char* name; }  propnames[]={
#define PR(t) { PROP_ID(t), #t }
#include "_genprops.h"
#undef PR
  { 0, NULL } };

static char*propbuffy=NULL;

const char *property_name(unsigned id)
{
  const int buflen=4096;

  unsigned i=0;
  do
    {
      if (propnames[i].id==id)
	return propnames[i].name;
      i++;
    } while (propnames[i].name);
  if(!propbuffy)
    propbuffy=(char*)malloc(buflen);

  // main categories
  if (id>=0x0001 && id<=0x0bff)
    snprintf(propbuffy, buflen, "MAPI_defined envelope property %04x", id);
  else if (id>=0x0c00 && id<=0x0dff)
    snprintf(propbuffy, buflen, "MAPI_defined per-recipient property %04x", id);
  else if (id>=0x0e00 && id<=0x0fff)
    snprintf(propbuffy, buflen, "MAPI_defined non-transmittable property %04x", id);
  else if (id>=0x1000 && id<=0x2fff)
    snprintf(propbuffy, buflen, "MAPI_defined message content property %04x", id);
  else if (id>=0x4000 && id<=0x57ff)
    snprintf(propbuffy, buflen, "Transport defined envelope property %04x", id);
  else if (id>=0x5800 && id<=0x5fff)
    snprintf(propbuffy, buflen, "Transport defined per-recipient property %04x", id);
  else if (id>=0x6000 && id<=0x65ff)
    snprintf(propbuffy, buflen, "User-defined non-transmittable property %04x", id);
  else if (id>=0x6600 && id<=0x67ff)
    snprintf(propbuffy, buflen, "Provider defined internal non-transmittable property %04x", id);
  else if (id>=0x6800 && id<=0x7bff)
    snprintf(propbuffy, buflen, "Message class-defined content property %04x", id);
  else if (id>=0x7c00 && id<=0x7fff)
    snprintf(propbuffy, buflen, "Messafe class-defined non-transmittable property %04x", id);
  else if (id>=0x8000 && id<=0xfffe)
    snprintf(propbuffy, buflen, "User defined Name-to-id property %04x", id);
  // mapi defined stuff
  else if (id>=0x3000 && id<=0x33ff)
    snprintf(propbuffy, buflen, "Common property %04x", id);
  else if (id>=0x3400 && id<=0x35ff)
    snprintf(propbuffy, buflen, "Message store object %04x", id);
  else if (id>=0x3600 && id<=0x36ff)
    snprintf(propbuffy, buflen, "Folder or AB container %04x", id);
  else if (id>=0x3700 && id<=0x38ff)
    snprintf(propbuffy, buflen, "Attachment %04x", id);
  else if (id>=0x3900 && id<=0x39ff)
    snprintf(propbuffy, buflen, "Address book %04x", id);
  else if (id>=0x3a00 && id<=0x3bff)
    snprintf(propbuffy, buflen, "Mail user %04x", id);
  else if (id>=0x3c00 && id<=0x3cff)
    snprintf(propbuffy, buflen, "Distribution list %04x", id);
  else if (id>=0x3d00 && id<=0x3dff)
    snprintf(propbuffy, buflen, "Profile section %04x", id);
  else if (id>=0x3e00 && id<=0x3fff)
    snprintf(propbuffy, buflen, "Status object %04x", id);
  else 
    snprintf(propbuffy, buflen, "NO IDEA WHAT THIS IS %04x", id);

  return propbuffy;
}


static inline unsigned numdigits(unsigned i) { 
  unsigned res=0;
  while(++res,i)
    i/=10;
  return res;
}

static char *valuebuffy=NULL;

const char *property_value(unsigned int type, const union _PV &value)
{
  const unsigned int buflen=65536;
  if (!valuebuffy)
    valuebuffy=(char*)malloc(buflen);

  if (type==PT_I2 || type==PT_SHORT)
    snprintf(valuebuffy, buflen, "int:%d", (int)value.i);
  else if (type==PT_I4 || type==PT_LONG)
    snprintf(valuebuffy, buflen, "int:%ld", value.l);
  else if (type==PT_BOOLEAN)
    snprintf(valuebuffy, buflen, "bool:%d", (int)value.b);
  else if (type==PT_STRING8)
    snprintf(valuebuffy, buflen, "string:%s", value.lpszA);
  else if (type==PT_BINARY)
    snprintf(valuebuffy, buflen, "binary:%lu,%lu", (unsigned long)value.bin.lpb, (unsigned long)value.bin.cb);
  else if (type==PT_MV_STRING8)
    {
      unsigned spaceneeded=strlen("strings:");
      for (unsigned i=0;i<value.MVszA.cValues;i++)
	  spaceneeded+=numdigits(strlen(value.MVszA.lppszA[i]))+1+strlen(value.MVszA.lppszA[i])+1;
      if (spaceneeded>buflen)
	{
	  free(valuebuffy);
	  valuebuffy=(char*)malloc(spaceneeded);
	}
      char *pos=valuebuffy;
      pos+=sprintf(valuebuffy, "strings:");
      for (unsigned i=0;i<value.MVszA.cValues;i++)
	  pos+=sprintf(pos,"%u:%s", strlen(value.MVszA.lppszA[i]), value.MVszA.lppszA[i]);
    }
  else if (type==PT_SYSTIME)
    {
      snprintf(valuebuffy, buflen, "binary:%lu,%lu", (unsigned long)&value, (unsigned long)8);
      return valuebuffy;
      SYSTEMTIME thetime={0};
      sprintf(valuebuffy, "PT_SYSTIME:%lu %lu", value.ft.dwLowDateTime, value.ft.dwHighDateTime);
      return valuebuffy;
      if (!FileTimeToSystemTime(&value.ft, &thetime))
	{
	  errorme(0, "Failed to convert filetime to systime");
	  return NULL;
	}
      sprintf(valuebuffy, "PT_SYSTIME:%d %d %d %d %d %d %d", thetime.wYear, thetime.wMonth, thetime.wDay,
	      thetime.wHour, thetime.wMinute, thetime.wSecond, thetime.wMilliseconds);

    }
#define tt(t) else if (type==t) snprintf(valuebuffy, buflen, "%s:", #t)
  tt(PT_FLOAT);
  tt(PT_R4);
  tt(PT_R8);
  tt(PT_DOUBLE);
  tt(PT_CURRENCY);
  tt(PT_APPTIME);
  tt(PT_UNICODE);
  tt(PT_CLSID);
  tt(PT_I8);
  tt(PT_LONGLONG);
  tt(PT_MV_I2);
  tt(PT_MV_LONG);
  tt(PT_MV_R4);
  tt(PT_MV_DOUBLE);
  tt(PT_MV_CURRENCY);
  tt(PT_MV_APPTIME);
  tt(PT_MV_SYSTIME);
  tt(PT_MV_BINARY);
  tt(PT_MV_UNICODE);
  tt(PT_MV_CLSID);
  tt(PT_MV_I8);
  tt(PT_ERROR);
  tt(PT_NULL);
  tt(PT_OBJECT);
#undef tt
  else snprintf(valuebuffy, buflen, "<unknown type %ux>", type);

  return valuebuffy;

}

unsigned wabrow::numproperties()
{
  if (rowset->cRows<1)
    return 0;
  return rowset->aRow[0].cValues;
}

const char* wabrow::getpropertyname(unsigned which)
{
  if (rowset->cRows<1)
    return NULL;
  SPropValue &val=rowset->aRow[0].lpProps[which];
  return property_name(PROP_ID(val.ulPropTag));
}

const char *wabrow::getpropertyvalue(unsigned which)
{
  if (rowset->cRows<1)
    return NULL;
  SPropValue &val=rowset->aRow[0].lpProps[which];
  return property_value(PROP_TYPE(val.ulPropTag), val.Value);
}

// this depends on unsigned long being big enough to hold a void pointer
entryid* wabtable::makeentryid(unsigned long pointer, unsigned long len)
{
  return new entryid((void*)pointer, len);
}

void wabtable::makebinarystring(char **result, size_t *resultlen, unsigned long pointer, unsigned long len)
{
  *result=(char*)pointer;
  *resultlen=len;
}



entryid::entryid(void *d, size_t l)
  : data(0), len(l)
{
  if(len)
    {
      data=malloc(l);
      memcpy(data, d, l);
    }
}

entryid::~entryid()
{
  if(data)
    free(data);
}
