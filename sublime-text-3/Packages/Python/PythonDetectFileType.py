import sublime, sublime_plugin
import os

class PythonDetectFileTypeCommand(sublime_plugin.EventListener):
    """ Detects current file type if the file's extension isn't conclusive """
    """ Modified for Python and Sublime Text 3 """
    """ Original pastie here: http://pastie.org/private/kz8gtts0cjcvkec0d4quqa """

    def on_load(self, view):
        filename = view.file_name()
        if not filename: # buffer has never been saved
            return

        name = os.path.basename(filename.lower())
        if name == "build":
          set_syntax(view, "Python", "Python")
        elif name[-2:] == "py":
          set_syntax(view, "Python", "Python")


def set_syntax(view, syntax, path=None):
    if path is None:
        path = syntax
    view.settings().set('syntax', 'Packages/'+ path + '/' + syntax + '.tmLanguage')
    print("Switched syntax to: " + syntax)