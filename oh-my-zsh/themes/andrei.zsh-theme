PROMPT='%{$fg_bold[red]%}➜  %{$fg[cyan]%}%~ %{$fg_bold[blue]%}$(virtualenv_info)$(git_prompt_info)%{$fg_bold[blue]%} % %{$reset_color%}'

ZSH_THEME_GIT_PROMPT_PREFIX="[%{$fg[red]%}"
ZSH_THEME_GIT_PROMPT_SUFFIX="%{$reset_color%}"
ZSH_THEME_GIT_PROMPT_DIRTY="%{$fg[blue]%}] %{$fg[yellow]%}✗%{$reset_color%}"
ZSH_THEME_GIT_PROMPT_CLEAN="%{$fg[blue]%}]"

function virtualenv_info {
    [ $VIRTUAL_ENV ] && echo "%{${fg[white]}%}(%{${fg[white]}%}env: %{${fg[green]}%}`basename \"$VIRTUAL_ENV\"`%{${fg[white]}%}) "
}
