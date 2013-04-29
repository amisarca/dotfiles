st() {
  if [[ $1 == '-v' || $1 == '--version' || $1 == '-h' || $1 == '--help' ]]; then
    sublime-text-2 $*
  else
    (sublime-text-2 $* &) > /dev/null 2>&1;
  fi
}
alias stt='st .'
