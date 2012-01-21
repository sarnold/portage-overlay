// BITPIM
//
// Copyright (C) 2005 Joe Pham <djpham@netzero.com>
//
// This program is free software; you can redistribute it and/or modify
// it under the terms of the BitPim license as detailed in the LICENSE file.
//
// $Id: avi_file.cxx 2117 2005-02-18 06:55:03Z djpham $

#include "avi_file.h"
#include "byte_order.h"

// endian conversion routines

AVIMAINHEADER endian(const AVIMAINHEADER &hdr) {
	AVIMAINHEADER h={
	LSB32(hdr.dwMicroSecPerFrame),
	LSB32(hdr.dwMaxBytesPerSec),
	LSB32(hdr.dwPaddingGranularity),
	LSB32(hdr.dwFlags),
	LSB32(hdr.dwTotalFrames),
	LSB32(hdr.dwInitialFrames),
	LSB32(hdr.dwStreams),
	LSB32(hdr.dwSuggestedBufferSize),
	LSB32(hdr.dwWidth),
	LSB32(hdr.dwHeight),
	0, 0, 0, 0
	};
	return h;
}

AVISTREAMHEADER endian(const AVISTREAMHEADER &hdr) {
	AVISTREAMHEADER h;
	memcpy(h.fccType, hdr.fccType, 4);
	memcpy(h.fccHandler, hdr.fccHandler, 4);
	h.dwFlags=LSB32(hdr.dwFlags);
	h.wPriority=LSB16(hdr.wPriority);
	h.wLanguage=LSB16(hdr.wLanguage);
	h.dwInitialFrames=LSB32(hdr.dwInitialFrames);
	h.dwScale=LSB32(hdr.dwScale);
	h.dwRate=LSB32(hdr.dwRate);
	h.dwStart=LSB32(hdr.dwStart);
	h.dwLength=LSB32(hdr.dwLength);
	h.dwSuggestedBufferSize=LSB32(hdr.dwSuggestedBufferSize);
	h.dwQuality=LSB32(hdr.dwQuality);
	h.dwSampleSize=LSB32(hdr.dwSampleSize);
	h.rcFrame.left=LSB16(hdr.rcFrame.left);
	h.rcFrame.top=LSB16(hdr.rcFrame.top);
	h.rcFrame.right=LSB16(hdr.rcFrame.right);
	h.rcFrame.bottom=LSB16(hdr.rcFrame.bottom);
	return h;
}

BITMAPINFOHEADER endian(const BITMAPINFOHEADER &hdr) {
	BITMAPINFOHEADER h={
	LSB32(hdr.biSize),
	LSB32(hdr.biWidth),
	LSB32(hdr.biHeight),
	LSB16(hdr.biPlanes),
	LSB16(hdr.biBitCount),
	LSB32(hdr.biCompression),
	LSB32(hdr.biSizeImage),
	LSB32(hdr.biXPelsPerMeter),
	LSB32(hdr.biYPelsPerMeter),
	LSB32(hdr.biClrUsed),
	LSB32(hdr.biClrImportant)
	};
	return h;
}

RGBQUAD endian(const RGBQUAD &hdr) {
	return hdr;
}

aIndex endian(const aIndex &hdr) {
	aIndex h;
	memcpy(h.dwChunkId, hdr.dwChunkId, 4);
	h.dwFlags=LSB32(hdr.dwFlags);
	h.dwOffset=LSB32(hdr.dwOffset);
	h.dwSize=LSB32(hdr.dwSize);
	return h;
}

/////////////////////////////////////////////////////////////////////////////////////////////////
AVIChunk::AVIChunk():
	id(""),
	size(0),
	data(NULL) {
}

AVIChunk::AVIChunk(FILE *file_in):
	id(""),
	size(0),
	data(NULL) {

	read(file_in);
}

AVIChunk::AVIChunk(const string &id, const unsigned int size, void *_data):
	id(id),
	size(size),
	data(NULL) {
	if(size) {
		data=new unsigned char[size];
		memcpy(data, _data, size);
	}
}

AVIChunk::~AVIChunk() {
	if (data)
		delete [] data;
}

unsigned int AVIChunk::get_buffer_size() {
	return size+8;
}

unsigned int AVIChunk::get_size() {
	return size;
}

string AVIChunk::get_id() {
	return id;
}

unsigned char *AVIChunk::get_data(void) {
	return data;
}

void AVIChunk::read_hdr(FILE *file_in) {
	char s[5];s[4]=0;
	
	if(feof(file_in))
		return;
	fread(s, 4, 1, file_in);
	id=s;
	fread(&size, 4, 1, file_in);
	size=LSB32(size);
}

void AVIChunk::read(FILE *file_in) {
	read_hdr(file_in);
	// cerr << "Reading AVI Chunk: " << id << ", size: " << size << endl;
	if (size) {
		if (data)
			delete [] data;
		data=new unsigned char[size];
		fread(data, size, 1, file_in);
	}
}

void AVIChunk::write_hdr(FILE *file_out) {
	char s[5];s[4]=0;
	strncpy(s, id.c_str(), 4);
	fwrite(s, 4, 1, file_out);
	unsigned int sz(LSB32(size));
	fwrite(&sz, 4, 1, file_out);
}

void AVIChunk::write(FILE *file_out) {
	write_hdr(file_out);
	if (size)
		fwrite(data, size, 1, file_out);
}

void AVIChunk::info(ostream &os) {
	os << "\nChunk ID: " << id << endl;
	os << "  Size: " << size << endl;
}

void AVIChunk::update_size() {
}

/////////////////////////////////////////////////////////////////////////////////////////////////
AVIList::AVIList():
	id(""),
	type(""),
	size(0),
	data(NULL) {
}

AVIList::AVIList(FILE *file_in):
	id(""),
	type(""),
	size(0),
	data(NULL) {

	read(file_in);
}

AVIList::AVIList(const string &id, const string &type, const unsigned int size, void *_data):
	id(id),
	type(type),
	size(size),
	data(NULL) {
	if(size) {
		data=new unsigned char[size];
		memcpy(data, _data, size);
	}
}

AVIList::~AVIList() {
	if (data)
		delete [] data;
}

unsigned int AVIList::get_buffer_size() {
	return size+12;
}

unsigned int AVIList::get_size() {
	return size+4;
}

string AVIList::get_id() {
	return id;
}

string AVIList::get_type() {
	return type;
}

void AVIList::read_hdr(FILE *file_in) {
	char s[5];s[4]=0;

	fread(s, 4, 1, file_in);
	id=s;
	fread(&size, 4, 1, file_in);
	size=LSB32(size);
	size -=4;
	fread(s, 4, 1, file_in);
	type=s;
}

void AVIList::read(FILE *file_in) {
	read_hdr(file_in);
	if(data) {
		delete [] data;
		data=NULL;
	}
	if (size) {
		data=new unsigned char[size];
		fread(data, size, 1, file_in);
	}
}

void AVIList::write_hdr(FILE *file_out) {
	char s[5];s[4]=0;

	strncpy(s, id.c_str(), 4);
	fwrite(s, 4, 1, file_out);
	unsigned int i(size+4);
	i=LSB32(i);
	fwrite(&i, 4, 1, file_out);
	strncpy(s, type.c_str(), 4);
	fwrite(s, 4, 1, file_out);
}

void AVIList::write(FILE *file_out) {
	write_hdr(file_out);
	if (size)
		fwrite(data, size, 1, file_out);
}

void AVIList::info(ostream &os) {
	os << "List ID: " << id << endl;
	os << "  Size: " << size << endl;
	os << "  Type: " << type << endl;
}

void AVIList::update_size() {
}

/////////////////////////////////////////////////////////////////////////////////////////////////
avihChunk::avihChunk(FILE *file_in):
	AVIChunk() {

	read(file_in);
}

avihChunk::avihChunk():
AVIChunk() {
	id="avih";
	size=sizeof(avi_hdr);
}

avihChunk::avihChunk(const AVIMAINHEADER &main_hdr):
AVIChunk() {
	id="avih";
	avi_hdr=main_hdr;
	size=sizeof(avi_hdr);
}

avihChunk::~avihChunk() {
}

unsigned int avihChunk::get_buffer_size() {
	return AVIChunk::get_buffer_size();
}

void avihChunk::read(FILE *file_in) {
	read_hdr(file_in);
	if (size != sizeof(avi_hdr))
		cerr << "AVI Header struct size mismatch!" << endl;
	if(size) {
		fread(&avi_hdr, size, 1, file_in);
		avi_hdr=endian(avi_hdr);
	}
}

void avihChunk::write(FILE *file_out) {
	write_hdr(file_out);
	AVIMAINHEADER hdr(endian(avi_hdr));
	fwrite(&hdr, size, 1, file_out);
}

void avihChunk::info(ostream &os) {
	AVIChunk::info(os);

	os.setf(ios::showbase);
	os << "Main AVI Header:" << endl;
	os << "  dwMicroSecPerFrame: " << hex << avi_hdr.dwMicroSecPerFrame << "=" << dec << avi_hdr.dwMicroSecPerFrame<< endl;
	os << "  dwMaxBytesPerSec: " << hex << avi_hdr.dwMaxBytesPerSec << "=" << dec << avi_hdr.dwMaxBytesPerSec<< endl;
	os << "  dwPaddingGranularity: " << hex << avi_hdr.dwPaddingGranularity << "=" << dec << avi_hdr.dwPaddingGranularity<< endl;
	os << "  dwFlags: " << hex << avi_hdr.dwFlags << "=" << dec << avi_hdr.dwFlags<< endl;
	os << "  dwTotalFrames: " << hex << avi_hdr.dwTotalFrames << "=" << dec << avi_hdr.dwTotalFrames<< endl;
	os << "  dwInitialFrames: " << hex << avi_hdr.dwInitialFrames << "=" << dec << avi_hdr.dwInitialFrames<< endl;
	os << "  dwStreams: " << hex << avi_hdr.dwStreams << "=" << dec << avi_hdr.dwStreams<< endl;
	os << "  dwSuggestedBufferSize: " << hex << avi_hdr.dwSuggestedBufferSize << "=" << dec << avi_hdr.dwSuggestedBufferSize<< endl;
	os << "  dwWidth: " << hex << avi_hdr.dwWidth << "=" << dec << avi_hdr.dwWidth<< endl;
	os << "  dwHeight: " << hex << avi_hdr.dwHeight << "=" << dec << avi_hdr.dwHeight<< endl;
}

void avihChunk::update_size() {
	size=sizeof(avi_hdr);
}

void avihChunk::add_frame(const BMPFile &bmp) {
	avi_hdr.dwTotalFrames++;
}

/////////////////////////////////////////////////////////////////////////////////////////////////
hdrlList::hdrlList(FILE *file_in):
	AVIList(),
	avih(NULL) {

	read(file_in);
}

hdrlList::hdrlList():
	AVIList(),
	avih(NULL) {
	id="LIST";
	type="hdrl";
}

hdrlList::hdrlList(const AVIMAINHEADER &main_hdr,
				   const AVISTREAMHEADER &stream_hdr,
				   const BITMAPINFO &bitmap_info):
AVIList(),
avih(NULL) {
	id="LIST";
	type="hdrl";
	avih=new avihChunk(main_hdr);
	strl.push_back(new strlList(stream_hdr, bitmap_info));
	update_size();
}

hdrlList::~hdrlList() {
	if(avih)
		delete avih;
	for(int i=0;i<strl.size(); i++)
		delete strl[i];
}

unsigned int hdrlList::get_buffer_size() {
	return AVIList::get_buffer_size();
}

void hdrlList::read(FILE *file_in) {
	read_hdr(file_in);
	if(avih)
		delete avih;
	avih=new avihChunk(file_in);
	strl.clear();
	strl.push_back(new strlList(file_in));
	bool not_done(true);
	char c1[5], c2[5];c1[4]=c2[4]=0;
	int i;
	while(not_done) {
		fread(c1, 4, 1, file_in);
		fread(&i, 4, 1, file_in);
		fread(c2, 4, 1, file_in);
		string str(c2);
		fseek(file_in, -12, SEEK_CUR);
		if(c1=="LIST" && c2=="strl") {
			// one more strl list, add it in
			strl.push_back(new strlList(file_in));
		} else {
			not_done=false;
		}
	}
}

void hdrlList::write(FILE *file_out) {
	write_hdr(file_out);
	if(avih)
		avih->write(file_out);
	for(int i=0;i<strl.size(); i++)
		strl[i]->write(file_out);
}

void hdrlList::info(ostream &os) {
	AVIList::info(os);
	if(avih)
		avih->info(os);
	for(int i=0;i<strl.size(); i++)
		strl[i]->info(os);
}

void hdrlList::update_size() {
	// update everyone's size
	if (avih) {
		avih->update_size();
		size = avih->get_buffer_size();
	} else
		size=0;
	for(int i=0; i<strl.size(); i++) {
		strl[i]->update_size();
		size += strl[i]->get_buffer_size();
	}
}

void hdrlList::add_frame(const BMPFile &bmp) {
	avih->add_frame(bmp);
	strl.back()->add_frame(bmp);
}

BITMAPINFOHEADER hdrlList::get_bitmap_hdr(void) {
	return strl.back()->get_bitmap_hdr();
}

/////////////////////////////////////////////////////////////////////////////////////////////////
strhChunk::strhChunk(FILE *file_in):
AVIChunk() {
	read(file_in);
}
strhChunk::strhChunk():
AVIChunk() {
	id="strh";
	size=sizeof(stream_hdr);
}

strhChunk::strhChunk(const AVISTREAMHEADER &strm_hdr):
AVIChunk() {
	id="strh";
	stream_hdr=strm_hdr;
	size=sizeof(stream_hdr);
}

strhChunk::~strhChunk() {
}

unsigned int strhChunk::get_buffer_size() {
	return AVIChunk::get_buffer_size();
}

void strhChunk::read(FILE *file_in) {
	read_hdr(file_in);
	fread(&stream_hdr, size, 1, file_in);
	stream_hdr=endian(stream_hdr);
}

void strhChunk::write(FILE *file_out) {
	write_hdr(file_out);
	AVISTREAMHEADER hdr(endian(stream_hdr));
	fwrite(&hdr, size, 1, file_out);
}

void strhChunk::info(ostream &os) {
	AVIChunk::info(os);
	os.setf(ios::showbase);
	char s[5];s[4]=0;
	os << "AVI Stream Header:" << endl;
	strncpy(s, stream_hdr.fccType, 4);s[4]=0;
	os << "  fccType: " << s << endl;
	strncpy(s, stream_hdr.fccHandler, 4);s[4]=0;
	os << "  fccHandler: " << s << endl;
	os << "  dwFlags: " << hex << stream_hdr.dwFlags << "=" << dec << stream_hdr.dwFlags << endl;
	os << "  wPriority: " << hex << stream_hdr.wPriority << "=" << dec << stream_hdr.wPriority << endl;
	os << "  wLanguage: " << hex << stream_hdr.wLanguage << "=" << dec << stream_hdr.wLanguage << endl;
	os << "  dwInitialFrames: " << hex << stream_hdr.dwInitialFrames << "=" << dec <<
		stream_hdr.dwInitialFrames << endl;
	os << "  dwScale: " << hex << stream_hdr.dwScale << "=" << dec << stream_hdr.dwScale << endl;
	os << "  dwRate: " << hex << stream_hdr.dwRate << "=" << dec << stream_hdr.dwRate << endl;
	os << "  dwStart: " << hex << stream_hdr.dwStart << "=" << dec << stream_hdr.dwStart << endl;
	os << "  dwLength: " << hex << stream_hdr.dwLength << "=" << dec << stream_hdr.dwLength << endl;
	os << "  dwSuggestedBufferSize: " << hex << stream_hdr.dwSuggestedBufferSize << "=" << dec <<
		stream_hdr.dwSuggestedBufferSize << endl;
	os << "  dwQuality: " << hex << stream_hdr.dwQuality << "=" << dec << stream_hdr.dwQuality << endl;
	os << "  dwSampleSize: " << hex << stream_hdr.dwSampleSize << "=" << dec << stream_hdr.dwSampleSize << endl;
	os << "  left: " << hex << stream_hdr.rcFrame.left << "=" << dec << stream_hdr.rcFrame.left << endl;
	os << "  top: " << hex << stream_hdr.rcFrame.top << "=" << dec << stream_hdr.rcFrame.top << endl;
	os << "  right: " << hex << stream_hdr.rcFrame.right << "=" << dec << stream_hdr.rcFrame.right << endl;
	os << "  bottom: " << hex << stream_hdr.rcFrame.bottom << "=" << dec << stream_hdr.rcFrame.bottom << endl;
}

void strhChunk::update_size() {
	size=sizeof(stream_hdr);
}

void strhChunk::add_frame(const BMPFile &bmp) {
	stream_hdr.dwLength++;
}

/////////////////////////////////////////////////////////////////////////////////////////////////
strfChunk::strfChunk(FILE *file_in):
AVIChunk() {
	read(file_in);
}

strfChunk::strfChunk():
AVIChunk() {
	id="strf";
	size=sizeof(bitmap_info);
}

strfChunk::strfChunk(const BITMAPINFO &bmp_info):
AVIChunk() {
	id="strf";
	bitmap_info=bmp_info;
	size=sizeof(bitmap_info.bmiHeader);
}

strfChunk::~strfChunk() {
}

unsigned int strfChunk::get_buffer_size() {
	return AVIChunk::get_buffer_size();
}

void strfChunk::read(FILE *file_in) {
	read_hdr(file_in);
	fread(&bitmap_info, size, 1, file_in);
	bitmap_info.bmiHeader=endian(bitmap_info.bmiHeader);
}

void strfChunk::write(FILE *file_out) {
	write_hdr(file_out);
	BITMAPINFO bi(bitmap_info);
	bi.bmiHeader=endian(bi.bmiHeader);
	fwrite(&bi, size, 1, file_out);
}

void strfChunk::info(ostream &os) {
	AVIChunk::info(os);
	os.setf(ios::showbase);

	BITMAPINFOHEADER bmi_hdr(bitmap_info.bmiHeader);

	os << "Bitmap Info Header:" << endl;
	os << "  biSize:" << hex <<  bmi_hdr.biSize << "=" << dec << bmi_hdr.biSize << endl;
	os << "  biWidth:" << hex <<  bmi_hdr.biWidth << "=" << dec << bmi_hdr.biWidth << endl;
	os << "  biHeight:" << hex <<  bmi_hdr.biHeight << "=" << dec << bmi_hdr.biHeight << endl;
	os << "  biPlanes:" << hex <<  bmi_hdr.biPlanes << "=" << dec << bmi_hdr.biPlanes << endl;
	os << "  biBitCount:" << hex <<  bmi_hdr.biBitCount << "=" << dec << bmi_hdr.biBitCount << endl;
	os << "  biCompression:" << hex <<  bmi_hdr.biCompression << "=" << dec << bmi_hdr.biCompression << endl;
	os << "  biSizeImage:" << hex <<  bmi_hdr.biSizeImage << "=" << dec << bmi_hdr.biSizeImage << endl;
	os << "  biXPelsPerMeter:" << hex <<  bmi_hdr.biXPelsPerMeter << "=" << dec << bmi_hdr.biXPelsPerMeter << endl;
	os << "  biYPelsPerMeter:" << hex <<  bmi_hdr.biYPelsPerMeter << "=" << dec << bmi_hdr.biYPelsPerMeter << endl;
	os << "  biClrUsed:" << hex <<  bmi_hdr.biClrUsed << "=" << dec << bmi_hdr.biClrUsed << endl;
	os << "  biClrImportant:" << hex <<  bmi_hdr.biClrImportant << "=" << dec << bmi_hdr.biClrImportant << endl;
}

void strfChunk::update_size() {
}

BITMAPINFOHEADER strfChunk::get_bitmap_hdr(void) {
	return bitmap_info.bmiHeader;
}

/////////////////////////////////////////////////////////////////////////////////////////////////
idx1Chunk::idx1Chunk():
AVIChunk() {
	id="idx1";
	size=0;
}

idx1Chunk::idx1Chunk(FILE *file_in):
AVIChunk() {
	read(file_in);
}

idx1Chunk::idx1Chunk(const aIndex &idx):
AVIChunk() {
	id="idx1";
	index.push_back(idx);
	update_size();
}

idx1Chunk::~idx1Chunk() {
}

unsigned int idx1Chunk::get_buffer_size() {
	AVIChunk::get_buffer_size();
}

void idx1Chunk::read(FILE *file_in) {
	read_hdr(file_in);
	int k(sizeof(aIndex)), i(size/k);
	aIndex an_idx;
	for(int j=0;j<i;j++) {
		fread(&an_idx, k, 1, file_in);
		index.push_back(endian(an_idx));
	}
}

void idx1Chunk::write(FILE *file_out) {
	write_hdr(file_out);
	for(int i=0;i<index.size(); i++) {
		aIndex an_idx(endian(index[i]));
		fwrite(&an_idx, sizeof(aIndex), 1, file_out);
	}
}
void idx1Chunk::info(ostream &os) {
	AVIChunk::info(os);
	os.setf(ios::showbase);
	char s[5];s[4]=0;
	for(int i=0;i<index.size();i++) {
		strncpy(s, index[i].dwChunkId, 4);
		os << "  " << i << ": ID: " << s <<
			", Flags: " << hex << index[i].dwFlags << "=" << dec << index[i].dwFlags <<
			", offset: " << hex << index[i].dwOffset << "=" << dec << index[i].dwOffset <<
			", size: " << hex << index[i].dwSize << "=" << dec << index[i].dwSize << endl;
	}
}

void idx1Chunk::update_size() {
	size=0;
	for(int i=0;i<index.size(); i++)
		size+=sizeof(aIndex);
}

void idx1Chunk::add_frame(const BMPFile &bmp) {
	aIndex an_idx, last_idx(index.back());
	memcpy(an_idx.dwChunkId, "00db", 4);
	an_idx.dwFlags=AVIIF_KEYFRAME;
	an_idx.dwOffset=last_idx.dwOffset+last_idx.dwSize+8;
	an_idx.dwSize=bmp.get_size();
	index.push_back(an_idx);
}

/////////////////////////////////////////////////////////////////////////////////////////////////
strlList::strlList(FILE *file_in):
AVIList(),
strh(NULL),
strf(NULL) {
	read(file_in);
}

strlList::strlList():
AVIList(),
strh(NULL),
strf(NULL) {
	id="LIST";
	type="strl";
}

strlList::strlList(const AVISTREAMHEADER &stream_hdr,
				   const BITMAPINFO &bitmap_info):
AVIList() {
	id="LIST";
	type="strl";
	strh=new strhChunk(stream_hdr);
	strf=new strfChunk(bitmap_info);
	update_size();
}

strlList::~strlList() {
	if(strh)
		delete strh;
	if(strf)
		delete strf;
}

unsigned int strlList::get_buffer_size() {
	return AVIList::get_buffer_size();
}

void strlList::read(FILE *file_in) {
	read_hdr(file_in);
	if(strh)
		delete strh;
	strh=new strhChunk(file_in);
	if(strf)
		delete strf;
	strf=new strfChunk(file_in);
	char s[5];s[4]=0;
	// sneak a peek at the next list/chunk
	bool not_done(true);
	int i;
	while (not_done) {
		fread(s, 4, 1, file_in);
		string str(s);
		if (str=="strd" || str=="strn" || str=="JUNK") {
			// read the size and move on
			// cerr << "Chunk " << str << " found, moving on" << endl;
			fread(&i, 4, 1, file_in);
			i=LSB32(i);
			fseek(file_in, i, SEEK_CUR);
		} else {
			// backup and return
			// cerr << "Next Chunk/List: " << str << endl;
			fseek(file_in, -4, SEEK_CUR);
			not_done=false;
		}
	}
}

void strlList::write(FILE *file_out) {
	write_hdr(file_out);
	if(strh)
		strh->write(file_out);
	if(strf)
		strf->write(file_out);
}

void strlList::info(ostream &os) {
	AVIList::info(os);
	if(strh)
		strh->info(os);
	if(strf)
		strf->info(os);
}

void strlList::update_size() {
	if(strh) {
		strh->update_size();
		size=strh->get_buffer_size();
	} else
		size=0;
	if(strf) {
		strf->update_size();
		size+=strf->get_buffer_size();
	}
}

void strlList::add_frame(const BMPFile &bmp) {
	strh->add_frame(bmp);
}

BITMAPINFOHEADER strlList::get_bitmap_hdr(void) {
	return strf->get_bitmap_hdr();
}

/////////////////////////////////////////////////////////////////////////////////////////////////
moviList::moviList(FILE *file_in):
AVIList() {
	read(file_in);
}

moviList::moviList():
AVIList() {
	id="LIST";
	type="movi";
}

moviList::moviList(AVIChunk *chunk):
AVIList() {
	id="LIST";
	type="movi";
	chunk_list.push_back(chunk);
	update_size();
}


moviList::~moviList() {
	for(int i=0;i<chunk_list.size(); i++)
		delete chunk_list[i];
}

unsigned int moviList::get_buffer_size() {
	return AVIList::get_buffer_size();
}

void moviList::read(FILE *file_in) {
	read_hdr(file_in);
	char s[5];s[4]=0;
	while(!feof(file_in)) {
		fread(s, 4, 1, file_in);
		fseek(file_in, -4, SEEK_CUR);
		if(string(s)=="idx1")
			break;
		else {
			AVIChunk *c(new AVIChunk(file_in));
			chunk_list.push_back(c);
		}
	}
}

void moviList::write(FILE *file_out) {
	write_hdr(file_out);
	for(int i=0;i<chunk_list.size(); i++)
		chunk_list[i]->write(file_out);
}

void moviList::info(ostream &os) {
	AVIList::info(os);
	for(int i=0;i<chunk_list.size(); i++) {
		os << "Chunk #" << i << endl;
		chunk_list[i]->info(os);
	}
}

void moviList::update_size() {
	size=0;
	for(int i=0; i<chunk_list.size(); i++) {
		chunk_list[i]->update_size();
		size+=chunk_list[i]->get_buffer_size();
	}
}

void moviList::add_frame(const BMPFile &bmp) {
	// add a new frame to this list
	chunk_list.push_back(new AVIChunk("00db", bmp.get_size(), bmp.get_data()));
}

AVIChunk *moviList::get_chunk(const int frame_num) {
	if(frame_num>=chunk_list.size())
		return NULL;
	return chunk_list[frame_num];
}

/////////////////////////////////////////////////////////////////////////////////////////////////
riffList::riffList(FILE *file_in):
AVIList(),
hdrl(NULL),
movi(NULL),
idx1(NULL) {
	read(file_in);
}
riffList::riffList():
AVIList(),
hdrl(NULL),
movi(NULL),
idx1(NULL) {
	id="RIFF";
	type="AVI ";
}

riffList::riffList(const BMPFile &bmp, const unsigned int fps):
AVIList(),
hdrl(NULL),
movi(NULL),
idx1(NULL) {
	id="RIFF";
	type="AVI ";
	BMPFile::BMPINFO bmp_info(bmp.get_info());
	AVIMAINHEADER main_hdr;
	AVISTREAMHEADER stream_hdr;
	BITMAPINFO bitmap_info;
	memset(&main_hdr, 0, sizeof(main_hdr));
	memset(&stream_hdr, 0, sizeof(stream_hdr));
	memset(&bitmap_info, 0, sizeof(bitmap_info));
	main_hdr.dwMicroSecPerFrame=1000000/fps;
	main_hdr.dwMaxBytesPerSec=bmp.get_size()*fps;
	main_hdr.dwFlags=AVIFILEINFO_HASINDEX|AVIFILEINFO_TRUSTCKTYPE;
	main_hdr.dwTotalFrames=1;
	main_hdr.dwStreams=1;
	main_hdr.dwSuggestedBufferSize=bmp.get_size();
	main_hdr.dwWidth=bmp_info.width;
	main_hdr.dwHeight=bmp_info.height;
	memcpy(stream_hdr.fccType, "vids", 4);
	memset(stream_hdr.fccHandler, 0, 4);
	stream_hdr.dwScale=1;
	stream_hdr.dwRate=fps;
	stream_hdr.dwLength=1;
	stream_hdr.dwSuggestedBufferSize=bmp.get_size();
	stream_hdr.rcFrame.right=bmp_info.width;
	stream_hdr.rcFrame.bottom=bmp_info.height;
	BITMAPINFOHEADER bmi;
	memset(&bmi, 0, sizeof(bmi));
	bmi.biSize=sizeof(bmi);
	bmi.biWidth=bmp_info.width;
	bmi.biHeight=bmp_info.height;
	bmi.biPlanes=bmp_info.planes;
	bmi.biBitCount=bmp_info.bpp;
	bmi.biCompression=bmp_info.compression;
	bitmap_info.bmiHeader=bmi;
	hdrl=new hdrlList(main_hdr, stream_hdr, bitmap_info);
	movi=new moviList(new AVIChunk("00db", bmp.get_size(), bmp.get_data()));
	aIndex an_idx;
	memcpy(an_idx.dwChunkId, "00db", 4);
	an_idx.dwFlags=AVIIF_KEYFRAME;
	an_idx.dwOffset=4;
	an_idx.dwSize=bmp.get_size();
	idx1=new idx1Chunk(an_idx);
	update_size();
}

riffList::~riffList() {
	if(hdrl)
		delete hdrl;
	if(movi)
		delete movi;
	if(idx1)
		delete idx1;
}

unsigned int riffList::get_buffer_size() {
	return AVIList::get_buffer_size();
}

void riffList::read(FILE *file_in) {
	read_hdr(file_in);
	if (id!="RIFF") {
		cerr << "RIFF not found" << endl;
		return;
	}
	if(hdrl)
		delete hdrl;
	hdrl=new hdrlList(file_in);
	if(movi)
		delete movi;
	movi=new moviList(file_in);
	idx1=new idx1Chunk(file_in);
}
void riffList::write(FILE *file_out) {
	write_hdr(file_out);
	if(hdrl)
		hdrl->write(file_out);
	if(movi)
		movi->write(file_out);
	if(idx1)
		idx1->write(file_out);
}

void riffList::info(ostream &os) {
	AVIList::info(os);
	if (hdrl)
		hdrl->info(os);
	if(movi)
		movi->info(os);
	if(idx1)
		idx1->info(os);
}

void riffList::update_size() {
	size=0;
	if(hdrl) {
		hdrl->update_size();
		size+=hdrl->get_buffer_size();
	}
	if(movi) {
		movi->update_size();
		size+=movi->get_buffer_size();
	}
	if(idx1) {
		idx1->update_size();
		size+=idx1->get_buffer_size();
	}
}

void riffList::add_frame(const BMPFile &bmp) {
	// TODO: need to do some basic checking to ensure sames resolution, size, etc ...
	hdrl->add_frame(bmp);
	movi->add_frame(bmp);
	idx1->add_frame(bmp);
	update_size();
}

BMPFile *riffList::extract_frame(const unsigned int frame_num) {
	BITMAPINFOHEADER bitmap_hdr(hdrl->get_bitmap_hdr());
	AVIChunk *chunk(movi->get_chunk(frame_num));
	if(chunk==NULL)
		return NULL;
	BMPFile::BMPINFO bmp_info={
		bitmap_hdr.biWidth,
		bitmap_hdr.biHeight,
		bitmap_hdr.biPlanes,
		bitmap_hdr.biBitCount,
		bitmap_hdr.biCompression,
		chunk->get_size()
	};
	return new BMPFile(bmp_info, chunk->get_data());
}

/////////////////////////////////////////////////////////////////////////////////////////////////
