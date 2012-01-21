/*
 * C implementation of the Jaro Winkler string similarity algorithm.
 * See the Python file in this directory which this is a derived
 * version of.
 *
 * This file uses a nasty trick to produce two versions of the
 * function for both 8 bit chars and what Python is using for Unicode
 * (sometimes 16 bit chars, sometimes 32 bit chars).  In C++ one could
 * use templates, but this is far more fun.
 *
 */

#ifndef TEMPLATING

#include <Python.h>

/* a modified version of the standard Python bitset.h as Python
   doesn't export the symbols */
#include "bitset.h"

#define MIN(x,y) (((x)<(y))?(x):(y))

#define TEMPLATING

#define JWCHARP char*
#define CHAR    int
#define NOCHAR  -1
#define FUNCTION jarowchar

#include "jarow.c"

#undef JWCHARP
#undef CHAR
#undef NOCHAR
#undef FUNCTION

#define JWCHARP  Py_UNICODE*
#define CHAR     unsigned int
#define NOCHAR   0xffffffffu
#define FUNCTION jarowunicode

#include "jarow.c"

#undef JWCHARP
#undef CHAR
#undef NOCHAR
#undef FUNCTION

#undef TEMPLATING
#endif /* TEMPLATING */

#ifdef TEMPLATING

/* length is in chars not bytes */
static double 
FUNCTION(JWCHARP s1, unsigned lens1, JWCHARP s2, unsigned lens2, unsigned winklercommonchars)
{
  unsigned i, halflen, s1pos=0, s2pos=0, transpositions=0, commonlen=0;
  bitset s1seenins2=0, s2seenins1=0;
  CHAR s1char, s2char;
  double score=0;

  /* if either string is empty then result is always zero */
  if (lens1==0 || lens2==0)
    return 0;

  /* if the strings are identical then it is 1.0 */
  if (lens1==lens2 && 0==memcmp(s1, s2, lens1*sizeof(s1[0])))
    return 1.0;

  halflen=MIN(lens1/2+1, lens2/2+1);

  s1seenins2=newbitset(lens2);
  s2seenins1=newbitset(lens1);

#define STRBEGIN(curpos,offset) ((offset>curpos)?0:curpos-offset)
#define STREND(curpos,offset,slen) ((curpos+offset>slen)?slen:curpos+offset)

  while (s1pos<lens1 || s2pos<lens2)
    {
      /* find next common char from s1 in s2 */
      s1char=NOCHAR;
      while (s1pos<lens1)
        {
          for(i=STRBEGIN(s1pos,halflen);i<STREND(s1pos,halflen,lens2);i++)
            {
              if (testbit(s1seenins2,i))
                  continue;

              if (s1[s1pos]==s2[i])
                {
                  s1char=s2[i];
                  addbit(s1seenins2, i);
                  break;
                }
            }
          s1pos+=1;
          if (s1char!=NOCHAR)
            break;
        }
      /* find next common char from s2 in s1 */
      s2char=NOCHAR;
      while (s2pos<lens2)
        {
          for(i=STRBEGIN(s2pos,halflen);i<STREND(s2pos,halflen,lens1);i++)
            {
              if (testbit(s2seenins1,i))
                continue;
              if (s2[s2pos]==s1[i])
                {
                  s2char=s1[i];
                  addbit(s2seenins1, i);
                  break;
                }
            }
          s2pos+=1;
          if (s2char!=NOCHAR)
            break;
        }
      /* are we still matching? */
      if (s1char==NOCHAR && s2char==NOCHAR)
        break;
      if ( (s1char!=NOCHAR && s2char==NOCHAR) || (s1char==NOCHAR && s2char!=NOCHAR))
          goto finally;
      commonlen++;
      if (s1char != s2char)
        transpositions++;
    }

  if (commonlen==0)
      goto finally;

  transpositions/=2;
  score=commonlen/(double)lens1+commonlen/(double)lens2+ (commonlen-transpositions)/(double)commonlen;
  score/=3.0;

  if (winklercommonchars)
    {
      commonlen=0;
      while(commonlen<=lens1 && commonlen<=lens2 && commonlen<=winklercommonchars)
        {
          if (commonlen>=lens1 || commonlen>=lens2)
            break;
          if (s1[commonlen]!=s2[commonlen])
            break;
          commonlen++;
        }
      score+=commonlen*0.1*(1-score);
    }

 finally:
  delbitset(s1seenins2);
  delbitset(s2seenins1);
  return score;

}

#endif /* TEMPLATING */

#ifndef TEMPLATING

/* Python entry point */
static PyObject *
jarow(PyObject *self, PyObject *args)
{
  PyObject *s1, *s2;
  int winklerchars=0;
  double result;

  if(!PyArg_ParseTuple(args, "OO|i:jarow(string,string[,winklerchars=0])", &s1, &s2, &winklerchars))
    return NULL;

  if(PyString_CheckExact(s1) && PyString_CheckExact(s2))
    {
      result=jarowchar(PyString_AS_STRING(s1), PyString_GET_SIZE(s1), 
                       PyString_AS_STRING(s2), PyString_GET_SIZE(s2), 
                       winklerchars);
    }
  else if (PyUnicode_CheckExact(s1) && PyUnicode_CheckExact(s2))
    {
      result=jarowunicode(PyUnicode_AS_UNICODE(s1), PyUnicode_GET_SIZE(s1),
                          PyUnicode_AS_UNICODE(s2), PyUnicode_GET_SIZE(s2),
                          winklerchars);
    }
  else if (PyString_CheckExact(s1) && PyUnicode_CheckExact(s2))
    {
      s1=PyUnicode_FromObject(s1);
      if(!s1) return NULL;
      result=jarowunicode(PyUnicode_AS_UNICODE(s1), PyUnicode_GET_SIZE(s1),
                          PyUnicode_AS_UNICODE(s2), PyUnicode_GET_SIZE(s2),
                          winklerchars);
      Py_DECREF(s1);
    }
  else if (PyUnicode_CheckExact(s1) && PyString_CheckExact(s2))
    {
      s2=PyUnicode_FromObject(s2);
      if(!s2) return NULL;
      result=jarowunicode(PyUnicode_AS_UNICODE(s1), PyUnicode_GET_SIZE(s1),
                          PyUnicode_AS_UNICODE(s2), PyUnicode_GET_SIZE(s2),
                          winklerchars);
      Py_DECREF(s2);
    }
  else
    {
      return PyErr_Format(PyExc_TypeError, "The first two parameters must be some combination of string or unicode objects");
    }

  return PyFloat_FromDouble(result);
}

static PyMethodDef JarowMethods[] = {
    {"jarow",  jarow, METH_VARARGS,
     "Do a Jaro-Winkler string match"},
    {NULL, NULL, 0, NULL}        /* Sentinel */
};

PyMODINIT_FUNC
initjarow(void)
{
  Py_InitModule("jarow", JarowMethods);
}

#endif /* TEMPLATING */
