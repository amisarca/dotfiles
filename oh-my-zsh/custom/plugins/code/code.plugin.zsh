c() { cd ~/code/$1; }
_c() { _files -W ~/code -/; }
compdef _c c

cr() { cd ~/code/rails/$1; }
_cr() { _files -W ~/code/rails -/; }
compdef _cr cr
