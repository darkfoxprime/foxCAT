
BEGIN {
  rn=0
}
{
  gsub(/[ \t][ \t]*/, " ");
  action="";
}
/ -> / {
  action=$0;
  sub(/^.* -> */, "", action);
  action = "-> " action;
  sub(/ ->.*$/, "");
}
$1 == "|" {
  rn += 1;
  $1 = "<-";
# print "[" rn "]",rule,$0,action;
  print rule,$0,action;
}
$2 == "<-" {
  rn += 1;
  rule=$1;
# if (rn==1) {
#   print "[0] start <- " rule;
# }
# print "[" rn "]",$0,action;
  print $0,action;
}
