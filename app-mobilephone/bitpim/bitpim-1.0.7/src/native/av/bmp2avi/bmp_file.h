// BITPIM
//
// Copyright (C) 2005 Joe Pham <djpham@netzero.com>
//
// This program is free software; you can redistribute it and/or modify
// it under the terms of the BitPim license as detailed in the LICENSE file.
//
// $Id: bmp_file.h 2117 2005-02-18 06:55:03Z djpham $

#ifndef __BMP_FILE_HH__
#define __BMP_FILE_HH__

#include <iostream>
#include <cstdio>

using namespace std;

class BMPFile {
private:
	unsigned int width, height, compression;
	unsigned short planes, bpp;
	unsigned int data_size;
	bool ok;
	unsigned char *data;
public:
	typedef struct _bmp_info {
		unsigned int	width;
		unsigned int	height;
		unsigned short	planes;
		unsigned short	bpp;
		unsigned int	compression;
		unsigned int	data_size;
	} BMPINFO;
	typedef struct _bmp_header {
		// char			id[2];
		unsigned int	file_size;
		unsigned int	reserved_1;
		unsigned int	data_offset;
		unsigned int	header_size;
		unsigned int	width;
		unsigned int	height;
		unsigned short	planes;
		unsigned short	bpp;
		unsigned int	compression;
		unsigned int	data_size;
		unsigned int	h_resolution;
		unsigned int	v_resolution;
		unsigned int	n_colors;
		unsigned int	imp_colors;
		unsigned int	palete[0x100];
	} BMPHEADER;
	BMPFile();
	BMPFile(FILE *file_in);
	BMPFile(const BMPINFO &bmp_info, unsigned char *data);
	~BMPFile();
	bool valid() const;
	BMPINFO get_info(void) const;
	unsigned int get_size() const;
	unsigned char *get_data() const;
	unsigned short get_bpp() const;
	void info(ostream &os) const;
	void write(FILE *file_out);
};

#endif
