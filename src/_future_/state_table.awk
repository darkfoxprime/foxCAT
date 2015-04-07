
/^State / {
  state=int(substr($2, 1, length($2)-1));
}
$2 == "shift" || $2 == "goto" || $2 == "reduce" || $2 == "accept" {
  if (!($1 in tokens)) {
    tokens[$1] = $1;
  }
  actions[state,$1] = $NF;
}
END {
  nt=asorti(tokens);
  printf("State#");
  for (i=1; i<=nt; i+=1) {
    printf("  %-6s", substr(tokens[i], 1, 6));
  }
  print "";
  for (s=0; s<=state; s+=1) {
    printf("%6d", s);
    for (i=1; i<=nt; i+=1) {
      if ( (s,tokens[i]) in actions) {
        a=actions[s,tokens[i]];
      } else {
        a = "--";
      }
      printf("  %-6s", a);
    }
    print ""
  }
}
