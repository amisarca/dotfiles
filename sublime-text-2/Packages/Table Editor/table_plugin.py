# table_plugin.py - sublime plugins for pretty print text table

# Copyright (C) 2012  Free Software Foundation, Inc.

# Author: Valery Kocubinsky
# Package: SublimeTableEditor
# Homepage: https://github.com/vkocubinsky/SublimeTableEditor

# This file is part of SublimeTableEditor.

# SublimeTableEditor is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# SublimeTableEditor is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with SublimeTableEditor.  If not, see <http://www.gnu.org/licenses/>.

import sublime, sublime_plugin
import tablelib
import re



def find(text, sep, num):
    found = -1
    index = 0
    for i in range(num):
        found = text.find(sep,index)
        if index == -1:
            return -1
        index = found + 1
    return found


class AbstractTableCommand(sublime_plugin.TextCommand):

    def get_text(self, row):
        point = self.view.text_point(row, 0)
        region = self.view.line(point)
        text = self.view.substr(region)
        return text

    def get_full_text(self, row):
        point = self.view.text_point(row, 0)
        region = self.view.full_line(point)
        text = self.view.substr(region)
        return text

    def get_row(self, point):
        return self.view.rowcol(point)[0]

    def is_separator_row(self, row):
        return re.match(r"^\s*\|([\-]+\|)+$", self.get_text(row)) is not None

    def is_table_row(self, row):
        return re.match(r"^\s*\|", self.get_text(row)) is not None

    def get_field_num(self, row, col):
        field_num = self.get_text(row).count("|", 0, col)
        return field_num - 1

    def get_field_count(self, row):
        return self.get_text(row).count('|') - 1

    def get_last_buffer_row(self):
        return self.view.rowcol(self.view.size())[0]

    def get_field_default_point(self, row, field_num):
        text = self.get_text(row)
        i1 = find(text, '|', field_num +1)
        i2 = find(text, '|', field_num +2)
        match = re.compile(r"([^\s])\s+$").search(text, i1 + 1, i2)
        if match:
            return self.view.text_point(row,match.start(1) + 1)
        else:
            return self.view.text_point(row,i1 + 2)

    def get_last_table_row(self, row):
        last_table_row = row
        last_line = self.get_last_buffer_row()
        while (row <= last_line and self.is_table_row(row)):
            last_table_row = row
            row = row + 1
        return last_table_row

    def get_first_table_row(self, row):
        first_table_row = row
        while (row >= 0 and self.is_table_row(row)):
            first_table_row = row
            row = row - 1
        return first_table_row


class AbstractTableMultiSelect(AbstractTableCommand):

    def run(self, edit):
        self.run_before(edit)
        new_sels = []
        for sel in self.view.sel():
            if not self.is_table_row(self.get_row(sel.begin())):
                new_sels.append(sel)
                continue
            new_sel = self.run_one_sel(edit,sel)
            new_sels.append(new_sel)

        self.view.sel().clear()
        for sel in new_sels:
            self.view.sel().add(sel)
        self.run_after(edit)

    def run_before(self, edit):
        pass

    def run_after(self, edit):
        pass

    def run_one_sel(self,edit,sel):
        return sel


class TableAlignCommand(AbstractTableMultiSelect):
    """
    Command: table_align
    Key: ctrl+c, ctrl+c
    Re-align the table without change the current table field. Move cursor to begin of the current table field.
    """

    def run_one_sel(self, edit,sel):
        (sel_row, sel_col) = self.view.rowcol(sel.begin())
        first_table_row = self.get_first_table_row(self.get_row(sel.begin()))
        last_table_row = self.get_last_table_row(self.get_row(sel.begin()))

        begin_point = self.view.line(self.view.text_point(first_table_row,0)).begin()
        end_point = self.view.line(self.view.text_point(last_table_row,0)).end()

        table_region = sublime.Region(begin_point,end_point)
        text = self.view.substr(table_region)

        line_text = self.get_text(sel_row)
        sel_field_num = line_text.count("|", 0, sel_col) - 1
        i1 = line_text.rfind("|", 0, sel_col)
        if len(line_text[i1+1:].strip()) == 0 and sel_field_num > 0:
            sel_field_num = sel_field_num - 1
        self.view.replace(edit, table_region, tablelib.format_table(text))
        pt = self.get_field_default_point(sel_row, sel_field_num)
        return sublime.Region(pt,pt)


class TableNextField(AbstractTableMultiSelect):
    """
    Command: table_next_field.
    Key: tab
    Re-align the table, move to the next field. Creates a new row if necessary.
    """

    def run_before(self,edit):
        self.view.run_command("table_align")

    def run_one_sel(self, edit,sel):
        (sel_row, sel_col) = self.view.rowcol(sel.begin())
        field_num = self.get_field_num(sel_row, sel_col)
        last_table_row = self.get_last_table_row(sel_row)
        moved = False
        while True:
            if self.is_separator_row(sel_row) and sel_row < last_table_row:
                sel_row = sel_row + 1
                field_num = 0
                moved = True
                continue
            elif not self.is_separator_row(sel_row) and field_num + 1 < self.get_field_count(sel_row):
                if not moved:
                    field_num = field_num + 1
                break
            elif sel_row < last_table_row:
                if not moved:
                    field_num = 0
                    sel_row = sel_row + 1
                    if self.is_separator_row(sel_row):
                        moved = True
                        continue
                break
            else:
                if self.is_separator_row(sel_row) or not moved:
                    point = self.view.text_point(sel_row,0)
                    region = self.view.line(point)
                    text = self.view.substr(region)
                    i1 = find(text, '|', 1)
                    new_text = "\n" + text[:i1] + re.sub(r"[^\|]",' ',text[i1:])
                    self.view.insert(edit, region.end(),new_text)
                    field_num = 0
                    sel_row += 1
                break
        pt = self.get_field_default_point(sel_row, field_num)
        return sublime.Region(pt,pt)


class TablePreviousField(AbstractTableMultiSelect):
    """
    Command: table_previous_field
    Key: shift+tab
    Re-align, move to previous field.
    """

    def run_before(self,edit):
        self.view.run_command("table_align")

    def run_one_sel(self, edit,sel):
        (sel_row, sel_col) = self.view.rowcol(sel.begin())
        field_num = self.get_field_num(sel_row, sel_col)
        first_table_row = self.get_first_table_row(sel_row)
        moved = False
        while True:
            if self.is_separator_row(sel_row) and sel_row == first_table_row:
                field_num = 0
                break
            elif self.is_separator_row(sel_row) and sel_row > first_table_row:
                sel_row = sel_row - 1
                field_num = self.get_field_count(sel_row) - 1
                moved = True
                continue
            elif field_num > 0:
                if not moved:
                    field_num = field_num -1
                break
            elif sel_row > first_table_row:
                if not moved:
                    sel_row = sel_row - 1
                    field_num = self.get_field_count(sel_row) - 1
                    if self.is_separator_row(sel_row):
                        moved = True
                        continue
                break
            else:
                break
        pt = self.get_field_default_point(sel_row, field_num)
        return sublime.Region(pt,pt)


class TableNextRow(AbstractTableMultiSelect):
    """
    Command: table_next_row
    Key: alt + enter, enter
    Re-align the table and move down to next row. Creates a new row if necessary.
    """

    def run_before(self,edit):
        self.view.run_command("table_align")

    def run_one_sel(self, edit,sel):
        (sel_row, sel_col) = self.view.rowcol(sel.begin())
        field_num = self.get_field_num(sel_row, sel_col)
        if sel_row < self.get_last_table_row(sel_row):
            sel_row += 1
        else:
            line_region = self.view.line(sel)
            text = self.get_text(sel_row)
            i1 = find(text, '|', 1)
            new_text = "\n" + text[:i1] + re.sub(r"[^\|]",' ',text[i1:])
            self.view.insert(edit, line_region.end(),new_text)
            sel_row += 1
        pt = self.get_field_default_point(sel_row, field_num)
        return sublime.Region(pt,pt)


class TableMoveColumnLeft(AbstractTableMultiSelect):
    """
    Command: table_move_column_left
    Key: alt+left
    Move the current column right.
    """

    def run_before(self,edit):
        self.view.run_command("table_align")

    def run_one_sel(self, edit,sel):
        (sel_row, sel_col) = self.view.rowcol(sel.begin())
        field_num = self.get_field_num(sel_row, sel_col)
        if field_num == 0:
            return sel
        start_row = self.get_first_table_row(sel_row)
        end_row = self.get_last_table_row(sel_row)
        row = start_row
        while row <= end_row:
            text = self.get_text(row)
            i1 = find(text, '|', field_num + 0)
            i2 = find(text, '|', field_num + 1)
            i3 = find(text, '|', field_num + 2)
            new_text = text[0:i1] + text[i2:i3] + text[i1:i2] + text[i3:]
            self.view.replace(edit,
                            self.view.line(self.view.text_point(row, sel_col)),
                            new_text
                            )
            row += 1
        pt = self.get_field_default_point(sel_row, field_num - 1)
        return sublime.Region(pt,pt)



class TableMoveColumnRight(AbstractTableMultiSelect):
    """
    Command: table_move_column_right
    Key: alt+right
    Move the current column right.
    """

    def run_before(self,edit):
        self.view.run_command("table_align")

    def run_one_sel(self, edit,sel):
        (sel_row, sel_col) = self.view.rowcol(sel.begin())
        field_num = self.get_field_num(sel_row, sel_col)
        if field_num == self.get_field_count(sel_row) - 1:
            return sel
        first_table_row = self.get_first_table_row(sel_row)
        last_table_row = self.get_last_table_row(sel_row)
        row = first_table_row

        while row <= last_table_row:
            text = self.get_text(row)
            i1 = find(text, '|', field_num + 1)
            i2 = find(text, '|', field_num + 2)
            i3 = find(text, '|', field_num + 3)
            new_text = text[0:i1] + text[i2:i3] + text[i1:i2] + text[i3:]
            self.view.replace(edit,
                            self.view.line(self.view.text_point(row, sel_col)),
                            new_text
                            )
            row += 1
        pt = self.get_field_default_point(sel_row, field_num + 1)
        return sublime.Region(pt,pt)



class TableDeleteColumn(AbstractTableMultiSelect):
    """
    Command: (table_delete_column)
    Key: alt+shift+left
    Kill the current column.
    """

    def run_before(self,edit):
        self.view.run_command("table_align")

    def run_one_sel(self, edit,sel):
        (sel_row, sel_col) = self.view.rowcol(sel.begin())
        field_num = self.get_field_num(sel_row, sel_col)

        first_table_row = self.get_first_table_row(sel_row)
        last_table_row = self.get_last_table_row(sel_row)
        row = first_table_row
        field_count = self.get_field_count(sel_row)
        while row <= last_table_row:
            text = self.get_text(row)
            i1 = find(text, '|', field_num + 1)
            i2 = find(text, '|', field_num + 2)
            if field_count > 1:
                self.view.replace(edit,
                                self.view.line(self.view.text_point(row, sel_col)),
                                text[0:i1] + text[i2:])
            else:
                self.view.replace(edit,
                                self.view.line(self.view.text_point(row, sel_col)),
                                text[0:i1] + text[i2+1:])

            row += 1
        if field_num == self.get_field_count(sel_row):
            field_num -= 1
        pt = self.get_field_default_point(sel_row, field_num)
        return sublime.Region(pt,pt)


class TableInsertColumn(AbstractTableMultiSelect):
    """
    Command: table_insert_column
    Keys: alt+shift+right
    Insert a new column to the left of the cursor position.
    """

    def run_before(self,edit):
        self.view.run_command("table_align")

    def run_one_sel(self, edit,sel):
        (sel_row, sel_col) = self.view.rowcol(sel.begin())
        field_num = self.get_field_num(sel_row, sel_col)

        first_table_row = self.get_first_table_row(sel_row)
        last_table_row = self.get_last_table_row(sel_row)
        row = first_table_row
        field_count = self.get_field_count(sel_row)
        while row <= last_table_row:
            text = self.get_text(row)
            cell = "   "
            if self.is_separator_row(row):
                cell = "---"
            i1 = find(text, '|', field_num + 1)
            self.view.replace(edit,
                            self.view.line(self.view.text_point(row, sel_col)),
                            text[0:i1] + "|" + cell + text[i1:])

            row += 1
        pt = self.get_field_default_point(sel_row, field_num)
        return sublime.Region(pt,pt)


class TableKillRow(AbstractTableMultiSelect):
    """
    Command: table_kill_row
    Key : alt+shift+up
    Kill the current row or horizontal line.
    """

    def run_before(self,edit):
        self.view.run_command("table_align")

    def run_one_sel(self, edit,sel):
        (sel_row, sel_col) = self.view.rowcol(sel.begin())
        self.view.erase(edit, self.view.full_line(sel))
        if sel_row == self.get_last_table_row(sel_row):
            sel_row = sel_row - 1
        if not self.is_table_row(sel_row):
            sel_col = 0
        pt = self.view.text_point(sel_row, sel_col)
        return sublime.Region(pt,pt)

class TableInsertRow(AbstractTableMultiSelect):
    """
    Command: table_insert_row
    Key: alt+shift+down
    Insert a new row above the current row.
    """

    def run_before(self,edit):
        self.view.run_command("table_align")

    def run_one_sel(self, edit,sel):
        (sel_row, sel_col) = self.view.rowcol(sel.begin())
        line_region = self.view.line(sel)
        text = self.view.substr(line_region)
        i1 = find(text, '|', 1)
        new_text = text[:i1] + re.sub(r"[^\|]",' ',text[i1:]) + "\n"
        self.view.insert(edit, line_region.begin(),new_text)
        pt = self.view.text_point(sel_row, sel_col)
        return sublime.Region(pt,pt)




class TableMoveRowUp(AbstractTableCommand):
    """
    Command: table_move_row_up
    Key: alt+up
    Move the current row up.
    """
    def run(self, edit):
        for sel in self.view.sel():
            row = self.get_row(sel.begin())
            if row - 1 >= self.get_first_table_row(row):
                self.view.run_command("swap_line_up")


class TableMoveRowDown(AbstractTableCommand):
    """
    Command: table_move_row_down
    Key: alt+down
    Move the current row down.
    """

    def run(self, edit):
        for sel in self.view.sel():
            row = self.get_row(sel.begin())
            if row + 1 <=  self.get_last_table_row(row):
                self.view.run_command("swap_line_down")


