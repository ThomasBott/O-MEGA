# -*- coding: cp1252 -*-
import os
import zipfile
import json
import sys
import wx
from omegalib import *

#exporter
#v1.1501


class GUI(wx.Frame):

    def __init__(self, parent, title, style):
        super(GUI, self).__init__(parent, title=title, style=style, size=(280,500))
        self.InitData()
        self.InitUI()
        self.Centre()
        self.Show()
        
    def InitData(self):
        self.omegaLocation = getOmegaHome()
        if not self.omegaLocation:
            msgBox("Exporter","Could not read O-MEGA Configuration Directory!","error")
            sys.exit(-1)
        self.installedTemplates = getInstalledTemplatesWithoutParentAndSystemTemplates()
        self.installedExtensions = getInstalledExtensionsWithoutSystemExtensions()
        
    def InitUI(self):
        self.panel = wx.Panel(self, -1)
        self.tList = wx.ListBox(self.panel, -1, (10,30), (245,200), [str(x) for x in self.installedTemplates], wx.LB_NEEDED_SB)
        wx.StaticText(self.panel, -1, pos=(10,10), size=(50,20), label="Installed:", style=wx.wx.ALIGN_LEFT)
        selectButton = wx.Button(self.panel, label='Choose', pos=(10, 240), size=(120,30))
        selectButton.Bind(wx.EVT_BUTTON, self.selectTemplate)
        deleteButton = wx.Button(self.panel, label='Delete', pos=(135, 240), size=(120,30))
        deleteButton.Bind(wx.EVT_BUTTON, self.deleteTemplate)
        self.eList = wx.ListBox(self.panel, -1, (10,280), (245,140), [], wx.LB_NEEDED_SB)
        self.exportButton = wx.Button(self.panel, label='Next', pos=(10, 430), size=(245,30))
        self.exportButton.Bind(wx.EVT_BUTTON, self.chooseExtensions)
        
    def selectTemplate(self, e):
        if self.tList.GetSelection() != -1:
            #print self.tList.GetSelection()
            self.eList.AppendAndEnsureVisible(self.tList.GetString(self.tList.GetSelection()))
            self.tList.Delete(self.tList.GetSelection())
            
    def deleteTemplate(self, e):
        if self.eList.GetSelection() != -1:
            #print self.eList.GetSelection()
            self.tList.AppendAndEnsureVisible(self.eList.GetString(self.eList.GetSelection()))
            self.eList.Delete(self.eList.GetSelection())
            
    def chooseExtensions(self, e):
        self.childList = []
        self.exportList = []
        for selectedName in self.eList.GetStrings():
            objTemplate = self.getTemplateFromLabel(selectedName)
            self.exportList.append(objTemplate)
            self.childList.extend(getChildTemplates(objTemplate.name))
            self.exportList.extend(getChildTemplates(objTemplate.name))
        if self.childList:
            message = "Some Child Templates have been automatically added:\n\n"
            for entry in self.childList:
                message += str(entry)+"\n"
            msgBox("Exporter",message)
        #load extensions into gui
        self.tList.Clear()
        self.eList.Clear()
        #load extensions from templates
        self.selectedExtensions = []
        self.selectedExtensions2 = []
        self.filteredExtensions = []
        for template in self.exportList:
            extension = getExtensionForTemplate(template)
            #print "Extension "+str(extension) + " : "+str(extension.json)
            if extension:
                if extension.name not in self.selectedExtensions2 and extension.name not in SYSTEM_EXTENSIONS:
                    self.selectedExtensions.append(extension)
                    self.selectedExtensions2.append(extension.name)
        #generate a filtered list and only add extensions which are not already selected via template
        for extensionEntry in self.installedExtensions:
            if extensionEntry.name not in self.selectedExtensions2:
                self.filteredExtensions.append(extensionEntry)
        if len(self.filteredExtensions)>0:
            self.tList.InsertItems([str(x) for x in self.filteredExtensions], 0)
        if len(self.selectedExtensions)>0:
            self.eList.InsertItems([str(x) for x in self.selectedExtensions], 0)
        self.exportButton.SetLabel("Export")
        self.exportButton.Bind(wx.EVT_BUTTON, self.exportTemplate)
        
    def exportTemplate(self, e):
        #get additional extensions
        self.extensionList = []
        for selectedName in self.eList.GetStrings():
            objExtension = self.getExtensionFromLabel(selectedName)
            #print objExtension
            self.extensionList.append(objExtension)
        #start exporting
        dlg = wx.FileDialog(None, "Choose the export location and file name", "C:\\", "", "*.omg", wx.SAVE)
        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetFilename()
            dirname = dlg.GetDirectory()
            #print filename
            #print dirname
            dlg.Destroy()
            filename = os.path.join(dirname, filename)
            #print filename
            if filename and exportTemplate(filename, self.exportList, self.extensionList):
                msgBox("Exporter","Export successfull!")
            else:
                msgBox("Exporter","Export failed!","error")
        wx.GetApp().ExitMainLoop()
            
    def getTemplateFromLabel(self, label):
        for entry in self.installedTemplates:
            if str(entry) == label:
                return entry
        return None
        
    def getExtensionFromLabel(self, label):
        for entry in self.installedExtensions:
            if str(entry) == label:
                return entry

app = wx.App()
gui = GUI(None, "OMG Exporter", style=wx.DEFAULT_FRAME_STYLE ^ wx.RESIZE_BORDER)
app.MainLoop()
