# -*- coding: cp1252 -*-
from omegalib import *

#updater
#v2.0


class GUI(wx.Frame):

    def __init__(self, parent, title, style):
        super(GUI, self).__init__(parent, title=title, style=style, size=(280,500))
        self.InitData()
        self.InitUI()
        self.Centre()
        self.Show()
        
    def InitData(self):
        self.omegaLocation = getOmegaHome()
        if self.omegaLocation:
            updateConfigFiles1()
        
    def InitUI(self):
        self.panel = wx.Panel(self, -1)
       

app = wx.App()
gui = GUI(None, "OMG Exporter", style=wx.DEFAULT_FRAME_STYLE ^ wx.RESIZE_BORDER)
app.MainLoop()
