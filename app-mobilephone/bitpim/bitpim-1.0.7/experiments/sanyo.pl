#!/usr/bin/perl
#
# THIS FILE IS NOT PART OF BITPIM.  IT IS HERE FOR REFERENCE ONLY
#
# sanyo.pl: Sanyo 4900 sync test program:
#
# Distributed under the terms of the
# Perl Artistic License (http://www.perl.com/pub/a/language/misc/Artistic.html)
# or the GNU Public License, version 2 (http://www.gnu.org/copyleft/gpl.html)
#
#   sawpcs  26.09.2003  0.50 First version that reads the phone book entries
#           28.09.2003  0.60 Add command line switches for sending interpreted
#                            data to a file, and to dump packets to a file.
#           29.09.2003  0.61 Fix bug in todo and callback lists.
#           07.10.2003  0.70 Write dump file in format for BITPIM analyzer
#           14.10.2003  0.71 Fix formatting of bitpim dump
#           30.10.2003  0.72 Minor Fixups
#           31.10.2003  0.73 Also dump 1000, 4000, and 7000 byte buffers
#                            for use by BITPIM analyzer.
# 
# 
# Usage:
#   0.  Make sure that the perl module Device::SerialPort is installed.
#   1.  USB cable to computer and phone
#   2.  Softlink /dev/pcsphone to the device your phone is connected to.
#       This will likely be /dev/input/ttyACM0.
#   3.  Run this script, redirecting output to a file
#       e.g.     ./sanyo.pl > sanyo.out
#   4.  Examine the file to find your Phonebook, Calendar, Notifications,
#        and Call History.  Help me out by trying to interpret some of the
#        things I don't understand.
#
# This program only reads from the phone.  In principle, all it takes to write
# to the phone is put the phone in write mode (see qcplink) and then construct
# packets that start with 0E instead of 0D.  One must of course be careful to
# only write stuff you understand.  Also, is is probably important to
# understand and properly edit the stuff read by the 0dXX0f packets.  (See
# the "bigchunk" buffers below.  Not doing this right could mess up caller
# ID showing the right name of a caller, or worse totally hosing your phone.
# I am sure one could mess up the PCSVision functionality of the phone with a
# little effort.
#
#  Warning:  The USB/ACM system seems to sometimes cause soft kernel OOPSes.
#            The system will still be up, but further USB operations may not
#            work until the system is rebooted.  This seems to be because USB
#            is hot pluggable, it is possible for a device to be disconnected
#            while applications still have the device open.  Things are tricky
#            for this phone because one must reset it at the end, and this
#            reset causes the phone to power cycle.  When this happens, the
#            USB system will detect that the phone is no longer there and
#            remove the ttyACM device.  If this script tries to communicate
#            while the device is gone, then kernel problems happen.  What is
#            done here is to send the reset (a break) and then immediately
#            close the device and hope that the close happens fast enough.
#
#            What I find works best, is each time after running this program,
#            wait about 15 seconds, unplug the phone from the computer.  Wait
#            a bit more, and then plug it back in.
#
# Acknowledgements:
#    http://qcplink.sourceforge.net/:  Software for a Qualcom 27XX phone.
#         The software and protocol discussions there gave the hint that
#         that the 4900 used the same data protocol.  By simply running
#         qcplink in test mode using the USB serial device created when the
#         phone is plugged in, it was found out how to put the phone into
#         data mode and that the phone uses HDLC framing.
#    Anonymous poster on sprintusers.com:  Discovered the packet size for the
#         4900 (508 bytes) and some the packet codes for talking to the phone
#         book.  The important clues were that packets for reading start with
#         0x0d and writing with 0x0e.
#    http://www.waider.ie/:  Has a nice collection of "Toy" perl scripts,
#         including a script to talk to a GSM phone.  Used his scripts for
#         guidance in opening serial ports and creating phone book
#         structures.
#
# Other References:
# Nate Carlson's site on using the 4900 to access the internet.  Usefull for
#   this project because it has information on how to configure a USB phone
#   so that one can communicate with it as if it were a serial device.
#   http://www.natecarlson.com/linux/sanyo-4900.php
#
# Sanyo 4900 Users Manual:
#   http://www.sanyo.com/wireless/handsets/downloads/Scp-4900_user.pdf
#
# Sanyo 4900 Specifications
#   http://www.sanyo.com/wireless/handsets/downloads/PCS-4900_spec.pdf
#
# Bitpim, software for the LG-VX4400 which appears to use the BREW protocol
#   which seems to be different than what the 4900 uses.  But there may be
#   things to be learned from that project as the LG and Sanyo phones both
#   use Qualcomm chipsets..  (e.g., the meaning of time, namely number of
#   seconds since Jan 1, 1980, plus a fudge factor, seem to be the same.)
#   http://bitpim.sourceforge.net/
#
use Device::SerialPort;

$scriptversion = "0.73 (31.10.2003)";
$devicename = "/dev/pcsphone";
$expectedphonename = "SCP-4900";

@phonetypes = ("Home", "Work", "Mobile", "Pager", "Data", "Fax", "No Label");
@repeattypes = ("No","Daily","Weekly","Monthly","Yearly");
@ringernames
    = ("Normal","None","Vibrate",("")x7,"Tone 1","Tone 2","Tone 3","Tone 4",
       "Tone 5",("")x15,"La Bamba","Foster Dreamer","Schubert March",
       "Mozart Eine Kleine","Debussey Arabesq","Nedelka","Brahms Hungarian",
       "Star Spangled Banner","Rodeo","Birds","Toy Box");


while($#ARGV >= 0) {
    if ($ARGV[0] eq "-o") {
	$outputfile = $ARGV[1];
	shift(@ARGV);shift(@ARGV);
    } elsif ($ARGV[0] eq "-d") {
	$dumpfile = $ARGV[1];
	shift(@ARGV);shift(@ARGV);
    } elsif ($ARGV[0] eq "-i") {
	$devicename = $ARGV[1];
	shift(@ARGV);shift(@ARGV);
    } elsif ($ARGV[0] =~ /-h/) {
	print STDERR "Usage: sanyo.pl [-d hexdumpfilename] [-o Outputfilename] [-i phonedevicename] [-h]\n";
	exit;
    }
}

if($outputfile) {
    open(OUT, ">$outputfile") || die("Can't open output file \"$outputfile\": $!");
    $fh_out = OUT;
} else {
    $fh_out = STDOUT;
}
if($dumpfile) {
    open(DUMP, ">$dumpfile") || die("Can't open hexdump file \"$dumpfile\": $!");
    $fh_dump = DUMP;
}

print STDERR "\nPCS Phone Dump Perl Script Version $scriptversion\n\n";
print $fh_out "\nPCS Phone Dump Perl Script Version $scriptversion\n\n";

$p = sanyo_open($devicename);

writeport($p,"ATZ\r");
checkreply($p);
checkreply($p); # Do it twice just in case
writeport($p, "AT+GMM\r");
($status, $reply) = checkreply($p);

if(not $status) {
    print STDERR "Phone ($devicename) did not respond properly\n";
    sanyo_close($p);
    exit;
}
if($reply=~/$expectedphonename/s) {
    print STDERR qq{Phone appears to be the expected $expectedphonename\n};
} else {
    print STDERR qq{Phone response of\n$reply\ndoes not contain expected phone name of $expectedphonename\n};
    sanyo_close($p);
    exit;
}

print STDERR "Entering datamode\n";
sanyo_datamode($p);
$debug=0;

print STDERR "Retrieving firmware information\n";
$packet = sendandreceive($p, "\0"); # Get firmware information
($firmware,$model,$prl) = unpack("x79A10x7A16A5x3",$packet);
print STDERR "Phone firmware version is $firmware.  PRL is $prl\n";

print STDERR "Retrieving the phone number\n";
$packet = sendandreceive($p, "\x26\xB2\0\0"."\0"x129); # Get #
($thisphonenumber) = unpack("x4A10x122",$packet);
print STDERR "Phone number is $thisphonenumber\n";

print $fh_out "Phone number: $thisphonenumber\n";
print $fh_out "Model: $model\n";
print $fh_out "Firmware: $firmware\n";
print $fh_out "PRL: $prl\n";


$packet = sendandreceive($p, "\01"); # Get ESN
($esn) = unpack("xVx3",$packet);
printf($fh_out "ESN: %8.8x\n\n", $esn);

print STDERR "Retrieving owner information.";
$packet = sendandreceive($p, "\x0d\x3b\x0c"."\0"x502);
($owner,$ybirth,$mbirth,$dbirth,$iblood,$address,$ohemail
 ,$owemail,$ohomephone,$oworkphone) =
    unpack("x3A16vCCCA110A48A48A48A48x182",$packet);
print $fh_out "Owner: $owner\n";
print $fh_out "Born: $mbirth/$dbirth/$ybirth\n";
print $fh_out "Blood Type: ".("?","A","B","O","AB")[$iblood]."\n";
print $fh_out "Address: $address\n";
print $fh_out "Home Email: $ohemail\n";
print $fh_out "Work Email: $owemail\n";
print $fh_out "Home Phone: $ohomephone\n";
print $fh_out "Work Phone: $oworkphone\n\n";
print STDERR "  Owner is $owner." if $owner;
print STDERR "\n";

# Dump out the calendar
print STDERR "Retrieving the Calendar\n";
for($icalslot=0;$icalslot<100;$icalslot++) {
    $packet=sendandreceive($p, pack("H6Cx501","0D230C",$icalslot));
    ($islot,$flag,$event,$elen,$start,$stop,$location,$llen,$atype,$num1,$num2
     ,$num3,$period,$day,$atime,$num4) = 
     unpack("x3CCA14x7CVVA14x7CCCCvCCVCx439",$packet);
    if($flag > 0) {
	print $fh_out "Calendar Slot $icalslot($islot) $flag\n";
	print $fh_out "Past Event\n" if($flag==2);
	print $fh_out "Event: $event\n";
	print $fh_out "Location: $location\n";
	print $fh_out "Alarm: $atime(".msd_date2string($atime).") ".("Beep","Voice","Silent")[$atype]."\n";
	print $fh_out "Start: $start(".msd_date2string($start).") Repeat "
	    .$repeattypes[$period]."\n";
	print $fh_out "Stop: $stop(".msd_date2string($stop).")\n";
	print $fh_out "Day, other numbers: $day $num1 $num2 $num3 $num4\n\n";
    }
}    
# Dump Call Alarms
print STDERR "Retrieving Call Alarms\n";
for($icaslot=0;$icaslot<15;$icaslot++) {
    $packet=sendandreceive($p, pack("H6Cx501","0D240C",$icaslot));
    ($islot,$flag,$num1,$phonenum,$phonenumlen,$date1,$period,$day,$date2
     ,$name,$namelen,$phonenumtype,$phonenumslot,$num2) = 
     unpack("x3CCCA49CVCCVA17CCvCx420",$packet);
    if($flag > 0) {
	print $fh_out "Call Alarm Slot $icaslot($islot) $flag\n";
	print $fh_out "Phone Number: $phonenum\n";
	print $fh_out "Name: $name\n" if ($name);
	print $fh_out "Phonebook entry: $phonenumslot ".$phonetypes[$phonenumtype-1]."\n"
	    if ($phonenumslot != -1);
	print $fh_out "Alarm: $date1(".msd_date2string($date1).")\n";
	print $fh_out "Other Date: $date2(".msd_date2string($date2).")\n";
	print $fh_out "Repeat: ".$repeattypes[$period]."\n";
	print $fh_out "Day, other numbers: $day $num1 $num2\n\n";
    }
}
# Dump To Do List
print STDERR "Retrieving To Do List\n";
for($itdslot=0;$itdslot<19;$itdslot++) {
    $packet=sendandreceive($p, pack("H6Cx501","0D250C",$itdslot));
    ($islot,$flag,$todo,$todolen,$num1,$num2,$num3) = 
     unpack("x3CCA21CCCCx475",$packet);
    if($flag > 0) {
	print $fh_out "To Do Slot $itdslot($islot) $flag\n";
	print $fh_out "To Do: $todo\n";
	print $fh_out "Numbers: $num1 $num2 $num3\n\n";
    }
}

print STDERR "Retrieving Holiday bit patterns (but not dumped because it's tedious)\n";
# Holiday bit pattern.  This is kind of boring.  Each year's packet
# returns 72 bytes (6 bytes per month).  Each byte is a bit pattern for
# a week within a month indicating which days are holidays.  When the first
# week with a month does not start on Sunday, the bits are meaningless
# until the first day of the month.  Similar for the last week.  The 5th
# and 6th bytes are meaningless if the month doesn't span that many weeks.
for($iyear=0;$iyear<=20;$iyear++) { # 2000+$iyear is the year
    $packet=sendandreceive($p, pack("H6Cx501","0D260C",$iyear));
}
# Returns 7 bytes indicating which days of the week are repeating
# holidays.
$packet=sendandreceive($p, pack("H6x502","0D270C"));

print STDERR "Retrieving Notifications\n";
# Dump all the received notifications.
# First get a list of the Folders.
$folderlist[100] = "Unfiled";
for($ifolder=0;$ifolder<100;$ifolder++) {
  $packet=sendandreceive($p, pack("H6Cx501","0DEF0B",$ifolder));
  ($islot,$flag,$autofile,$notify,$icon,$foldername,$keyword) =
    unpack("x3CCCCCA16A16x466",$packet);
  if($flag > 0) {
    print $fh_out "Folder Slot: $ifolder($islot) $flag\n";
    print $fh_out "Folder Name: $foldername\n";
    print $fh_out "Attributes:";
    print $fh_out " Notify" if $notify;
    print $fh_out " EnvelopeIcon" if $icon;
    print $fh_out "\n";
    print $fh_out "Autofile: $keyword\n" if $autofile;
    print $fh_out "\n";
    $folderlist[$islot]= $foldername;
  }
}
# Now the messages
for($imessage=0;$imessage<200;$imessage++) { # 200 from  users manual
  $packet=sendandreceive($p, pack("H6Cx501","0DE10C",$imessage));
  ($islot,$type,$num1,$num2, $num3, $num4,$num5,$num6,$num7,$num8,$num9,$num10
   ,$num11,$messlen,$message,$year,$month,$day,$hour,$min,$seconds,$phonenumlen
   ,$phonenumber,$num12,$num13,$ifolder) = 
     unpack("x3CCCCCCCCCCCCCCA255xCCCCCCCA33Cx38CCx154",$packet);
  if($type > 0) {
    print $fh_out "Notification: $imessage($islot) Type: $type\n";
    print $fh_out "Begin Text:\n$message\nEnd Text:\n";
    print $fh_out "Phone Number: $phonenumber\n" if ($phonenumlen > 0);
    printf($fh_out "Date: %2.2d/%2.2d/%d %2.2d:%2.2d:%2.2d\n",
	   $month, $day, 2000+$year, $hour, $min, $seconds);
    print $fh_out "Folder: ";
    if($ifolder == 100) {
      print $fh_out "Unfiled($ifolder)\n";
    } else {
      print $fh_out $folderlist[$ifolder]."($ifolder)\n";
    }
    print $fh_out "Other Numbers: $num1 $num2 $num3 $num4 $num5 $num6 $num7 $num8".
      "$num9 $num10 $num11 $num12 $num13\n\n";
  }
}
# Get the Outgoing, Incoming and Missed call lists
print STDERR "Retrieving Call History\n";
@history = ("Outgoing","Incoming", "Missed");
for($ih=0;$ih<3;$ih++) {
  for($icall=0;$icall<20;$icall++) {
    $packet1=sendandreceive($p, pack("H2CH2Cx501","0D"
						,0x3d+$ih,"0C",$icall));
    $packet2=sendandreceive($p, pack("H2CH2Cx501","0D"
						,0x60+$ih,"0C",$icall));
    ($islot,$date,$phonenumlen,$phonenum,$name,$num1,$num2) =
      unpack("x3Cx2VCA48A16CCx431",$packet1);
    ($num3, $num4, $num5, $num6, $num7) =
      unpack("x4vCCCCx497",$packet2);
    print $fh_out $history[$ih]." call: $icall\n";
    print $fh_out "Phone Number: $phonenum\n";
    print $fh_out "Name: $name\n" if ($name);
    print $fh_out "Date: $date(".msd_date2string($date).")\n";
    print $fh_out "Other Numbers: $num1 $num2 $num3 $num4 $num5 $num6 $num7\n\n";
  }
}
#
# Get the big memory chunks
#
# 3c0f - 430f 4000 Bytes.  Sorting information.  Speed Dial.
#                          Lists of slots with email and web. addresses
#                          A Password?  List of secret numbers

print STDERR "Retrieving the 4000 byte buffer\n";
$bigchunk1 = "";
for($i=0x3c;$i<=0x43;$i++) {
  $packet=sendandreceive($p, pack("H2CH2x502","0D"
					     ,$i,"0F",$i));
  $bigchunk1 .= substr($packet,3,500);
}
# 460f - 470f 1000 Bytes Ringer and Picture Assignments
print STDERR "Retrieving the 1000 byte buffer (ringer/picture assignments)\n";
$bigchunk2 = "";
for($i=0x46;$i<=0x47;$i++) {
  $packet=sendandreceive($p, pack("H2CH2x502","0D"
					     ,$i,"0F",$i));
  $bigchunk2 .= substr($packet,3,500);
}
print STDERR "Retrieving the Caller ID phone number index (7000 byte buffer)\n";
# 500f - 5d0f 7000 Bytes Index of phone number to slots. For Caller ID
$bigchunk3 = "";
for($i=0x50;$i<=0x5d;$i++) {
  $packet=sendandreceive($p, pack("H2CH2x502","0D"
					     ,$i,"0F",$i));
  $bigchunk3 .= substr($packet,3,500);
}
@slotsused = unpack("C300x3700",$bigchunk1);
@secrets = unpack("x3634C300x66",$bigchunk1); # Up to 150 secret numbers listed
@speeddial = unpack("x2108v8x1876",$bigchunk1);
print $fh_out "Speed dial: ".join(" ", @speeddial)."\n";
($nslots1, $nslots2, $nemail, $nsecret) = unpack("x300vvvvx3692",$bigchunk1);

print $fh_out "Numbers from 4000 byte chunk: $nslots1($nslots2) Names,  $nemail Emails, $nsecret Secrets\n\n";

@ringers = unpack("C300x700",$bigchunk2);
@pictures = unpack("x300C300x400",$bigchunk2);
#print $fh_out join(" ", @ringers)."\n".join(" ",@pictures)."\n";

print STDERR "Retrieving the phone book\n";
# Read the phone book into an array
@phonebook = ();
for($iphoneslot=0;$iphoneslot<300;$iphoneslot++) {
    if($slotsused[$iphoneslot]) {
	$packet=sendandreceive($p, pack("H6vx500","0D280C",$iphoneslot));
	($islot,$islot2,$name,$homelen,$home,$worklen,$work,$mobilelen,$mobile
	 ,$pagerlen,$pager,$datalen,$data,$faxlen,$fax,$otherlen,$other
	 ,$emaillen,$email,$urllen,$url,$secret,$namelen)
	    = unpack("x3vvA16CA49CA49CA49CA49CA49CA49CA49CA49CA49CCx33",$packet);
	@phonenumbers = ($home,$work,$mobile,$pager,$data,$fax,$other);
	$phonebook[$islot]{name} = $name;
	$phonebook[$islot]{email} = $email if $email;
	$phonebook[$islot]{url} = $url if $url;
	$phonebook[$islot]{secret} = 1 if $secret;
	$phonebook[$islot]{ringer} = $ringers[$islot];
	$phonebook[$islot]{picture} = $pictures[$islot];
	for($itype=0;$itype<=$#phonenumbers;$itype++) {
	    $phonebook[$islot]{phonenumber}[$itype] = $phonenumbers[$itype];
	}
    }
}

# Dump the Speed Dial list
for($ispeed=0;$ispeed<=$#speeddial;$ispeed++) {
    $islot = $speeddial[$ispeed] & 0xFFF;
    $itype = ($speeddial[$ispeed] >> 12) & 0xF - 1;
    if($itype >= 0) {
	$speeddialkey = $ispeed+2;
	print $fh_out "Speed Dial Slot $speeddialkey: $phonebook[$islot]{name} ($phonetypes[$itype]) - $phonebook[$islot]{phonenumber}[$itype]\n\n";
	$phonebook[$islot]{speeddial}[$itype] = $speeddialkey;
    }
}
print STDERR "Retrieving the Voice Dial List\n";
# Read and dump the Voice Dial list
for($ivoiceslot=0;$ivoiceslot<30;$ivoiceslot++) {
    $packet=sendandreceive($p, pack("H6Cx501","0DED0B",$ivoiceslot));
    ($islot,$iflag,$iphoneslot,$itype) 
	    = unpack("x3CCx2vCx498",$packet);
    $itype--;
    if($iflag) {
	print $fh_out "Voice Dial Slot $islot: $phonebook[$iphoneslot]{name} ($phonetypes[$itype]) - $phonebook[$iphoneslot]{phonenumber}[$itype]\n\n";
	$phonebook[$iphoneslot]{voicedial}[$itype] = $ivoiceslot;
    }
}

# Dump the phone book.  If we move this to the end, we can
# flag numbers as being speed dial or voice dial
for($islot=0;$islot<=$#phonebook;$islot++) {
    if($phonebook[$islot]) {
	print $fh_out "Phonebook Slot: $islot\n";
	print $fh_out "Name: $phonebook[$islot]{name}\n";
	print $fh_out "Secret\n" if $phonebook[$islot]{secret};
	for($itype=0;$itype<7;$itype++) {
	    if($phonebook[$islot]{phonenumber}[$itype]) {
		print $fh_out $phonetypes[$itype].": "
		    .$phonebook[$islot]{phonenumber}[$itype];
		print $fh_out " (Speed Dial # $phonebook[$islot]{speeddial}[$itype])"
		    if($phonebook[$islot]{speeddial}[$itype]);
		print $fh_out " (Voice Dial Slot $phonebook[$islot]{voicedial}[$itype])"
		    if(defined $phonebook[$islot]{voicedial}[$itype]);
		$phonebook[$islot]{phonenumber}[$itype];
		print $fh_out "\n";
	    }
	}
	print $fh_out "Email: $phonebook[$islot]{email}\n" if
	    $phonebook[$islot]{email};
	print $fh_out "Url: $phonebook[$islot]{url}\n" if
	    $phonebook[$islot]{url};
	print $fh_out "Ringer: ".$phonebook[$islot]{ringer};
	print $fh_out " (".$ringernames[$phonebook[$islot]{ringer}].")"
	    if($ringernames[$phonebook[$islot]{ringer}]);
	print $fh_out "\n";
	print $fh_out "Picture: ".$phonebook[$islot]{picture}."\n";
	print $fh_out "\n";
    }
}

print STDERR "Retrieving the T9 buffer\n";
# Read what looks like to be some kind of T9 dictionary.  Bytes 4-13 are
# some numbers I don't understand yet.  Perhaps # of words, or pointers into
# the buffer.  Starting with byte 14, it seems to be a list of words.  Each
# word is preceeded by two bytes.  The first byte is some kind of bit pattern.
# Perhaps this byte indicates what this word is used in, phone book, calendar,
# internet forms...?   
# The next byte is a number one less than the length of the word.  Somewhere
# in the middle, the pattern breaks, but more byte/word sets follow.  Perhaps
# it is a round robin buffer, in which case the numbers at the beginning of 
# the packet probably matter.
# If write out a packet (Change the 0x0d to 0x0e, can we edit the dynamic
# T9 database?  I probably won't try.
#
$packet = sendandreceive($p, "\x0d\x0a\x0c"."\0"x502);
# This packet is huge.  Only the first 1024 bytes seem relevant.  The rest
# seem to be other views into the memory that one gets with 0DXX0F.
#
print $fh_out "T9 Packet:\n";
$len = length($packet);
$len=1024 if $len>1024;
$bufp = 0;
while($bufp < $len) {
    $line = substr($packet,$bufp,16);
    @chars = unpack("H2H2H2H2H2H2H2H2H2H2H2H2H2H2H2H2",$line);
    for($i=0;$i<16;$i++) {
	$chars[$i] = "  " if(not $chars[$i]);
    }
    printf $fh_out "%4d: ",$bufp;
    print $fh_out join(" ",@chars)," | ";;
    for($i=0;$i<16;$i++) {
	$byte = ord(substr($line,$i,1));
	if($byte >=32 && $byte<=126) {
	    print $fh_out chr($byte);
	} else {
	    print $fh_out " ";
	}
    }
    print $fh_out "\n";
    $bufp += 16;
}

packetdump($bigchunk1,2);
packetdump($bigchunk2,2);
packetdump($bigchunk3,2);

# Other things not read	that might be interesting
# 0dc20bNN NN = 0-2.  Number in security 
# 265200              Get Lock Code
# 0D040C ESN in Decimal form (11 digits)
# 0DC50B Some numbers.
# 0DD30B Some kind of sort order? (Calling history?)
# 0D3B00 Some kind of sort order? (Calling history?)
# 0DD50B Some kind of sort order? (Calling history?)
# 0DD10C ??  FE, 02, and 00s
# 0DD20C ??  Bunch of 7Fs
# 0DD30C ??  Bunch of 02s
# 0DD40C ??  More Fe, 02, and 00s
# 0DD50C ??  More Fe, 02, and 00s
# 0DD70C Ringer list
# 0DD80C Ringer list
# 0DD90C Loginname and Custom banner and bit to say which one.
# 0DB20000 Phone number of the phone?
# 0DB20001 Returns 0123456789
# 
# To read a packet, add commands like the following and run this script
# with hexdump mode on.
#
#$packet = sendandreceive($p, "\x26\x52\x00"."\0"x130);
#     \x26 packets should be 136 bytes including checksum and terminator
# or
#$packet=sendandreceive($p, pack("H6Cx501","0DC20B",$islot));
#
print STDERR "Resetting the phone\n";

# One thing that seems to help Kernel crashes is to comment out the following
# line, and then each time after using this script, disconnect the phone
# from the computer, power cycle the phone, and then plug it back in
# (If further use of this script is desired)
#$p->pulse_break_on(0); # Reset the phone

sanyo_close($p);       # Immediately close so we don't get Kernel Panics
exit;

sub sendandreceive {
# Send a packet and get back the response
    my $port=shift;
    my $packet=shift;
    my $reply;
    my $i;

    if($fh_dump) {
	packetdump($packet,0);
    }
    writeport($port, frame_hdlc($packet));
    $reply = datareply($port);

    if($fh_dump) {
	packetdump($reply,1);
    }
    $reply;

}
sub packetdump {
    my $packet=shift;
    my $direction=shift;
    my $i,$len,$bufp,@chars,$hexchar,$llen;
    my ($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst) = localtime(time);
    my %packettype = 
	(0x0c0a=>"t9",
	 0x0c23=>"event",
	 0x0c24=>"callalarm",
	 0x0c25=>"todo",
	 0x0c26=>"holidaybits",
	 0x0c27=>"weeklyholidaybits",
	 0x0c28=>"phonebookslot",
	 0x0c60=>"outgoingmisc",
	 0x0c61=>"incomingmisc",
	 0x0c62=>"missedmisc",
	 0x0ce1=>"message",
	 0x0c3b=>"ownerinfo",
	 0x0c3d=>"outgoing",
	 0x0c3e=>"incoming",
	 0x0c3f=>"missed",
	 0x0bef=>"foldername",
	 0x0bed=>"voicedial",
	 0x0bc2=>"securitynumber");
    my ($cmd1, $cmd2, $cmd3) = unpack("CCC",substr($packet,0,3));
    my $packdesc = "unknown";

    $len = length($packet);

    if($direction == 2) {
	if($len > 6900) {
	    $packdesc = "callerid";
	} elsif ($len > 3900) {
	    $packdesc = "pbsort";
	} else {
	    $packdesc = "ringerpic";
	}
    } elsif($cmd1==0x00) {
	$packdesc = "firmware";
    } elsif ($cmd1==0x26) {
	$packdesc = "phonenumber";
    } elsif ($cmd1==0x01) {
	$packdesc = "esn";
    } elsif ($cmd1==0x0d) {
	if($cmd3==0x0f) {
	    $packdesc = "bufferpart";
	} elsif($cmd3 == 0x0c || $cmd3 == 0x0b) {
	    my $cmd = $cmd3*256 + $cmd2;
	    $packdesc = $packettype{$cmd} if $packettype{$cmd};
	}
    }

    printf $fh_dump ("%2.2d:%2.2d:%2.2d.000 %s:",$hour,$min,$sec,$model);

    if($direction == 0) {
	printf $fh_dump ("sanyo phonebook request Data - %d bytes\n",$len);
	print $fh_dump "<\#! p_sanyo.${packdesc}request !\#>\n";
    } elsif($direction == 1) {
	printf $fh_dump ("sanyo phonebook response Data - %d bytes\n",$len-3);
	print $fh_dump "<\#! p_sanyo.${packdesc}response !\#>\n";
    } else {
	printf $fh_dump ("sanyo phonebook buffer Data - %d bytes\n",$len);
	print $fh_dump "<\#! p_sanyo.${packdesc}buffer !\#>\n";
    }

    if($direction == 1 && (substr($packet,$len-1,1) == "\x7e")) {
	$len -= 3;
    } # Don't show checksum and 7e
    $bufp = 0;
    while($bufp < $len) {
	$llen = $len-$bufp;
	$llen = 16 if($llen > 16);
	$line = substr($packet,$bufp,$llen);
	@chars = unpack("H2H2H2H2H2H2H2H2H2H2H2H2H2H2H2H2",$line);
	for($i=0;$i<16;$i++) {
	    $chars[$i] = "  " if(not $chars[$i]);
	}
	printf $fh_dump "%8.8x ",$bufp;
	print $fh_dump join(" ",@chars),"     ";;
	for($i=0;$i<16;$i++) {
	    if($bufp+$i < $len) {
		$byte = ord(substr($line,$i,1));
		if($byte >=32 && $byte<=126) {
		    print $fh_dump chr($byte);
		} else {
		    print $fh_dump ".";
		}
	    }
	}
	print $fh_dump "\n";
	$bufp += 16;
    }
    print $fh_dump "\n";
}

sub sanyo_datamode {
    local $port=shift;

#    writeport($port, "AT\$DCCMS?\r");
#    checkreply($port);
#    sleep(2);
    writeport($port, "AT\$QCDMG?\r");
    checkreply($port);
    sleep(2);

    $port->parity_enable(F);
    $port->baudrate(38400);
    $port->handshake("rts");

    $port->input; # Flush the input
}   
    

sub sanyo_open {
    local $phonedevice = shift;
    local $phonefd;

    $PortObj = new Device::SerialPort($phonedevice)
	|| die "Can't open phone \"$phonedevice\": $!\n";
    $PortObj->databits(8);
    $PortObj->parity_enable(T);
    $PortObj->parity("even");
    $PortObj->stopbits(1);
    $PortObj->handshake("rts");
    $PortObj->baudrate(19200);
    
    $PortObj->stty_opost(0);
    $PortObj->stty_echo(0);
    $PortObj->stty_echonl(0);
    $PortObj->stty_icanon(0);
    $PortObj->stty_isig(0);
#$PortObj->stty_iexten(0);csize;

#    print "Phone opened $PortObj\n";
    $PortObj;
}

sub sanyo_close {
    local $port=shift;

    if ( ref( $port)) {
	$port->close;
    }
    undef $port;
}

sub datareply {
    my $p = shift;
    my $now = time;
    my $reply="";
    my $i,$s,$len;

    while(1) {
	$s = $p->input;

	$len = length($s);
#	print "Length=$len\n";
	for($i=0;$i<$len;$i++) {
	    $hexchar = ord(substr($s,$i,1));
#	    printf("%2.2x",$hexchar);
	}
#	print "\n";


	$reply .= $s;
	last if ( $reply =~ m/\x7E/m);
	if ( time > ($now + 2)) {
	    $^W and warn "Timed out in datareply\n";
	    last;
	}
    }
    $reply=~s/\x7d\x5e/\x7e/gs;
    $reply=~s/\x7d\x5d/\x7d/gs;
    $reply;
}
    
sub checkreply {
  my $p = shift;
  my $reply = "";
  my $ok;
  my $now = time;

  while ( 1 ) {
	$s = $p->input;
	print "<<< $s\n" if $debug && $s;
	$reply .= $s;
	last if ( $reply =~ m/^(OK|ERROR)\r?$/m ); # wait for answer
	if ( time > ( $now + 3)) { # don't wait more than 2 seconds
	  $^W and warn "Timed out in checkreply\n";
	  last
	}
  }

  $ok = ( $reply =~ m/^OK\r?$/m ) ? 1 : 0;

  if ( wantarray ) {
	return ( $ok, $reply );
  } else {
	return $ok;
  }
}



sub writeport {
  my $p = shift;
  my $str = shift;
  my $len = length( $str ); # not used
  my $i;

# I couldn't seem to get the handshaking correct, but if
# the write is broken up into smaller write/drain pairs, then
# it seems to work OK.  100 bytes was too big, 50 worked, use 25
# for safety.

  print "$len >>> $str\n" if $debug;
  $i=0;
  while($i<$len) {
      $p->write(substr($str,$i,25));
      while ( !($p->write_drain)[0] ){print "Drain\n";};
      $i += 25;
  }
  print ">>> $str\n" if $debug;
}

# Compute FCS16 checksum and escape control characters 
sub frame_hdlc { # RFC 1662
    my $packet=shift;
    my @bytelist, $trialfcs;
    @bytelist = unpack("c*",$packet);
    $trialfcs = calcFcs16(0xffff, @bytelist) ^ 0xffff;
    push @bytelist, $trialfcs&0xff, ($trialfcs>>8) & 0xff;
    $trialfcs = calcFcs16(0xffff, @bytelist);
    if($trialfcs != 0xf0b8) {
	print "Bad FCS\n";
    }
    push @bytelist, 0x7e;
    $packet=pack("c*",@bytelist);
    $packet=~s/\x7d/\x7d\x5d/gs; # Escape the escape character
    $packet=~s/\x7f/\x7d\x5f/gs; # Escaping 7F seems to help
    $packet=~s/\x7e(.)/\x7d\x5e$1/gs; # Escape Frame terminator char (except at end)
    $packet;
}

sub calcFcs16 {
    my $fcs = shift;
    my @bytelist = @_;
    my $i;

    if(!@fcstab) {
	@fcstab =
	    (0x0000,0x1189,0x2312,0x329B,0x4624,0x57AD,0x6536,0x74BF,
	     0x8C48,0x9DC1,0xAF5A,0xBED3,0xCA6C,0xDBE5,0xE97E,0xF8F7,
	     0x1081,0x0108,0x3393,0x221A,0x56A5,0x472C,0x75B7,0x643E,
	     0x9CC9,0x8D40,0xBFDB,0xAE52,0xDAED,0xCB64,0xF9FF,0xE876,
	     0x2102,0x308B,0x0210,0x1399,0x6726,0x76AF,0x4434,0x55BD,
	     0xAD4A,0xBCC3,0x8E58,0x9FD1,0xEB6E,0xFAE7,0xC87C,0xD9F5,
	     0x3183,0x200A,0x1291,0x0318,0x77A7,0x662E,0x54B5,0x453C,
	     0xBDCB,0xAC42,0x9ED9,0x8F50,0xFBEF,0xEA66,0xD8FD,0xC974,
	     0x4204,0x538D,0x6116,0x709F,0x0420,0x15A9,0x2732,0x36BB,
	     0xCE4C,0xDFC5,0xED5E,0xFCD7,0x8868,0x99E1,0xAB7A,0xBAF3,
	     0x5285,0x430C,0x7197,0x601E,0x14A1,0x0528,0x37B3,0x263A,
	     0xDECD,0xCF44,0xFDDF,0xEC56,0x98E9,0x8960,0xBBFB,0xAA72,
	     0x6306,0x728F,0x4014,0x519D,0x2522,0x34AB,0x0630,0x17B9,
	     0xEF4E,0xFEC7,0xCC5C,0xDDD5,0xA96A,0xB8E3,0x8A78,0x9BF1,
	     0x7387,0x620E,0x5095,0x411C,0x35A3,0x242A,0x16B1,0x0738,
	     0xFFCF,0xEE46,0xDCDD,0xCD54,0xB9EB,0xA862,0x9AF9,0x8B70,
	     0x8408,0x9581,0xA71A,0xB693,0xC22C,0xD3A5,0xE13E,0xF0B7,
	     0x0840,0x19C9,0x2B52,0x3ADB,0x4E64,0x5FED,0x6D76,0x7CFF,
	     0x9489,0x8500,0xB79B,0xA612,0xD2AD,0xC324,0xF1BF,0xE036,
	     0x18C1,0x0948,0x3BD3,0x2A5A,0x5EE5,0x4F6C,0x7DF7,0x6C7E,
	     0xA50A,0xB483,0x8618,0x9791,0xE32E,0xF2A7,0xC03C,0xD1B5,
	     0x2942,0x38CB,0x0A50,0x1BD9,0x6F66,0x7EEF,0x4C74,0x5DFD,
	     0xB58B,0xA402,0x9699,0x8710,0xF3AF,0xE226,0xD0BD,0xC134,
	     0x39C3,0x284A,0x1AD1,0x0B58,0x7FE7,0x6E6E,0x5CF5,0x4D7C,
	     0xC60C,0xD785,0xE51E,0xF497,0x8028,0x91A1,0xA33A,0xB2B3,
	     0x4A44,0x5BCD,0x6956,0x78DF,0x0C60,0x1DE9,0x2F72,0x3EFB,
	     0xD68D,0xC704,0xF59F,0xE416,0x90A9,0x8120,0xB3BB,0xA232,
	     0x5AC5,0x4B4C,0x79D7,0x685E,0x1CE1,0x0D68,0x3FF3,0x2E7A,
	     0xE70E,0xF687,0xC41C,0xD595,0xA12A,0xB0A3,0x8238,0x93B1,
	     0x6B46,0x7ACF,0x4854,0x59DD,0x2D62,0x3CEB,0x0E70,0x1FF9,
	     0xF78F,0xE606,0xD49D,0xC514,0xB1AB,0xA022,0x92B9,0x8330,
	     0x7BC7,0x6A4E,0x58D5,0x495C,0x3DE3,0x2C6A,0x1EF1,0x0F78
	     );
    }

    for($i=0;$i<=$#bytelist;$i++) {
	$fcs = ($fcs >> 8) ^ $fcstab[($fcs^$bytelist[$i])&0xff];
    }
    $fcs;
}    

sub msd_date2string {
#
# Phone time is number of seconds since Jan 1, 1980.  Unix time is number
# of seconds since Jan 1, 1970.  To convert to unix time, add the number of
# seconds between the two dates, including the two leap days.  This seems to
# be not enough.  5 more days (Which happens to be the number of leap days
# between Jan 1, 1980 and Jan 1, 2000), need to be added to get the unix time.
# The resulting time is # of seconds since Jan 1, 1970 in whatever time zone
# the phone is operating in.  So the gmtime function must be used as it does
# do correction for timezone of the computer.
#
# The 5 day fudge factor is close to what is seen with the LG-VX4400 phone
# in the bitpim (http://bitpim.sourceforge.net/) project.  bitpim uses a
# fudge factor of 4 days and 17 hours.  Perhaps because they are comparing
# what the phone reports to a GMT clock which would the start of the epoch 5
# hours later for EST.
#
    local $secondssince1980 = shift;
    local @timeparts;
    @timeparts = gmtime($secondssince1980 + (365*10+2)*24*3600 + 5*24*3600);

    local $month=("January","February","March","April","May","June","July"
		  ,"August","September","October","November"
		  ,"December")[$timeparts[4]];
    sprintf("%s %d, %d %2.2d:%2.2d:%2.2d",$month,$timeparts[3]
	    ,(1900+$timeparts[5]),$timeparts[2],
	    $timeparts[1],$timeparts[0]);
}   


