#!/usr/bin/python2
# -*- coding: utf-8 -*-
import Tkconstants as TkC
import os
import subprocess
import sys
from Tkinter import Tk, Frame, Button, Label, PhotoImage
from math import sqrt, floor, ceil

import yaml


class FlatButton(Button):
    def __init__(self, master=None, cnf=None, **kw):
        Button.__init__(self, master, cnf, **kw)

        self.config(
            compound=TkC.TOP,
            relief=TkC.FLAT,
            bd=0,
            bg="#004E66",  # petrol blue - Button background
            fg="#BABFD1",  # light grey - text color
            activebackground="#006787",  # light petrol blue - Button background highlight level 2
            activeforeground="#ffffff",  # white - text highlight level 2
            highlightthickness=0 # button border size
        )

    def set_color(self, color):
        self.configure(
            bg=color,
            fg="#BABFD1", # light grey - main text color
            activebackground=color,
            activeforeground="#ffffff",  # white - text highlight level 1
        )


class oplauncher(Frame):
    framestack = []
    icons = {}
    path = ''
    lastinit = 0

    def __init__(self, parent):
        Frame.__init__(self, parent, background="#004E66") # petrol blue - main window background
        self.parent = parent
        self.pack(fill=TkC.BOTH, expand=1)

        self.path = os.path.dirname(os.path.realpath(sys.argv[0]))
        self.initialize()

    def initialize(self):
        """
        (re)load the the items from the yaml configuration and (re)init
        the whole menu system

        :return: None
        """
        with open(self.path + '/oplauncher.yaml', 'r') as f:
            doc = yaml.load(f)
        self.lastinit = os.path.getmtime(self.path + '/oplauncher.yaml')

        if len(self.framestack):
            self.destroy_all()
            self.destroy_top()

        self.show_items(doc)

    def has_config_changed(self):
        """
        Checks if the configuration has been changed since last loading

        :return: Boolean
        """
        return self.lastinit != os.path.getmtime(self.path + '/oplauncher.yaml')

    def show_items(self, items, upper=None):
        """
        Creates a new page on the stack, automatically adds a back button when there are
        pages on the stack already

        :param items: list the items to display
        :param upper: list previous levels' ids
        :return: None
        """
        if upper is None:
            upper = []
        num = 0

        # create a new frame
        wrap = Frame(self, bg="#1c1c1c") # verydark grey - window background & borders color

        if len(self.framestack):
            # when there were previous frames, hide the top one and add a back button for the new one
            self.hide_top()
            back = FlatButton(
                wrap,
                text='BACK',
                image=self.get_icon("arrow.left"),
                command=self.go_back,
            )
            back.set_color("#13293D")  # prussian blue - Back button color
            back.grid(row=0, column=0, padx=1, pady=1, sticky=TkC.W + TkC.E + TkC.N + TkC.S)
            num += 1

        # add the new frame to the stack and display it
        self.framestack.append(wrap)
        self.show_top()

        # calculate tile distribution
        allitems = len(items) + num
        rows = floor(sqrt(allitems))
        cols = ceil(allitems / rows)

        # make cells autoscale
        for x in range(int(cols)):
            wrap.columnconfigure(x, weight=1)
        for y in range(int(rows)):
            wrap.rowconfigure(y, weight=1)

        # display all given buttons
        for item in items:
            act = upper + [item['name']]

            if 'icon' in item:
                image = self.get_icon(item['icon'])
            else:
                image = self.get_icon('scrabble.' + item['label'][0:1].lower())

            btn = FlatButton(
                wrap,
                text=item['label'],
                image=image
            )

            if 'items' in item:
                # this is a deeper level
                btn.configure(command=lambda act=act, item=item: self.show_items(item['items'], act),
                              text=item['label'] + '…')
                btn.set_color("#2b5797")  # dark-blue - color for button with sub-level
            else:
                # this is an action
                btn.configure(command=lambda act=act: self.go_action(act), )

            if 'color' in item:
                btn.set_color(item['color'])

            # add buton to the grid
            btn.grid(
                row=int(floor(num / cols)),
                column=int(num % cols),
                padx=1,
                pady=1,
                sticky=TkC.W + TkC.E + TkC.N + TkC.S
            )
            num += 1

    def get_icon(self, name):
        """
        Loads the given icon and keeps a reference

        :param name: string
        :return:
        """
        if name in self.icons:
            return self.icons[name]

        ico = self.path + '/ico/' + name + '.png'
        if not os.path.isfile(ico):
            ico = self.path + '/ico/' + name + '.gif'
            if not os.path.isfile(ico):
                ico = self.path + '/ico/cancel.gif'

        self.icons[name] = PhotoImage(file=ico)
        return self.icons[name]

    def hide_top(self):
        """
        hide the top page
        :return:
        """
        self.framestack[len(self.framestack) - 1].pack_forget()

    def show_top(self):
        """
        show the top page
        :return:
        """
        self.framestack[len(self.framestack) - 1].pack(fill=TkC.BOTH, expand=1)

    def destroy_top(self):
        """
        destroy the top page
        :return:
        """
        self.framestack[len(self.framestack) - 1].destroy()
        self.framestack.pop()

    def destroy_all(self):
        """
        destroy all pages except the first aka. go back to start
        :return:
        """
        while len(self.framestack) > 1:
            self.destroy_top()

    def go_action(self, actions):
        """
        execute the action script
        :param actions:
        :return:
        """
        # hide the menu and show a "loading..." screen
        self.hide_top()
        delay = Frame(self, bg="#13293D") # loading message background color
        delay.pack(fill=TkC.BOTH, expand=1)
        label = Label(delay, text="Loading...", fg="white", bg="#13293D", font="Sans 30") # loading message text color
        label.pack(fill=TkC.BOTH, expand=1)
        self.parent.update()

        # excute shell script
        subprocess.call([self.path + '/oplauncher.sh'] + actions)

        # remove delay screen and show menu again
        delay.destroy()
        self.destroy_all()
        self.show_top()

    def go_back(self):
        """
        destroy the current frame and reshow the one below, except when the config has changed
        then reinitialize everything
        :return:
        """
        if self.has_config_changed():
            self.initialize()
        else:
            self.destroy_top()
            self.show_top()


def main():
    root = Tk()
    root.geometry("800x600") # window size
    root.wm_title('OP_Launcher')
    if len(sys.argv) > 1 and sys.argv[1] == 'fs':
        root.wm_attributes('-fullscreen', True)
    oplauncher(root)
    root.mainloop()


if __name__ == '__main__':
    main()
