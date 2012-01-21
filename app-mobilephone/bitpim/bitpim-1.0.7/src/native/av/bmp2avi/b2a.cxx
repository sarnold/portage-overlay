// BITPIM
//
// Copyright (C) 2005 Joe Pham <djpham@netzero.com>
//
// This program is free software; you can redistribute it and/or modify
// it under the terms of the BitPim license as detailed in the LICENSE file.
//
// $Id: b2a.cxx 2117 2005-02-18 06:55:03Z djpham $

#include <iostream>
#include <cstdlib>

#include "byte_order.h"
#include "avi_file.h"
#include "bmp_file.h"

using namespace std;

static void get_options(int argc, char *argv[]);
static void print_help_and_exit(const string &exe_name, const int exit_code);

// global optional variables
string in_file_name(""), out_file_name("");
unsigned int fps(4);	// default to 4 frames/second
unsigned int frame_num(0);	// default to the 1st frame
bool build_avi(true);	// default to build AVI from BMP files

static void build_avi_file(void) {
	FILE *f(fopen(in_file_name.c_str(), "rb"));
	if (!f) {
		cerr << "Failed to open BMP file " << in_file_name << endl;
		exit(2);
	}
	BMPFile bmp_file(f);
	fclose(f);
	if(!bmp_file.valid()) {
		cerr << in_file_name << " is not a valid BMP file" << endl;
		exit(3);
	}
	if(bmp_file.get_bpp() !=24) {
		// only works with 24-bit BMP file
		cerr << in_file_name << " is not a 24-bit BMP file" << endl;
		exit(4);
	}

	FILE *riff_f(fopen(out_file_name.c_str(), "rb"));
	riffList *riff;
	if (!riff_f) {
		// cerr << "File " << out_file_name << " does not exist, creating one" << endl;
		riff=new riffList(bmp_file, 4);
	} else {
		// cerr << "File " << out_file_name << " exists, adding this new frame to it" << endl;
		riff=new riffList(riff_f);
		fclose(riff_f);
		riff->add_frame(bmp_file);
	}
	FILE *f_out(fopen(out_file_name.c_str(), "wb"));
	if(!f_out) {
		cerr << "Failed to open output file: " << out_file_name << endl;
		exit(5);
	}
	riff->write(f_out);
	fclose(f_out);
	// just for fun
	delete riff;
}

static void extract_bmp_frame(void) {
	FILE *f(fopen(in_file_name.c_str(), "rb"));
	if(!f) {
		cerr << "Failed to open file " << in_file_name << endl;
		exit(1);
	}
	riffList riff(f);
	fclose(f);
	BMPFile *bmp(riff.extract_frame(frame_num));
	if(!bmp) {
		cerr << "Failed to extract frame from AVI file" << endl;
		exit(2);
	}
	FILE *f_out(fopen(out_file_name.c_str(), "wb"));
	bmp->write(f_out);
	fclose(f_out);
	delete bmp;
}

int main(int argc, char *argv[]) {

	get_options(argc, argv);
	if(build_avi)
		build_avi_file();
	else
		extract_bmp_frame();
}

void print_help_and_exit(const string &exe_name, const int exit_code) {
	cerr << "Usage :" << exe_name <<
		" [-help] [-f <frame-per-second> | -t <frame number>] -i <input file name> -o <output file name>" << endl;
	exit(exit_code);
}

void get_options(int argc, char *argv[]) {
	string exe_name(argv[0]);
	for(int i=1;i<argc;i++) {
		string s(argv[i]);
		if(s.substr(0, 2)=="-h")
			print_help_and_exit(exe_name, 0);
		else if (s=="-f")
			fps=atoi(argv[++i]);
		else if (s=="-t") {
			frame_num=atoi(argv[++i]);
			// extract frame instead
			build_avi=false;
		} else if (s=="-i")
			in_file_name=argv[++i];
		else if (s=="-o")
			out_file_name=argv[++i];
		else
			print_help_and_exit(exe_name, 1);
	}
	// Primitive checks
	if (in_file_name.empty() || out_file_name.empty())
		print_help_and_exit(exe_name, 2);
}
