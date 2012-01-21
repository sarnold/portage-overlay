// BITPIM
//
// Copyright (C) 2005 Joe Pham <djpham@netzero.com>
//
// This program is free software; you can redistribute it and/or modify
// it under the terms of the BitPim license as detailed in the LICENSE file.
//
// $Id: bmp_file.cxx 2117 2005-02-18 06:55:03Z djpham $

#include <iostream>
#include <string>
#include "bmp_file.h"
#include "byte_order.h"

using namespace std;

BMPFile::BMPFile():
width(0),
height(0),
compression(0),
planes(0),
bpp(0),
data_size(0),
ok(false),
data(NULL) {
}

BMPFile::BMPFile(const BMPINFO &bmp_info, unsigned char *_data):
ok(true) {
	width=bmp_info.width;
	height=bmp_info.height;
	compression=bmp_info.compression;
	planes=bmp_info.planes;
	bpp=bmp_info.bpp;
	data_size=bmp_info.data_size;
	data=new unsigned char[data_size];
	memcpy(data, _data, data_size);
}

BMPFile::BMPFile(FILE *file_in):
width(0),
height(0),
compression(0),
planes(0),
bpp(0),
data_size(0),
ok(false),
data(NULL) {
	char s[3];s[2]=0;
	fread(s, 2, 1, file_in);
	if(string(s)!="BM") {
		// not a BMP file
		cerr << "Not a BMP file." << endl;
		return;
	}
	ok=true;
	// read the info
	unsigned int file_size;
	fread(&file_size, 4, 1, file_in);
	file_size=LSB32(file_size);
	fseek(file_in, 4, SEEK_CUR);
	unsigned int data_offset;
	fread(&data_offset, 4, 1, file_in);
	data_offset=LSB32(data_offset);
	fseek(file_in, 4, SEEK_CUR);
	fread(&width, 4, 1, file_in);
	width=LSB32(width);
	fread(&height, 4, 1, file_in);
	height=LSB32(height);
	fread(&planes, 2, 1, file_in);
	planes=LSB16(planes);
	fread(&bpp, 2, 1, file_in);
	bpp=LSB16(bpp);
	fread(&compression, 4, 1, file_in);
	compression=LSB32(compression);
	// read the data
	data_size=file_size-data_offset;
	fseek(file_in, data_offset, SEEK_SET);
	data=new unsigned char[data_size];
	fread(data, data_size, 1, file_in);
}

BMPFile::~BMPFile() {
	if(data)
		delete [] data;
}

bool BMPFile::valid() const {
	return ok;
}

BMPFile::BMPINFO BMPFile::get_info(void) const {
	BMPINFO bmp_info={
		width, height, planes, bpp, compression, data_size };
	return bmp_info;
}

unsigned char *BMPFile::get_data() const {
	return data;
}

void BMPFile::info(ostream &os) const {
	if (!ok) {
		os << "Not a valid BMP file" << endl;
		return;
	}
	os.setf(ios::showbase);
	os << "Resolution: " << width << "x" << height << endl;
	os << "BPP: " << bpp << ", planes: " << planes << ", compression: " << compression << endl;
	os << "Data size: " << hex << data_size << "=" << dec << data_size << endl;
	os << "Data: ";
	for(int i=0;i<16;i++) {
		unsigned short j(data[i]);
		os << " " << hex << j;
	}
	os << endl;
}

unsigned int BMPFile::get_size() const {
	return data_size;
}

unsigned short BMPFile::get_bpp() const {
	return bpp;
}

void BMPFile::write(FILE *file_out) {
	BMPHEADER hdr;
	unsigned int hdr_size(sizeof(hdr)+2);
	memset(&hdr, 0, sizeof(hdr));
	hdr.file_size=LSB32(hdr_size+data_size);
	hdr.data_offset=LSB32(hdr_size);
	hdr.header_size=LSB32(0x28);
	hdr.width=LSB32(width);
	hdr.height=LSB32(height);
	hdr.planes=LSB16(planes);
	hdr.bpp=LSB16(bpp);
	hdr.compression=LSB32(compression);
	fwrite("BM", 2, 1, file_out);
	fwrite(&hdr, sizeof(hdr), 1, file_out);
	fwrite(data, data_size, 1, file_out);
}
