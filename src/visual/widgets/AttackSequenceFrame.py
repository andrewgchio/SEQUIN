# AttackSequenceBlock.py

import re
import tkinter as tk
import customtkinter as ctk

from utils import get_atk_str, get_atk_eid

import model

# MVC Utility functions
Model = lambda : model.Model()

class AttackSequenceFrame(ctk.CTkFrame):

    def __init__(self, master, title, titlefont=('TkDefaultFont', 12)):
        super().__init__(master)

        if type(title) is str:
            ctk.CTkLabel(self, text=title, font=titlefont).grid(row=0)
        elif type(title) is tk.StringVar:
            ctk.CTkLabel(self, textvariable=title, font=titlefont).grid(row=0)

        self.seq_frame = ctk.CTkScrollableFrame(self)
        self.seq_frame.grid(row=1, padx=10)

        self.labels = []
    
    def __len__(self):
        return len(self.labels)
    
    def __bool__(self):
        return bool(self.labels)
    
    def __iter__(self):
        return iter(self.labels)
    
    def __getitem__(self, i):
        return self.labels[i]

    def add_entry(self, eid, status=None):
        i = len(self)

        br_label = ctk.CTkLabel(self.seq_frame, text=f'{i+1}. ') 
        br_label.grid(row=i, column=0, padx=5, sticky=tk.W)

        eid_label = ctk.CTkLabel(self.seq_frame, text=get_atk_str(eid, Model()))
        eid_label.grid(row=i, column=1, sticky=tk.W)

        status_label = ctk.CTkLabel(self.seq_frame, text=status)
        status_label.grid(row=i, column=2, sticky=tk.W)
        
        self.labels.append((eid,br_label,eid_label,status_label))

    def remove_entry(self):
        _,br_label,eid_label,status_label = self.labels[-1]
        br_label.destroy()
        eid_label.destroy()
        status_label.destroy()
        self.labels.pop()

    def clear(self):
        for eid,br_label,eid_label,status_label in self.labels:
            br_label.destroy()
            eid_label.destroy()
            status_label.destroy()
        self.labels.clear()
