
#ifndef JAROW_BITSET_H
#define JAROW_BITSET_H
#ifdef __cplusplus
extern "C" {
#endif

/* A somewhat mashed version of the standard Python bitset.h header.
   That one doesn't export the symbols so we have to define everything
   here. */

/* Bitset interface */

#define BYTE		char

#define BITSPERBYTE	(8*sizeof(BYTE))
#define NBYTES(nbits)	(((nbits) + BITSPERBYTE - 1) / BITSPERBYTE)

#define BIT2BYTE(ibit)	((ibit) / BITSPERBYTE)
#define BIT2SHIFT(ibit)	((ibit) % BITSPERBYTE)
#define BIT2MASK(ibit)	(1 << BIT2SHIFT(ibit))
#define BYTE2BIT(ibyte)	((ibyte) * BITSPERBYTE)

typedef BYTE *bitset;

static bitset 
newbitset(int nbits)
{
  bitset result=(bitset)PyMem_Malloc(NBYTES(nbits));
  if (!result) return result;
  memset(result, 0, NBYTES(nbits));
  return result;
}

static void
delbitset(bitset bs)
{
  PyMem_Free(bs);
}

#define testbit(bs, ibit) (((bs)[BIT2BYTE(ibit)] & BIT2MASK(ibit)) != 0)

#define addbit(bs, ibit)  (bs)[BIT2BYTE((ibit))]|=BIT2MASK((ibit))

#ifdef __cplusplus
}
#endif
#endif /* JAROW_BITSET_H */
