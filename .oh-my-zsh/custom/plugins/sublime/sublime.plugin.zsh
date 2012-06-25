st() {
  if [[ $1 == '-v' || $1 == '--version' || $1 == '-h' || $1 == '--help' ]]; then
    sublime $*
  else
    (sublime $* &) > /dev/null 2>&1;
  fi
}
alias stt='st .'
