// BITPIM
//
// Copyright (C) 2005 Joe Pham <djpham@netzero.com>
//
// This program is free software; you can redistribute it and/or modify
// it under the terms of the BitPim license as detailed in the LICENSE file.
//
// $Id: avi_file.h 2117 2005-02-18 06:55:03Z djpham $

#ifndef __BMP2AVI_HH__
#define __BMP2AVI_HH__

#include <iostream>
#include <fstream>
#include <string>
#include <cstdlib>
#include <vector>
#include <memory>
#include "bmp_file.h"

using namespace std;

typedef unsigned int DWORD;
typedef unsigned short WORD;
typedef long LONG;
typedef	unsigned char FOURCC[4];

#define AVIIF_KEYFRAME				0x10
#define AVIFILEINFO_HASINDEX		0x10
#define AVIFILEINFO_MUSTUSEINDEX	0x20
#define AVIFILEINFO_TRUSTCKTYPE		0x800

typedef struct _avimainheader {
	// char	fcc[4];
	// DWORD	cb;
	DWORD	dwMicroSecPerFrame;
	DWORD	dwMaxBytesPerSec;
	DWORD	dwPaddingGranularity;
	DWORD	dwFlags;
	DWORD	dwTotalFrames;
	DWORD	dwInitialFrames;
	DWORD	dwStreams;
	DWORD	dwSuggestedBufferSize;
	DWORD	dwWidth;
	DWORD	dwHeight;
	DWORD	dwReserved[4];
} AVIMAINHEADER;

AVIMAINHEADER endian(const AVIMAINHEADER &hdr);

typedef struct _avistreamheader {
	// char	fcc[4];
	// DWORD	cb;
	char	fccType[4];
	char	fccHandler[4];
	DWORD	dwFlags;
	WORD	wPriority;
	WORD	wLanguage;
	DWORD	dwInitialFrames;
	DWORD	dwScale;
	DWORD	dwRate;
	DWORD	dwStart;
	DWORD	dwLength;
	DWORD	dwSuggestedBufferSize;
	DWORD	dwQuality;
	DWORD	dwSampleSize;
	struct {
		short left;
		short top;
		short right;
		short bottom;
	} rcFrame;
} AVISTREAMHEADER;

AVISTREAMHEADER endian(const AVISTREAMHEADER &hdr);

typedef struct _bitmapinforheader {
	DWORD	biSize;
	LONG	biWidth;
	LONG	biHeight;
	WORD	biPlanes;
	WORD	biBitCount;
	DWORD	biCompression;
	DWORD	biSizeImage;
	LONG	biXPelsPerMeter;
	LONG	biYPelsPerMeter;
	DWORD	biClrUsed;
	DWORD	biClrImportant;
} BITMAPINFOHEADER, *PBITMAPINFOHEADER;

BITMAPINFOHEADER endian(const BITMAPINFOHEADER &hdr);

typedef struct _rgbquad {
	unsigned char rgbBlue;
	unsigned char rgbGreen;
	unsigned char rgbRed;
	unsigned char rgbReserved;
} RGBQUAD;

RGBQUAD endian(const RGBQUAD &hdr);

typedef struct _bitmapinfo {
	BITMAPINFOHEADER	bmiHeader;
	RGBQUAD				bmiColors[1];
} BITMAPINFO, *PBITMAPINFO;

typedef struct _avioldindex_entry {
	char	dwChunkId[4];
	DWORD	dwFlags;
	DWORD	dwOffset;
	DWORD	dwSize;
} aIndex;

aIndex endian(const aIndex &hdr);

class AVIChunk {
protected:
	string id;
	unsigned int size;
	unsigned char *data;
	void read_hdr(FILE *file_in);
	void write_hdr(FILE *file_out);
public:
	AVIChunk(FILE *file_in);
	AVIChunk(const string &id, const unsigned int size, void *data);
	AVIChunk();
	~AVIChunk();
	void write(FILE *file_out);
	void read(FILE *file_in);
	unsigned int get_buffer_size();
	unsigned int get_size();
	unsigned char *get_data(void);
	string get_id();
	void info(ostream &os);
	void update_size();
};

class AVIList {
protected:
	string id, type;
	unsigned int size;
	unsigned char *data;
	void read_hdr(FILE *file_in);
	void write_hdr(FILE *file_out);
public:
	AVIList(FILE *file_in);
	AVIList(const string &id, const string &type, const unsigned int size, void *data);
	AVIList();
	~AVIList();
	void write(FILE *file_out);
	void read(FILE *file_in);
	unsigned int get_buffer_size();
	unsigned int get_size();
	string get_id();
	string get_type();
	void info(ostream &os);
	void update_size();
};

class avihChunk: protected AVIChunk {
private:
	AVIMAINHEADER avi_hdr;
public:
	avihChunk(FILE *file_in);
	avihChunk(const AVIMAINHEADER &main_hdr);
	avihChunk();
	~avihChunk();
	unsigned int get_buffer_size();
	void read(FILE *file_in);
	void write(FILE *file_out);
	void info(ostream &os);
	void update_size();
	void add_frame(const BMPFile &bmp);
};

class strhChunk: protected AVIChunk {
private:
	AVISTREAMHEADER stream_hdr;
public:
	strhChunk(FILE *file_in);
	strhChunk(const AVISTREAMHEADER &stream_hdr);
	strhChunk();
	~strhChunk();
	unsigned int get_buffer_size();
	void read(FILE *file_in);
	void write(FILE *file_out);
	void info(ostream &os);
	void update_size();
	void add_frame(const BMPFile &bmp);
};

class strfChunk: protected AVIChunk {
private:
	BITMAPINFO bitmap_info;
public:
	strfChunk(FILE *file_in);
	strfChunk(const BITMAPINFO &bitmap_info);
	strfChunk();
	~strfChunk();
	unsigned int get_buffer_size();
	void read(FILE *file_in);
	void write(FILE *file_out);
	void info(ostream &os);
	void update_size();
	BITMAPINFOHEADER get_bitmap_hdr(void);
};

typedef vector<aIndex> IndexVector;
class idx1Chunk:protected AVIChunk {
private:
	IndexVector index;
public:
	idx1Chunk();
	idx1Chunk(FILE *file_in);
	idx1Chunk(const aIndex &idx);
	~idx1Chunk();
	unsigned int get_buffer_size();
	void read(FILE *file_in);
	void write(FILE *file_out);
	void info(ostream &os);
	void update_size();
	void add_frame(const BMPFile &bmp);
};

class strlList: protected AVIList {
private:
	strhChunk *strh;
	strfChunk *strf;
public:
	strlList(FILE *file_in);
	strlList(const AVISTREAMHEADER &stream_hdr,
		const BITMAPINFO &bitmap_info);
	strlList();
	~strlList();
	unsigned int get_buffer_size();
	void read(FILE *file_in);
	void write(FILE *file_out);
	void info(ostream &os);
	void update_size();
	void add_frame(const BMPFile &bmp);
	BITMAPINFOHEADER get_bitmap_hdr(void);
};

typedef vector<AVIChunk *> ChunkListType;
class moviList: protected AVIList {
private:
	ChunkListType chunk_list;
public:
	moviList(FILE *file_in);
	moviList(AVIChunk *chunk);
	moviList();
	~moviList();
	unsigned int get_buffer_size();
	void read(FILE *file_in);
	void write(FILE *file_out);
	void info(ostream &os);
	void update_size();
	void add_frame(const BMPFile &bmp);
	AVIChunk *get_chunk(const int frame_num);
};

typedef vector<strlList *> strlVector;
class hdrlList: protected AVIList {
private:
	avihChunk *avih;
	strlVector strl;
public:
	hdrlList(FILE *file_in);
	hdrlList();
	hdrlList(const AVIMAINHEADER &main_hdr, const AVISTREAMHEADER &stream_hdr,
		const BITMAPINFO &bitmap_info);
	~hdrlList();
	unsigned int get_buffer_size();
	void read(FILE *file_in);
	void write(FILE *file_out);
	void info(ostream &os);
	void update_size();
	void add_frame(const BMPFile &bmp);
	BITMAPINFOHEADER get_bitmap_hdr(void);
};

class riffList: protected AVIList {
private:
	hdrlList *hdrl;
	moviList *movi;
	idx1Chunk *idx1;
public:
	riffList(FILE *file_in);
	riffList(const BMPFile &bmp, const unsigned int fps);
	riffList();
	~riffList();
	unsigned int get_buffer_size();
	void read(FILE *file_in);
	void write(FILE *file_out);
	void info(ostream &os);
	void update_size();
	void add_frame(const BMPFile &bmp);
	BMPFile *extract_frame(const unsigned int frame_num);
};

#endif
