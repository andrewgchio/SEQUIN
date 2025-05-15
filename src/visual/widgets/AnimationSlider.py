# AnimationControls.py

import tkinter as tk
import customtkinter as ctk

import controller

Controller = lambda : controller.Controller()

class AnimationSlider(ctk.CTkFrame):

    def __init__(self, master):
        super().__init__(master, fg_color='transparent')

        self.is_empty = True

        self.slider = ctk.CTkSlider(self, command=Controller().slider_move)
        self.slider.grid(row=0) # because 4 buttons later

        self.slider_label = tk.StringVar(self, value='Failed 0 / 0')
        ctk.CTkLabel(self, textvariable=self.slider_label).grid(row=1)
    
    def get(self):
        return int(self.slider.get())
    
    def update(self, value=None, to=None):
        if to is not None:
            self.is_empty = (to == 0)
            self.slider.configure(
                to=to+self.is_empty,
                number_of_steps=to+self.is_empty)

        if value is not None:
            self.slider.set(value)

        n_failed = self.slider.cget('to') if not self.is_empty else 0
        self.slider_label.set(f'Failed {int(self.slider.get())} / {n_failed}')

    def slide_last(self):
        self.update(value=self.slider.cget('to'), to=self.slider.cget('to'))
    