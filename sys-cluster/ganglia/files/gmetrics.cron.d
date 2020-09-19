SHELL=/bin/bash
PATH=/sbin:/bin:/usr/sbin:/usr/bin
MAILTO=root

*/10 * * * * root /bin/bash /usr/bin/string-metrics.sh > /dev/null 2>&1
