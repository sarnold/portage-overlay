// BITPIM
//
// Copyright (C) 2005 Joe Pham <djpham@netzero.com>
//
// This program is free software; you can redistribute it and/or modify
// it under the terms of the BitPim license as detailed in the LICENSE file.
//
// $Id: byte_order.h 2117 2005-02-18 06:55:03Z djpham $

#ifndef __BYTE_ORDER_HH__
#define __BYTE_ORDER_HH__

#define SWAP16(x) (((x>>8) & 0x00ff) |\
                   ((x<<8) & 0xff00))

#define SWAP32(x) (((x>>24) & 0x000000ff) |\
                   ((x>>8)  & 0x0000ff00) |\
                   ((x<<8)  & 0x00ff0000) |\
                   ((x<<24) & 0xff000000))

#ifdef __BIG_ENDIAN__
#define MSB16(x)	(x)
#define MSB32(x)	(x)
#define LSB16(x)	SWAP16((x))
#define LSB32(x)	SWAP32((x))
#else
#define MSB16(x)	SWAP16((x))
#define MSB32(x)	SWAP32((x))
#define LSB16(x)	(x)
#define LSB32(x)	(x)
#endif

#endif
