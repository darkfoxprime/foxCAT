
BEGIN {rn=0}
{gsub(/[ \t][ \t]*/, " "); sub(/ ->.*$/, "");}
$1 == "|"  {rn += 1; $1 = "<-"; print "[" rn "]",rule,$0}
$2 == "<-" {rn += 1; rule=$1; if (rn==1) {print "[0] start <- " rule} print "[" rn "]",$0}
