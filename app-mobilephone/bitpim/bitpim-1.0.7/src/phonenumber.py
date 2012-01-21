### BITPIM
###
### Copyright (C) 2004 Roger Binns <rogerb@rogerbinns.com>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: phonenumber.py 4404 2007-09-23 03:27:27Z djpham $

"""Code for normalising and formatting phone numbers

This doesn't (yet) try to deal with international numbers.
The rule is that if the string contains 10 digits (with an optional
preceding one) then it is reduced to the 10 digits (all non-digit
characters removed, optional leading one removed).

If the string doesn't meet those criteria then it is passed through
as is.

For formatting, 10 digit strings are formatted in standard US
notation.  All others are left as is.
"""


import re

_notdigits=re.compile("[^0-9]*")
_tendigits=re.compile("^[0-9]{10}$")
_sevendigits=re.compile("^[0-9]{7}$")


def normalise(n):
    # this was meant to remove the long distance '1' prefix,
    # temporary disable it, will be done on a phone-by-phone case.
    return n
    nums="".join(re.split(_notdigits, n))
    if len(nums)==10:
        return nums
    if len(nums)==11 and nums[0]=="1":
        return nums[1:]
    return n

def format(n):
    if re.match(_tendigits, n) is not None:
        return "(%s) %s-%s" % (n[0:3], n[3:6], n[6:])
    elif re.match(_sevendigits, n) is not None:
        return "%s-%s" %(n[:3], n[3:])
    return n


if __name__=='__main__':
    nums=("011441223518046", "+1-123-456-7890", "(123) 456-7890", "0041-2702885504",
          "19175551212", "9175551212", "123 456 7890", "123 456 7890 ext 17")

    for n in nums:
        print "%s\n  norm: %s\n   fmt: %s\n" % (n, normalise(n), format(normalise(n)))
