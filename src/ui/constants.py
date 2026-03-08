"""UI tooltips and constants."""

# Format description table
FORMAT_TOOLTIPTEXT = """
Form		|Description					|Example
%a		|Weekday, short version					|Wed
%A		|Weekday, full version					|Wednesday
%w		|Weekday as a number 0-6, 0 is Sunday			|3
%d		|Day of month 01-31					|31
%b		|Month name, short version				|Dec
%B		|Month name, full version					|December
%m		|Month as a number 01-12				|12
%y		|Year, short version, without century		|18
%Y		|Year, full version						|2018
%H		|Hour 00-23						|17
%I		|Hour 00-12						|05
%p		|AM/PM						|PM
%M		|Minute 00-59					|41
%S		|Second 00-59					|08
%f		|Microsecond 000000-999999		|548513
%z		|UTC offset						|+0100
%Z		|Timezone						|CST
%j		|Day number of year 001-366			|365
%U		|Week num of year, Sunday as first day of week, 00-053	|52
%W		|Week num of year, Monday as first day of week, 00-53	|52
%c		|Local ver of date and time		|Mon Dec 31 17:41:00 2018
%C		|Century						|20
%x		|Local version of date				|12/31/18
%X		|Local version of time				|17:41:00
%%		|A % character					|%
%G		|ISO 8601 year					|2018
%u		|ISO 8601 weekday (1-7)				|1
%V		|ISO 8601 weeknumber (01-53)			|01
"""

# Unknown data tooltip
UNKNOWN_TOOLTIP = """If Checked - Any image or video without an associated date
will be moved to a dedicated folder name ".unknown"

If Unchecked - The aforementioned images or videos will not
be moved/copied and will be LEFT AS IS (without regard to if the user
has Chosen to move or to Copy the images in the folder)"""

# Valid characters for date format
INVALID_FORMAT_CHARS = ["/", ">", "<", ":", '"', "\\", "|", "?", "*"]

# Invalid error code for Windows
ERROR_INVALID_NAME = 123
