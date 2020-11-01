# -*- coding: utf-8 -*-
#
# plugins/O-MEGA/__init__.py
#
# This file is a plugin for EventGhost.

import eg
import wx
import os
import pythoncom
import _winreg
import re
import json
import codecs
import time
import subprocess
import asynchat
import asyncore
import random
import socket
import xml.etree.ElementTree as ET
from hashlib import md5, sha1
from threading import Timer, Event, Thread, Lock
from eg.WinApi.Dynamic import (
# functions:
    byref, cast,
    SetEvent,
    CreateEvent,
    PulseEvent,
    CreateFile,
    CloseHandle,
    MsgWaitForMultipleObjects,
    ReadDirectoryChangesW,
# extensions:
    c_byte,
    DWORD,
    HANDLE,
    OVERLAPPED,
    LPOVERLAPPED_COMPLETION_ROUTINE,
# constants:
    INFINITE,
    INVALID_HANDLE_VALUE,
    QS_ALLINPUT,
    WAIT_OBJECT_0,
    OPEN_EXISTING,
    FILE_SHARE_READ,
    FILE_SHARE_WRITE,
    FILE_FLAG_BACKUP_SEMANTICS,
    FILE_FLAG_OVERLAPPED,
    FILE_NOTIFY_CHANGE_FILE_NAME,
    FILE_NOTIFY_CHANGE_DIR_NAME,
    FILE_LIST_DIRECTORY,
)

from win32api import LoadLibrary, LoadString, GetVolumeInformation
from win32com.shell import shell
from win32file import GetFileAttributesW, GetLogicalDrives
from fnmatch import fnmatch
from urllib2 import unquote, quote, urlopen, Request as urlRequest
from win32clipboard import OpenClipboard, GetClipboardData, SetClipboardData, SetClipboardText, CloseClipboard, EnumClipboardFormats, GetClipboardFormatName, EmptyClipboard
from uuid import getnode
from eg.WinApi.Dynamic import GetCursorPos, POINT
from win32com.client import Dispatch
from inspect import getsourcelines
#from copy import copy
from HTMLParser import HTMLParser

from ssl import wrap_socket, CERT_NONE
from posixpath import splitext, normpath
from urllib import unquote_plus
from httplib import HTTPResponse
from jinja2 import BaseLoader, TemplateNotFound, Environment
from base64 import b64encode, encodestring as b64_encStr
from BaseHTTPServer import HTTPServer
from SimpleHTTPServer import SimpleHTTPRequestHandler
from SocketServer import ThreadingMixIn
from traceback import print_exc

eg.RegisterPlugin(
    name = "O-MEGA",
    author = "Sem;colon",
    version = "0.5.9",
    kind = "other",
    description = u"""Home Automation Web-interface for EventGhost""",
    createMacrosOnAdd = False,
    canMultiLoad = False,
    guid = '{FA12138C-B53B-48F4-8F3C-542F92033CB5}',
)

class Text:
    noAssoc = 'Error: No application is associated with the "%s" file type for operation "Open" !'
    accDeni = 'The file or folder "%s" can not be deleted. Access denied.'
    myComp  = "My computer"
    tcpBox  = "TCP connection parameters"
    port    = "TCP/IP port"
    password= "Password"
    pyComm  = "Python command"
    pyOComm  = "Python/O-MEGA command"
    importB = "Save config and Import"
    exportB = "Export"
    importExportBox = "Templates and Extensions"
    targetState = "Target State"
    targetType = "Target Type"
    variable= "Variable"
    value   = "Value"
    optional= "Optional"
    targetDeviceId = "Target Device ID"
    targetButtonId = "Target Button ID"
    targetInterfaceId = "Target Interface ID"
    state   = "State"
    webAuthUsername = "Username:"
    webAuthPassword = "Password:"
    webCertfile = "SSL certificate"
    webKeyfile = "SSL private key"
    sslTool = "Select the appropriate file if you want to use a secure "\
"protocol (https).\n If this field remains blank, the server will use an "\
"unsecure protocol (http). "
    cMask = (
        "crt files (*.crt)|*.crt"
        "|pem files (*.pem)|*.pem"
        "|All files (*.*)|*.*"
    )
    kMask = (
        "key files (*.key)|*.key"
        "|pem files (*.pem)|*.pem"
        "|All files (*.*)|*.*"
    )
    webBox = "Webserver parameters"
    parsing = "disable parsing"
    simplify = "Simplify output by removeing the #"
    autorunTimeout = "Scene Autorun Startup Delay (sec.)"
    purgeBackupDays = "Automatically delete backups after X days"
    miscSettings = "Other Settings"
    
    started = "O-MEGA: Webserver started as %s on port %i"
    secur = (
        "secured (https://)",
        "unsecured (http://)",
    )
    stopped = "O-MEGA: Webserver on port %i stopped"

    
class PrerequisiteError(Exception):
    def __init__(self, plugins):
        self.value = plugins
    def __str__(self):
        return "The following plugins are missing in your configuration: " + ",".join(self.value)

        
class OMEGA(eg.PluginBase):
    menuDlg = {}
    instances = []
    text = Text
    lastEnduringEvent = None


    def MyComputer(self):
        mc_reg = None
        try:
            mc_reg = _winreg.OpenKey(
                _winreg.HKEY_CLASSES_ROOT,
                "CLSID\\{20D04FE0-3AEA-1069-A2D8-08002B30309D}"
            )
            value, type = _winreg.QueryValueEx(mc_reg, "LocalizedString")
            dll = os.path.split(value.split(",")[0][1:])[1]
            index = -1*int(value.split(",")[1])
            myComputer = LoadString(LoadLibrary(dll), index)
        except:
            myComputer = self.text.myComp
        if mc_reg:
            _winreg.CloseKey(mc_reg)
        return myComputer
        
        
    def __init__(self):
        global MY_COMPUTER
        MY_COMPUTER = self.MyComputer()
        self.configDir=eg.configDir+u'\\plugins\\O-MEGA'
        self.TCPserver = None
        self.pluginServer = False
        self.serverOnline = False
        self.registeredWebFunctions={}
        self.uml=HTMLParser()
        if self.readFromReg("server")=="1":
            self.pluginServer = True
            #self.actionValues={}
            import omegalib
            import defaultConfig
            socket.setdefaulttimeout(5)
            self.RegisterWebFunction(self.dataUpdate,"dataUpdate")
            self.RegisterWebFunction(self.dataUpdate2,"dataUpdate2")
            self.RegisterWebFunction(self.unregisterClient,"unregisterClient")
            self.RegisterWebFunction(self.uniUnregister,"uniUnregister")
            self.RegisterWebFunction(self.uniUpdate,"uniUpdate")
            self.RegisterWebFunction(self.sceneRemove,"sceneRemove")
            self.RegisterWebFunction(self.getFilesForDropdown,"getFilesForDropdown")
            self.RegisterWebFunction(self.sceneSaveActions,"sceneSaveActions")
            self.RegisterWebFunction(self.saveUserSettings,"saveUserSettings")
            self.RegisterWebFunction(self.getUserSettings,"getUserSettings")
            self.RegisterWebFunction(self.sceneCheckCondition,"sceneCheckCondition")
            self.RegisterWebFunction(self.getSceneActions,"getSceneActions")
            self.RegisterWebFunction(self.saveActionEventsFor,"saveActionEventsFor")
            self.RegisterWebFunction(self.removeActionEventsFor,"removeActionEventsFor")
            self.RegisterWebFunction(self.loadActionEventsFor,"loadActionEventsFor")
            self.RegisterWebFunction(self.sceneRename,"sceneRename")
            self.RegisterWebFunction(self.sceneMove,"sceneMove")
            self.RegisterWebFunction(self.sceneSetting,"sceneSetting")
            self.RegisterWebFunction(self.sceneSave,"sceneSave")
            self.RegisterWebFunction(self.changePassword,"changePassword")
            self.RegisterWebFunction(self.getTimestamp,"getTimestamp")
            self.RegisterWebFunction(self.makeBackup,"makeBackup")
            self.RegisterWebFunction(self.saveConfig,"saveConfig")
            self.RegisterWebFunction(self.sceneNew,"sceneNew")
            self.RegisterWebFunction(self.getAllLoadedPlugins,"getAllLoadedPlugins") 
        self.RegisterWebFunction(self.startBrowserMenu,"startBrowserMenu")
        self.RegisterWebFunction(self.getBrowserValue,"getBrowserValue")
        self.RegisterWebFunction(self.browserGoBack,"browserGoBack")
        self.RegisterWebFunction(self.browserGoToParent, "browserGoToParent")
        self.RegisterWebFunction(self.browserExecute, "browserExecute")
        self.RegisterWebFunction(self.browserOpenLocation, "browserOpenLocation")
        self.RegisterWebFunction(self.getBrowserValues,"getBrowserValues")
        self.RegisterWebFunction(self.getProperties,"getProperties")
        self.RegisterWebFunction(self.serachSubFolders,"serachSubFolders")
        self.RegisterWebFunction(self.getBrowerSearchResult,"getBrowerSearchResult")
        self.RegisterWebFunction(self.browserClose,"browserClose")
        self.RegisterWebFunction(self.mouseMove,"mouseMove")
        self.RegisterWebFunction(self.mouseScroll,"mouseScroll")
        self.RegisterWebFunction(self.sendKeys,"sendKeys")
        self.RegisterWebFunction(self.mouseButton,"mouseButton")
        self.stopUniThreadEvent = False
        self.serverIP = ''
        self.Ping=PingHost()
        self.RequestData=RequestData()
        self.cachedEvents={}
        self.LogWrapper=LogWrapper(self)
        self.saveToReg("configDir",self.configDir)
        try:
            open(os.environ['windir']+"\\check.txt", 'a').close()
            os.remove(os.environ['windir']+"\\check.txt")
            self.runsAsAdmin = True
        except:
            self.runsAsAdmin = False
        self.initLocalConfig()
        self.AddAction(StartMenu, hidden=True)
        self.AddAction(Execute, hidden=True)
        self.AddAction(GoToParent, hidden=True)
        self.AddAction(GoBack, hidden=True)
        self.AddAction(Cancel, hidden=True)
        self.AddAction(GetValue, hidden=True)
        #self.AddAction(RequestData, hidden=True)
        self.AddAction(ActiveMedia)
        self.AddAction(InterpretSpokenCommand,"InterpretSpokenCommand","Interpret Spoken Command","Interprets a spoken command and executes determined actions",None)
        typeGroup = self.AddGroup(
            "Extension Creation / Scripting",
            "Functions that help you with the creation of O-MEGA Extensions or if you like to do some scripting."
        )
        typeGroup.AddAction(SetValueForProgram)
        typeGroup.AddAction(GetValueForProgram)
        typeGroup.AddAction(SetValueForDevice)
        typeGroup.AddAction(GetValueForDevice)
        typeGroup.AddAction(SetSettingForProgram)
        typeGroup.AddAction(GetSettingForProgram)
        typeGroup.AddAction(SetSettingForDevice)
        typeGroup.AddAction(GetSettingForDevice)
        typeGroup.AddAction(SetSettingForInterface)
        typeGroup.AddAction(GetSettingForInterface)
        typeGroup.AddAction(GetDevicesByType)
        typeGroup.AddAction(GetInterfacesByType)
        typeGroup.AddAction(SetButtonValue, hidden=True)
        typeGroup.AddAction(GetButtonValue)
        typeGroup.AddAction(SetButtonState, hidden=True)
        typeGroup.AddAction(GetButtonState)
        typeGroup.AddAction(ServerExecute)
        typeGroup.AddAction(ClientExecute, hidden=True)
        typeGroup.AddAction(ReadyForAudio)
        typeGroup.AddAction(Ping)
        typeGroup.AddAction(ProgramPower)
        typeGroup.AddAction(SendEventExt,"SendEventExt","Send event to another webserver","Sends event to another webserver.",None)
        typeGroup.AddAction(RegisterWebFunction,"RegisterWebFunction","Registers a function to be used with the webserver","Registers a function to be used with the webserver.",None)
        typeGroup.AddAction(UnregisterWebFunction,"UnregisterWebFunction","Unregisters a function that was registered to be used with the webserver","Unregisters a function that was registered to be used with the webserver.",None)


    def __stop__(self):
        try:
            eg.scheduler.CancelTask(self.sceneAutoStartWait)
        except:
            pass
        for inst in xrange(len(self.instances)):
            if self.menuDlg[inst]:
                prefix = self.menuDlg[inst].prefix
                self.menuDlg[inst].watchStop()
                self.menuDlg[inst] = None
                self.instances[inst] = False
                eg.TriggerEvent(prefix = prefix, suffix ="Instance destroyed:" , payload = (inst+1))
        self.LogWrapper.StopAllEventListeners()
        self.Ping.PausePings()
        if self.pluginServer:
            self.saveStates()
            self.webServer.Stop()
            self.webServer = None
            print self.text.stopped % self.webPort
            if self.stopUniThreadEvent:
                self.stopUniThreadEvent.set()
        if self.TCPserver:
            self.TCPserver.close()
        self.TCPserver = None
        eg.TriggerEvent(prefix='O-MEGA', suffix='Plugin.Stopped')  
        

    def __close__(self):
        self.Ping.PausePings()
        if self.TCPserver:
            self.TCPserver.close()
        self.TCPserver = None
        if self.pluginServer:
            self.saveStates()
        eg.TriggerEvent(prefix='O-MEGA', suffix='Plugin.Unloaded')
    
    
    def __start__(self, port = 1024, password="", webPort=80, webAuthUsername="", webAuthPassword="", webCertfile = "", webKeyfile = "", autorunTimeout = 30, purgeBackupDays = 90):
        self.eventLog = []
        self.webPort=webPort
        self.browserSearchIDForInst={}
        self.browserSearchDataForInst={}
        pluginList=[]
        self.Ping.ResumePings()
        self.loadedPlugins=eg.plugins.__dict__.keys()
        for i in ["OMEGA","EventGhost","System","Window","Mouse"]:
            self.loadedPlugins.remove(i)
        if self.pluginServer:
            serverPluginList=["SchedulGhost"]
            self.allLoadedPlugins=self.loadedPlugins
            pluginList=self.loadDataFromConfig(serverPluginList)
            print "O-MEGA deleted backups: "+self.cleanBackup(purgeBackupDays)
        else:
            self.serverIP=self.readFromReg("serverIP")
            self.thisPc=self.readFromReg("thisPc")
            if self.serverIP!="":
                try:
                    pluginList=self.updateClient(self.RequestData(self.serverIP, self.info.args[0], self.info.args[1], u'self.info.version'))
                except:
                    eg.PrintError('O-MEGA: Server ('+self.serverIP+':'+str(self.info.args[0])+') is not reachable!')
                    self.serverOnline = False
                    
        missingPlugins=[]
        for i in pluginList:
            if i!="":
                if i not in self.loadedPlugins:
                    dlg = wx.MessageDialog(None, 'Plugin "'+i+'" could not be found in your configuration! (Please add this plugin to your configuration, save your configuration and restart EventGhost!)', "O-MEGA Start Error", wx.ICON_ERROR)
                    dlg.ShowModal()
                    dlg.Destroy()
                    missingPlugins.append(i)
                else:
                    #if self.pluginServer and i=="Webserver":
                    #    pass
                    #else:
                        eg.plugins.__dict__[i].plugin.info.Start()
        if len(missingPlugins)>0:
            self.__stop__()
            raise PrerequisiteError(missingPlugins)
            return False
        
        if self.pluginServer:
            if webAuthUsername or webAuthPassword:
                authString = b64encode(webAuthUsername + ':' + webAuthPassword)
            else:
                authString = None
            class RequestHandler(MyHTTPRequestHandler):
                plugin = self
                environment = Environment(loader=FileLoader())
                #environment.globals = eg.globals.__dict__
                repeatTimer = eg.ResettableTimer(self.EndLastEnduringEvent)
            RequestHandler.basepath = self.configDir+u"\\web"
            RequestHandler.authRealm = u"O-MEGA"
            RequestHandler.authString = authString
            self.webServer = MyServer(RequestHandler, webPort, webCertfile, webKeyfile)
            self.webServer.Start()
            sr = int(not (os.path.isfile(webCertfile) and os.path.isfile(webKeyfile)))
            print self.text.started % (self.text.secur[sr], webPort)
            self.saveToReg("SchedulGhostXMLPath",eg.plugins.SchedulGhost.plugin.info.args[0]+u'\\SchedulGhost.xml')
            self.saveToReg("EventGhostPath",eg.mainDir)
            self.saveToReg("PluginPath",self.info.path)
            
            self.stopUniThreadEvent = Event()
            thread = Thread(
                target=self.uniUpdateCheck,
                args=(self.stopUniThreadEvent, )
            )
            thread.start()
            self.serverOnline = True
            eg.TriggerEvent(prefix="O-MEGA", suffix="OnInit")
            self.sceneAutoStartWait = eg.scheduler.AddTask(autorunTimeout, self.sceneAutoStart)
        try:
            print "O-MEGA: This PC is recognized to be: "+self.thisPc
        except:
            eg.PrintError("O-MEGA: This PC was not found in your configuration, please configure this PC in the web-interface!")
        self.LogWrapper.AddEventListener()
        if self.TCPserver:
            self.TCPserver.close()
        self.TCPserver = None
        try:
            self.TCPserver = TCPServer(port, password, self)
        except socket.error, exc:
            eg.PrintError("O-MEGA: TCP Socket ERROR")
            raise self.Exception(exc[1])
        self.saveToReg("xmlpath",eg.document.filePath)
        eg.TriggerEvent(prefix='O-MEGA', suffix='Plugin.Started', payload=self.info.version)
    
    
    def sceneAutoStart(self):
        for i in xrange(len(self.sceneNames)):
            if self.sceneNames[i][6]==1 and self.sceneNames[i][2]=="[activate]":
                print "O-MEGA: Restarting scene "+str(self.sceneNames[i][1])+"("+str(self.sceneNames[i][0])+")"
                self.sceneAction(self.sceneNames[i][0],0,True,1)
            elif self.sceneNames[i][6]==2 and self.sceneNames[i][2]=="[activate]":
                print "O-MEGA: Continue execution of scene "+str(self.sceneNames[i][1])+"("+str(self.sceneNames[i][0])+")"
                self.sceneAction(self.sceneNames[i][0],self.sceneNames[i][4],True,1)
            else:
                self.sceneNames[i][2]="[none]"
                self.sceneAction(self.sceneNames[i][0],"*",True)
            if self.sceneNames[i][6]==3:
                eg.plugins.SchedulGhost.RunScheduleImmediately(u'scene'+str(self.sceneNames[i][0]),True)
                
    
    def OnComputerSuspend(self,type=None):
        self.__stop__()
    
    
    def OnComputerResume(self,type=None):
        self.__start__(*self.info.args)
    
    
    def Configure(self, port=1024, password="", webPort=80, webAuthUsername="", webAuthPassword="", webCertfile = "", webKeyfile = "", autorunTimeout = 30, purgeBackupDays = 90):
        self.text = Text
        panel = eg.ConfigPanel(self)
        portCtrl = panel.SpinIntCtrl(port, max=65535)
        passwordCtrl = panel.TextCtrl(password,style=wx.TE_PASSWORD)
        st1 = panel.StaticText(Text.port)
        st2 = panel.StaticText(Text.password)
        eg.EqualizeWidths((st1, st2))
        box1 = panel.BoxedGroup(Text.tcpBox, (st1, portCtrl), (st2, passwordCtrl))
        panel.AddLine(box1)
        
        def startImport(event):
            if self.runsAsAdmin:
                if eg.document.isDirty:
                    eg.document.Save()
                eg.plugins.System.Execute(eg.mainDir+u'\\pyw.exe', u'"'+self.info.path+u'\\ext\\importer.py" "'+eg.mainDir+u'\\EventGhost.exe" "'+eg.document.filePath+u'"', 0, False, 2, self.info.path, False, False, u'', True, True, False)
                eg.app.Exit()
            else:
                #eg.PrintError("O-MEGA: EventGhost needs to be executed as administrator in order to import something!")
                omegalib.msgBox("O-MEGA Import Error", "EventGhost needs to be executed as administrator in order to import something!", "error")
            
        def startExport(event):
            eg.plugins.System.Execute(eg.mainDir+u'\\pyw.exe', u'"'+self.info.path+u'\\ext\\exporter.py"', 0, False, 2, self.info.path, False, False, u'', True, True, False)
        
        if self.pluginServer:
            importButton = wx.Button(panel, -1, Text.importB)
            exportButton = wx.Button(panel, -1, Text.exportB)
            eg.EqualizeWidths((importButton, exportButton))
            box2 = panel.BoxedGroup(Text.importExportBox, (importButton), (exportButton))
            panel.AddLine(box2)
            importButton.Bind(wx.EVT_BUTTON, startImport)
            exportButton.Bind(wx.EVT_BUTTON, startExport)
            ACV = wx.ALIGN_CENTER_VERTICAL
            webPortCtrl = panel.SpinIntCtrl(webPort, min=1, max=65535)
            webCertfileCtrl = eg.FileBrowseButton(
                panel,
                -1,
                toolTip = Text.sslTool,
                dialogTitle = Text.webCertfile,
                buttonText = eg.text.General.browse,
                startDirectory = "",
                initialValue = webCertfile,
                fileMask = Text.cMask,
            )
            webKeyfileCtrl = eg.FileBrowseButton(
                panel,
                -1,
                toolTip = Text.sslTool,
                dialogTitle = Text.webKeyfile,
                buttonText = eg.text.General.browse,
                startDirectory = "",
                initialValue = webKeyfile,
                fileMask = Text.kMask,
            )
            webAuthUsernameCtrl = panel.TextCtrl(webAuthUsername)
            webAuthPasswordCtrl = panel.TextCtrl(webAuthPassword)
            labels = (
                panel.StaticText(Text.port),
                panel.StaticText(Text.webAuthUsername),
                panel.StaticText(Text.webAuthPassword),
                panel.StaticText(Text.webCertfile + ":"),
                panel.StaticText(Text.webKeyfile + ":")
            )
            eg.EqualizeWidths(labels)
            sizer = wx.FlexGridSizer(5, 2, 5, 5)
            sizer.AddGrowableCol(1)
            sizer.Add(labels[0], 0, ACV)
            sizer.Add(webPortCtrl)
            sizer.Add(labels[3], 0, ACV)
            sizer.Add(webCertfileCtrl, 0, wx.EXPAND)
            sizer.Add(labels[4], 0, ACV)
            sizer.Add(webKeyfileCtrl, 0, wx.EXPAND)
            sizer.Add(labels[1], 0, ACV)
            sizer.Add(webAuthUsernameCtrl)
            sizer.Add(labels[2], 0, ACV)
            sizer.Add(webAuthPasswordCtrl)
            webBox = wx.StaticBox(panel, label=Text.webBox)
            webBoxSizer = wx.StaticBoxSizer(webBox, wx.VERTICAL)
            webBoxSizer.Add(sizer, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 5)
            panel.sizer.Add(webBoxSizer, 0, wx.EXPAND)
            autorunTimeoutText = panel.StaticText(Text.autorunTimeout + ":")
            autorunTimeoutCtrl = panel.SpinIntCtrl(autorunTimeout, min=0, max=10000)
            purgeBackupDaysText = panel.StaticText(Text.purgeBackupDays + ":")
            purgeBackupDaysCtrl = panel.SpinIntCtrl(purgeBackupDays, min=0, max=10000)
            eg.EqualizeWidths((autorunTimeoutText, purgeBackupDaysText))
            box3 = panel.BoxedGroup(Text.miscSettings, (autorunTimeoutText, autorunTimeoutCtrl), (purgeBackupDaysText, purgeBackupDaysCtrl))
            panel.AddLine(box3)
            
        while panel.Affirmed():
            if self.pluginServer:
                panel.SetResult(
                    portCtrl.GetValue(), 
                    passwordCtrl.GetValue(),
                    webPortCtrl.GetValue(),
                    webAuthUsernameCtrl.GetValue(),
                    webAuthPasswordCtrl.GetValue(),
                    webCertfileCtrl.GetValue(),
                    webKeyfileCtrl.GetValue(),
                    autorunTimeoutCtrl.GetValue(),
                    purgeBackupDaysCtrl.GetValue(),
                )
            else:
                panel.SetResult(
                    portCtrl.GetValue(), 
                    passwordCtrl.GetValue(),
                )
 
#===============================================================================
# O-MEGA functions Start
#===============================================================================
    
    #thisClientWasConnected=False
    
    def updateClient(self, serverVersion):
        if self.info.version!=serverVersion:
            print "O-MEGA: Updating client and restarting EventGhost..."
            if eg.document.isDirty:
                eg.document.Save()
            pluginCode=self.RequestData(self.serverIP, self.info.args[0], self.info.args[1], u'getsourcelines(self.info.module)')[0]
            file=codecs.open(self.info.path+u'\\__init__.py','w',eg.systemEncoding)
            for codeLine in pluginCode:
                file.write(codeLine)
            file.close()
            time.sleep(3)
            wx.CallAfter(eg.app.Restart)
        else:
            pluginList=[]
            self.RequestData(self.serverIP, self.info.args[0], self.info.args[1], u'self.saveMac(\''+self.thisPc+'\',\''+self.thisPcMac+'\')')
            self.serverOnline = True
            self.getGlobalDicts()
            for data in self.programs:
                if data[3]==self.thisPc:
                    pluginList+=self.extensions[self.extensionsIDArray[data[1]]][3]
            for data in self.interfaces:
                if data[3]==self.thisPc:
                    pluginList+=self.extensions[self.extensionsIDArray[data[1]]][3]
            targetXMLconfig=self.RequestData(self.serverIP, self.info.args[0], self.info.args[1], u'self.GetOMEGAXML(\''+self.thisPc+'\')')
            targetHash = md5(targetXMLconfig).hexdigest()
            lastHash = self.readFromReg("xmlHash")
            if targetHash!=lastHash or self.readFromReg("xmlpath")!=eg.document.filePath:
                if self.ImportXML(eg.document.filePath,targetXMLconfig):
                    self.saveToReg("xmlHash",targetHash)
                    time.sleep(3)
                    wx.CallAfter(eg.app.Restart)
            else:
                #if self.thisClientWasConnected:
                #    if eg.document.isDirty:
                #        eg.document.Save()
                        #time.sleep(3)
                #    wx.CallAfter(eg.app.Restart)
                #if self.ServerExecute(u'True'):
                self.ServerExecute(u'eg.TriggerEvent(prefix=\'O-MEGA\', suffix=\'ClientPC.Connected\', payload=\''+unicode(self.thisPc)+u'\')')
                #self.thisClientWasConnected = True
                eg.TriggerEvent(prefix='O-MEGA', suffix='ServerPC.Connected', payload=self.serverIP)
                eg.TriggerEvent(prefix="O-MEGA", suffix="OnInit")
            return pluginList

        
    def initLocalConfig(self):
        self.thisPcName=socket.gethostname()
        tmp = [a for a in socket.gethostbyname_ex(self.thisPcName)[2]]
        addresses = []
        for a in tmp:
            if a.startswith("127.") or a.startswith("169."):
                continue
            addresses.append(a)
        self.thisPcIPs=addresses
        global MY_COMPUTER
        self.thisPcRoot=MY_COMPUTER
        self.thisPcMac='-'.join(("%012X" % getnode())[i:i+2] for i in range(0, 12, 2))
        
    
    def loadDataFromConfig(self,pluginList=[]):
        if not os.path.exists(self.configDir+u'\\web\\config'):
            os.mkdir(self.configDir+u'\\web\\config')
        if not os.path.exists(self.configDir+u'\\web\\img'):
            os.mkdir(self.configDir+u'\\web\\img')
        #=========================actionEvents Start============================
        try:
            file=codecs.open(self.configDir+u'\\web\\config\\actionEvents.json','r',eg.systemEncoding)
            self.actionEvents=json.load(file)
            file.close()
        except:
            try:
                file.close()
            except:
                pass
            self.actionEvents=defaultConfig.actionEvents()
            self.saveConfig(self.actionEvents,u'actionEvents.json',False)
        self.createActionEventCategories()
        #=========================actionEvents End==============================
        #=========================statesCfg Start===============================
        statesReset=False
        try:
            file=codecs.open(self.configDir+u'\\web\\config\\statesCfg.json','r',eg.systemEncoding)
            self.statesCfg=json.load(file)
            file.close()
        except:
            try:
                file.close()
            except:
                pass
            self.statesCfg=defaultConfig.statesCfg()
            self.saveConfig(self.statesCfg,u'statesCfg.json',False)
            statesReset=True
        self.validStates=["[none]","[error]","[?]"]
        for state in self.statesCfg:
            if not state[3] and state[0] not in self.validStates:
                self.validStates.append(state[0])
        #=========================statesCfg End==================================
        #=========================mediaCfg Start===============================
        try:
            file=codecs.open(self.configDir+u'\\web\\config\\mediaCfg.json','r',eg.systemEncoding)
            self.mediaCfg=json.load(file)
            file.close()
        except:
            try:
                file.close()
            except:
                pass
            self.mediaCfg=defaultConfig.mediaCfg()
            self.saveConfig(self.mediaCfg,u'mediaCfg.json',False)
        self.mediaCfgIDArray={}
        for i in xrange(len(self.mediaCfg)):
            self.mediaCfgIDArray[self.mediaCfg[i][0]]=i
        #=========================mediaCfg End==================================
        #=========================views Start====================================
        try:
            file=codecs.open(self.configDir+u'\\web\\config\\views.json','r',eg.systemEncoding)
            self.views=json.load(file)
            file.close()
            defaultViewMissing=True
            for view in self.views:
                if view[0]=="-":
                    defaultViewMissing=False
            if defaultViewMissing:
                self.views.append(["-", "-", 0])
                self.saveConfig(self.views,u'views.json',False)
        except:
            try:
                file.close()
            except:
                pass
            self.views=defaultConfig.views()
            self.saveConfig(self.views,u'views.json',False)
        self.viewsIDArray={}
        for i in xrange(len(self.views)):
            self.viewsIDArray[self.views[i][0]]=i
            if len(self.views[i])==2:
                self.views[i].append(0)
        #=========================views End=====================================
        #=========================users Start====================================
        self.spokenCommandCache={}
        try:
            file=codecs.open(self.configDir+u'\\web\\config\\users.json','r',eg.systemEncoding)
            self.users=json.load(file)
            file.close()
            defaultUserMissing=True
            adminMissing=True
            for user in self.users:
                if user[0]=="default":
                    defaultUserMissing=False
                if len(user)>3:
                    tempData = json.loads(user[3])
                    if "isAdmin" in tempData and tempData["isAdmin"]:
                        adminMissing=False
                self.spokenCommandCache[user[0]]={"lastCommand":""}
            if defaultUserMissing:
                self.users.append(["default", "", [], "{\"isAdmin\":1,\"isSceneEditor\":1}"])
                self.saveConfig(self.users,u'users.json',False)
            elif adminMissing:
                self.users.append(["admin", "", [], "{\"isAdmin\":1,\"isSceneEditor\":1}"])
                self.saveConfig(self.users,u'users.json',False)
        except:
            try:
                file.close()
            except:
                pass
            self.users=defaultConfig.users()
            self.saveConfig(self.users,u'users.json',False)
        self.usersIDArray={}
        changedSomething=False
        for i in xrange(len(self.users)):
            self.usersIDArray[self.users[i][0]]=i
            for y in reversed(xrange(len(self.users[i][2]))):
                if self.users[i][2][y] not in self.viewsIDArray:
                    self.users[i][2].pop(y)
                    changedSomething=True
        if changedSomething:
            self.saveConfig(self.users,u'users.json',False)
        #=========================users End=====================================
        #=========================files Start===================================
        try:
            file=codecs.open(self.configDir+u'\\web\\config\\files.json','r',eg.systemEncoding)
            self.files=json.load(file)
            file.close()
        except:
            try:
                file.close()
            except:
                pass
            self.files=defaultConfig.files()
            self.saveConfig(self.files,u'files.json',False)
        try:
            file=codecs.open(self.configDir+u'\\web\\config\\templatesCfg.json','r',eg.systemEncoding)
            tmp=json.load(file)
            file.close()
            defaultTemplates=defaultConfig.templatesCfg()
            somethingChanged=False
            for targetTemplateName in omegalib.SYSTEM_TEMPLATES:
                for defaultTemplate in defaultTemplates:
                    if defaultTemplate[0]==targetTemplateName:
                        for i in xrange(len(tmp)):
                            if tmp[i][0]==targetTemplateName:
                                if defaultTemplate[1]!=tmp[i][1]:
                                    tmp[i]=defaultTemplate
                                    somethingChanged=True
                                break
                            elif i == len(tmp)-1:
                                tmp.append(defaultTemplate)
                                somethingChanged=True
                        break
            if somethingChanged:
                self.saveConfig(tmp,u'templatesCfg.json',False)
        except:
            try:
                file.close()
            except:
                pass
            self.saveConfig(defaultConfig.templatesCfg(),u'templatesCfg.json',False)
        try:
            file=codecs.open(self.configDir+u'\\web\\config\\pages.json','r',eg.systemEncoding)
            tmp=json.load(file)
            file.close()
        except:
            try:
                file.close()
            except:
                pass
            self.saveConfig(defaultConfig.pages(),u'pages.json',False)
        try:
            file=codecs.open(self.configDir+u'\\web\\config\\doku.json','r',eg.systemEncoding)
            tmp=json.load(file)
            file.close()
        except:
            try:
                file.close()
            except:
                pass
            self.saveConfig(defaultConfig.doku(),u'doku.json',False)
        self.filesIDArray={}
        self.primaryFilesTarget={}
        self.buttons = []
        self.buttonsRIds = []
        self.buttonsIDArray = {}
        try:
            file=codecs.open(self.configDir+u'\\web\\config\\buttonStates.json','r',eg.systemEncoding)
            self.buttonStates = json.load(file)
            file.close()
        except:
            self.buttonStates = defaultConfig.buttonStates()
            self.saveConfig(self.buttonStates,u'buttonStates.json',False)
        try:
            file=codecs.open(self.configDir+u'\\web\\config\\States.json','r',eg.systemEncoding)
            self.States = json.load(file)
            file.close()
        except:
            self.States = defaultConfig.States()
            self.saveConfig(self.States,u'States.json',False)
        self.buttonStatesPre = {}
        self.buttonInterestingStates = {}
        self.hashs["buttons"]=1
        tempFilesIDList=[]
        self.buttonViewsForPage={}
        for y in self.files:
            tempFilesIDList.append(y[0])
        i=0
        z=0
        while i<len(self.files):
            self.filesIDArray[self.files[i][0]]=i
            self.buttonViewsForPage[self.files[i][0]]=False
            try:
                tempButtons=json.loads(self.files[i][5])
            except:
                #print self.files[i][0]+" does not have proper buttons!"
                tempButtons=[]
            pageLevel=0
            tempParent=self.files[i][1]
            while tempParent in tempFilesIDList:
                pageLevel+=1
                for y in self.files:
                    if y[0]==tempParent:
                        tempParent=y[1]
                        break
            if self.files[i][2]!="-":
                if self.files[i][2] not in self.primaryFilesTarget or primaryFilesTargetLevel>pageLevel:
                    self.primaryFilesTarget[self.files[i][2]]=[i]
                    primaryFilesTargetLevel=pageLevel
                elif primaryFilesTargetLevel==pageLevel:
                    self.primaryFilesTarget[self.files[i][2]].append(i)
            try:
                self.files[i][4]=json.loads(self.files[i][4])
                tmpKeys=self.files[i][4].keys()
                for item in tmpKeys:
                    self.files[i][4][item]=self.files[i][4][item].split(",")
            except:
                self.files[i][4]={}
            j=0
            if len(tempButtons)>0:
                while j<len(tempButtons):
                    target=tempButtons[j][1]
                    id=str(self.files[i][0]+"/"+tempButtons[j][0])
                    try:
                        tempButtons[j][5]=json.loads(tempButtons[j][5])
                    except:
                        tempButtons[j][5]={}
                    try:
                        tempButtons[j][6]=json.loads(tempButtons[j][6])
                    except:
                        tempButtons[j][6]={}
                    try:
                        tempButtons[j][7]=json.loads(tempButtons[j][7])
                    except:
                        tempButtons[j][7]={}
                    if target!="macro" or tempButtons[j][2]!="copy":#target!="frontend"
                        #target=target.split("/")
                        if id not in self.buttonStates:
                            self.buttonStates[id]={"state":"[?]","value":"?"}
                        if tempButtons[j][6]!={}:
                            self.buttonInterestingStates[id]=[]
                            self.buttonStatesPre[id]={}
                            tmpKeys=tempButtons[j][6].keys()
                            for y in self.validStates:
                                if y in tmpKeys:
                                    self.buttonStatesPre[id][y]=[]
                                    interesting=False
                                    for k in xrange(len(tempButtons[j][6][y])):
                                        self.buttonStatesPre[id][y].append(False)
                                        if not interesting and (tempButtons[j][6][y][k][0]!="" or tempButtons[j][6][y][k][1]!=""):
                                            interesting=True
                                    if interesting:
                                        self.buttonInterestingStates[id].append(y)
                            self.buttonsRIds.append(id)
                        else:
                            if id in self.buttonStates:
                                del self.buttonStates[id]
                    while len(tempButtons[j])<10:
                        tempButtons[j].append("")
                    for y in reversed(xrange(len(tempButtons[j][9]))):
                        if tempButtons[j][9][y] not in self.viewsIDArray:
                            tempButtons[j][9].pop(y)
                    if len(tempButtons[j][9])>0:
                        self.buttonViewsForPage[self.files[i][0]]=True
                    else:
                        tempButtons[j][9]=[[""]]
                    self.buttons.append(tempButtons[j])
                    self.buttonsIDArray[id]=z
                    z+=1
                    j+=1
            self.files[i][5]=tempButtons
            for y in reversed(xrange(len(self.files[i][10]))):
                if self.files[i][10][y] not in self.viewsIDArray:
                    self.files[i][10].pop(y)
            i+=1
        #============================files End==================================
        #=========================dictionary Start==============================
        try:
            file=codecs.open(self.configDir+u'\\web\\config\\dictionary.json','r',eg.systemEncoding)
            self.dictionary=json.load(file)
            file.close()
        except:
            try:
                file.close()
            except:
                pass
            self.dictionary=defaultConfig.dictionary(self.thisPcName)
            self.saveConfig(self.dictionary,u'dictionary.json',False)
        else:
            if statesReset:
                tempDict=defaultConfig.dictionary(self.thisPcName)
                self.dictionary["statesCfg.json"]=tempDict["statesCfg.json"]
                self.dictionary["statesCfg.jsonshort"]=tempDict["statesCfg.jsonshort"]
                self.dictionary["statesCfg.jsonvoice"]=tempDict["statesCfg.jsonvoice"]
                self.dictionary["statesCfg.jsonnames"]=tempDict["statesCfg.jsonnames"]
                self.dictionary["mediaCfg.json"]=tempDict["mediaCfg.json"]
                self.dictionary["mediaCfg.jsonvoice"]=tempDict["mediaCfg.jsonvoice"]
                self.dictionary["mediaCfg.jsonnames"]=tempDict["mediaCfg.jsonnames"]
                self.saveConfig(self.dictionary,u'dictionary.json',False)
        #=========================dictionary End================================
        #============================extensions Start===========================
        try:
            file=codecs.open(self.configDir+u'\\web\\config\\extensionsCfg.json','r',eg.systemEncoding)
            self.extensions=json.load(file)
            file.close()
            defaultExtensions=defaultConfig.extensions()
            somethingChanged=False
            for targetExtensionName in omegalib.SYSTEM_EXTENSIONS:
                for defaultExtension in defaultExtensions:
                    if defaultExtension[0]==targetExtensionName:
                        for i in xrange(len(self.extensions)):
                            if self.extensions[i][0]==targetExtensionName:
                                if defaultExtension[1]!=self.extensions[i][1]:
                                    self.extensions[i]=defaultExtension
                                    somethingChanged=True
                                break
                            elif i == len(self.extensions)-1:
                                self.extensions.append(defaultExtension)
                                somethingChanged=True
                        break
            if somethingChanged:
                self.saveConfig(self.extensions,u'extensionsCfg.json',False)
        except:
            try:
                file.close()
            except:
                pass
            self.extensions = defaultConfig.extensions()
            self.saveConfig(self.extensions,u'extensionsCfg.json',False)
        data=self.extensions
        self.extensionsIDArray={}
        for i in xrange(len(data)):
            try:
                tempArr=json.loads(data[i][4])
                self.extensions[i][4]={}
                for y in tempArr:
                    self.extensions[i][4][y[0]]=y[1]
            except:
                self.extensions[i][4]={}
            try:
                self.extensions[i][5]=json.loads(data[i][5])
            except:
                self.extensions[i][5]=[]
            #try:
            #    self.extensions[i][6]=json.loads(data[i][6])
            #except:
            #    self.extensions[i][6]={}
            try:
                self.extensions[i][7]=json.loads(data[i][7])
            except:
                self.extensions[i][7]=[]
            #try:
            #    self.extensions[i][8]=json.loads(data[i][8])
            #except:
            #    self.extensions[i][8]={}
            #try:
            #    self.extensions[i][9]=json.loads(data[i][9])
            #except:
            #    self.extensions[i][9]={}
            #try:
            #    self.extensions[i][10]=json.loads(data[i][10])
            #except:
            #    self.extensions[i][10]={}
            self.extensionsIDArray[data[i][0]]=i
        #============================extensions End=============================
        self.mediaPlayers=[]
        #============================devices Start==============================
        try:
            file=codecs.open(self.configDir+u'\\web\\config\\devices.json','r',eg.systemEncoding)
            self.devices=json.load(file)
            file.close()
            file=codecs.open(self.configDir+u'\\web\\config\\devices.json','r',eg.systemEncoding)
            self.devices2=json.load(file)
            file.close()
            serverMissing=True
            for device in self.devices:
                if device[0]=="-":
                    serverMissing=False
            if serverMissing:
                self.devices.append(["-", "PC_WIN", "{\"host\":\""+self.thisPcName+"\",\"mac\":\"\"}", "-", [""]])
                self.devices2.append(["-", "PC_WIN", "{\"host\":\""+self.thisPcName+"\",\"mac\":\"\"}", "-", [""]])
                self.saveConfig(self.devices,u'devices.json',False)
        except:
            try:
                file.close()
            except:
                pass
            self.devices = defaultConfig.devices(self.thisPcName)
            self.devices2 = defaultConfig.devices(self.thisPcName)
            self.saveConfig(self.devices,u'devices.json',False)
        data=self.devices
        self.hashs["devices"]=1
        if "devices" not in self.States:
            self.States["devices"]={}
        self.devicesIDArray={}
        self.hifiDevices=[]
        for i in xrange(len(data)):
            self.devicesIDArray[data[i][0]]=i
            tempDict={}
            for temp in self.extensions[self.extensionsIDArray[data[i][1]]][5]:
                if temp[2]=="int" or temp[2]=="checkbox":
                    tempDict[temp[0]]=int(temp[3])
                else:
                    tempDict[temp[0]]=temp[3]
            try:
                temp=self.merge_two_dicts(self.extensions[self.extensionsIDArray[data[i][1]]][4],tempDict)
                if data[i][2]=="":
                    data[i][2]=temp
                else:
                    data[i][2]=self.merge_two_dicts(temp,json.loads(data[i][2]))
            except Exception, err:
                eg.PrintError("O-MEGA: Failed to load settings for device: "+data[i][0]+". %s" % str(err))
                data[i][2]=self.extensions[self.extensionsIDArray[data[i][1]]][4]
            if data[i][1]=="PC_WIN":
                if data[i][0] not in self.States["devices"]:
                    self.States["devices"][data[i][0]] = {}
                self.States["devices"][data[i][0]]["browser"]={}
                if self.thisPcName.upper()==data[i][2]["host"].upper() or data[i][2]["host"] in self.thisPcIPs:
                    self.thisPc=data[i][0]
                    self.States["devices"][data[i][0]]["browser"]["root"]=self.thisPcRoot
                    self.saveMac(data[i][0],self.thisPcMac)
                else:
                    self.Ping.Ping(data[i][2]["host"],u'PC.'+data[i][0])
            if "maxOnTime" not in data[i][2] or data[i][2]["maxOnTime"]=="":
                data[i][2]["maxOnTime"]="5.0"
            if "maxOnRetry" not in data[i][2] or data[i][2]["maxOnRetry"]=="":
                data[i][2]["maxOnRetry"]="3"
            if "maxOffTime" not in data[i][2] or data[i][2]["maxOffTime"]=="":
                data[i][2]["maxOffTime"]="10.0"
            if "maxOffRetry" not in data[i][2] or data[i][2]["maxOffRetry"]=="":
                data[i][2]["maxOffRetry"]="3"
            if "masterAudio" in data[i][2] and (data[i][2]["masterAudio"]=="1" or data[i][2]["masterAudio"]=="True"):
                data[i][2]["masterAudio"]="1"
                self.hifiDevices.append(data[i][0])
            else:
                data[i][2]["masterAudio"]="0"
            if "mediaPlayer" in data[i][2] and (data[i][2]["mediaPlayer"]=="1" or data[i][2]["mediaPlayer"]=="True"):
                data[i][2]["mediaPlayer"]="1"
                self.mediaPlayers.append("devices/"+data[i][0])
            else:
                data[i][2]["mediaPlayer"]="0"
            if "forwardToMasterAudio" in data[i][2] and (data[i][2]["forwardToMasterAudio"]=="0" or data[i][2]["forwardToMasterAudio"]=="False"):
                data[i][2]["forwardToMasterAudio"]="0"
            else:
                data[i][2]["forwardToMasterAudio"]="1"
            if data[i][0] not in self.States["devices"]:
                self.States["devices"][data[i][0]] = {}
            pluginList+=self.extensions[self.extensionsIDArray[data[i][1]]][3]
            if data[i][1]=="Pseudo_Device":
                if data[i][2]["buttonIDSelector"] in self.buttonsIDArray:
                    deviceResponseData=self.buttons[self.buttonsIDArray[data[i][2]["buttonIDSelector"]]][6]
                else:
                    eg.PrintError("O-MEGA: Pseudo_Device ("+data[i][0]+") is broken, as the associated button has been deleted! Please update or delete this Device!")
                    deviceResponseData={}
            else:
                try:
                    deviceResponseData=json.loads(self.extensions[self.extensionsIDArray[data[i][1]]][6])
                except:
                    deviceResponseData={}
            deviceActionData={}
            try:
                tempActionData=json.loads(self.extensions[self.extensionsIDArray[data[i][1]]][8])
            except:
                tempActionData={}
            if "power" in tempActionData:
                for state in tempActionData["power"]:
                    tempData={}
                    for param in tempActionData["power"][state]:
                        tempData[param[0]]=[param[3], int(param[4])]
                    deviceActionData[state]=tempData
            target=u"devices/"+data[i][0]
            id=target+u"/power"
            if deviceResponseData!={}:
                self.buttonInterestingStates[id]=[]
                if id not in self.buttonStates:
                    self.buttonStates[id]={"state":"[?]","value":"?"}
                if "power" not in self.States["devices"][data[i][0]]:
                    self.States["devices"][data[i][0]]["power"]="[?]"
                self.buttonStatesPre[id]={}
                tmpKeys=deviceResponseData.keys()
                for y in tmpKeys:
                    if y in self.validStates:
                        self.buttonStatesPre[id][y]=[]
                        interesting=False
                        for k in xrange(len(deviceResponseData[y])):
                            for q in [0,1]:
                                if deviceResponseData[y][k][q]!="":
                                    interesting=True
                                    deviceResponseData[y][k][q]=self.replaceVariableInText(deviceResponseData[y][k][q],target)
                                else:
                                    break
                            self.buttonStatesPre[id][y].append(False)
                        if interesting:
                            self.buttonInterestingStates[id].append(y)
                self.buttonsRIds.append(id)
            else:
                #if id not in self.buttonStates:
                self.buttonStates[id]={"state":"[?]","value":"?"}
                #if data[i][0] not in self.States["devices"]:
                self.States["devices"][data[i][0]]["power"]="[?]"
            self.buttons.append([u"power",target,u"power",[],[u"[on]",u"[off]"],deviceActionData,deviceResponseData,u""])
            self.buttonsIDArray[id]=z
            z+=1
        #============================devices End================================
        #============================interfaces Start===========================
        try:
            file=codecs.open(self.configDir+u'\\web\\config\\interfaces.json','r',eg.systemEncoding)
            self.interfaces=json.load(file)
            file.close()
        except:
            try:
                file.close()
            except:
                pass
            self.interfaces = defaultConfig.interfaces()
            self.saveConfig(self.interfaces,u'interfaces.json',False)
        data=self.interfaces
        self.interfacesIDArray={}
        for i in xrange(len(data)):
            tempDict={}
            for temp in self.extensions[self.extensionsIDArray[data[i][1]]][5]:
                if temp[2]=="int" or temp[2]=="checkbox":
                    tempDict[temp[0]]=int(temp[3])
                else:
                    tempDict[temp[0]]=temp[3]
            try:
                temp=self.merge_two_dicts(self.extensions[self.extensionsIDArray[data[i][1]]][4],tempDict)
                if data[i][2]=="":
                    data[i][2]=temp
                else:
                    data[i][2]=self.merge_two_dicts(temp,json.loads(data[i][2]))
            except Exception, err:
                eg.PrintError("O-MEGA: Failed to load settings for interface: "+data[i][0]+". %s" % str(err))
                data[i][2]=self.extensions[self.extensionsIDArray[data[i][1]]][4]
                #if data[i][2]=={}:
                #    data[i][2]=""
            if data[i][1]=="Ping":
                self.Ping.Ping(data[i][2]["host"],data[i][0])
            self.interfacesIDArray[data[i][0]]=i
            if data[i][3]==self.thisPc:
                pluginList+=self.extensions[self.extensionsIDArray[data[i][1]]][3]
        #============================interfaces End=============================
        #============================programs Start=============================
        try:
            file=codecs.open(self.configDir+u'\\web\\config\\programs.json','r',eg.systemEncoding)
            self.programs=json.load(file)
            file.close()
        except:
            try:
                file.close()
            except:
                pass
            self.programs = defaultConfig.programs()
            self.saveConfig(self.programs,u'programs.json',False)
        data=self.programs
        self.hashs["programs"]=1
        if "programs" not in self.States:
            self.States["programs"]={}
        self.programsIDArray={}
        self.programsForPCsByType={}
        for i in xrange(len(data)):
            self.programsIDArray[data[i][0]]=i
            tempDict={}
            for temp in self.extensions[self.extensionsIDArray[data[i][1]]][5]:
                if temp[2]=="int" or temp[2]=="checkbox":
                    tempDict[temp[0]]=int(temp[3])
                else:
                    tempDict[temp[0]]=temp[3]
            try:
                temp=self.merge_two_dicts(self.extensions[self.extensionsIDArray[data[i][1]]][4],tempDict)
                if data[i][2]=="":
                    data[i][2]=temp
                else:
                    data[i][2]=self.merge_two_dicts(temp,json.loads(data[i][2]))
            except Exception, err:
                eg.PrintError("O-MEGA: Failed to load settings for program: "+data[i][0]+". %s" % str(err))
                data[i][2]=self.extensions[self.extensionsIDArray[data[i][1]]][4]
                #if data[i][2]=={}:
                #    data[i][2]=""
            if "maxOnTime" not in data[i][2] or data[i][2]["maxOnTime"]=="":
                data[i][2]["maxOnTime"]="5.0"
            if "maxOnRetry" not in data[i][2] or data[i][2]["maxOnRetry"]=="":
                data[i][2]["maxOnRetry"]="1"
            if "maxOffTime" not in data[i][2] or data[i][2]["maxOffTime"]=="":
                data[i][2]["maxOffTime"]="10.0"
            if "maxOffRetry" not in data[i][2] or data[i][2]["maxOffRetry"]=="":
                data[i][2]["maxOffRetry"]="1"
            data[i][2]["masterAudio"]="0"
            if "mediaPlayer" in data[i][2] and (data[i][2]["mediaPlayer"]=="1" or data[i][2]["mediaPlayer"]=="True"):
                data[i][2]["mediaPlayer"]="1"
                self.mediaPlayers.append("programs/"+data[i][0])
            else:
                data[i][2]["mediaPlayer"]="0"
            if "forwardToMasterAudio" in data[i][2] and (data[i][2]["forwardToMasterAudio"]=="0" or data[i][2]["forwardToMasterAudio"]=="False"):
                data[i][2]["forwardToMasterAudio"]="0"
            else:
                data[i][2]["forwardToMasterAudio"]="1"
            if data[i][3] not in self.programsForPCsByType:
                self.programsForPCsByType[data[i][3]]={}
            self.programsForPCsByType[data[i][3]][data[i][1]]=data[i][0]
            if data[i][0] not in self.States["programs"]:
                self.States["programs"][data[i][0]] = {}
            if data[i][3]==self.thisPc:
                pluginList+=self.extensions[self.extensionsIDArray[data[i][1]]][3]
            try:
                deviceResponseData=json.loads(self.extensions[self.extensionsIDArray[data[i][1]]][6])
            except:
                deviceResponseData={}
            deviceActionData={}
            try:
                tempActionData=json.loads(self.extensions[self.extensionsIDArray[data[i][1]]][8])
            except:
                tempActionData={}
            if "power" in tempActionData:
                for state in tempActionData["power"]:
                    tempData={}
                    for param in tempActionData["power"][state]:
                        tempData[param[0]]=[param[3], int(param[4])]
                    deviceActionData[state]=tempData
            target=u"programs/"+data[i][0]
            id=target+u"/power"
            if deviceResponseData!={}:
                self.buttonInterestingStates[id]=[]
                if id not in self.buttonStates:
                    self.buttonStates[id]={"state":"[?]","value":"?"}
                if "power" not in self.States["programs"][data[i][0]]:
                    self.States["programs"][data[i][0]]["power"]="[?]"
                self.buttonStatesPre[id]={}
                tmpKeys=deviceResponseData.keys()
                for y in tmpKeys:
                    if y in self.validStates:
                        self.buttonStatesPre[id][y]=[]
                        interesting=False
                        for k in xrange(len(deviceResponseData[y])):
                            for q in [0,1]:
                                if deviceResponseData[y][k][q]!="":
                                    interesting=True
                                    deviceResponseData[y][k][q]=self.replaceVariableInText(deviceResponseData[y][k][q],target)
                                else:
                                    break
                            self.buttonStatesPre[id][y].append(False)
                        if interesting:
                            self.buttonInterestingStates[id].append(y)
                self.buttonsRIds.append(id)
            else:
                #if id not in self.buttonStates:
                self.buttonStates[id]={"state":"[?]","value":"?"}
                #if data[i][0] not in self.States["programs"]:
                self.States["programs"][data[i][0]]["power"]="[?]"
            self.buttons.append([u"power",target,u"power",[],[u"[on]",u"[off]"],deviceActionData,deviceResponseData,u""])
            self.buttonsIDArray[id]=z
            z+=1
        #============================programs End===============================
        #============================sceneNames Start===========================
        try:
            file=codecs.open(self.configDir+u'\\web\\config\\sceneNames.json','r',eg.systemEncoding)
            self.sceneNames=json.load(file)
            file.close()
        except:
            try:
                file.close()
            except:
                pass
            self.sceneNames = defaultConfig.sceneNames()
            self.saveConfig(self.sceneNames,u'sceneNames.json',False)
        self.hashs["scene"]=1
        self.hashs["sceneData"]=1
        self.sceneNamesIds={}
        somethingChanged=False
        for i in xrange(len(self.sceneNames)):
            while len(self.sceneNames[i])<=7:
                self.sceneNames[i].append(0)
            if len(self.sceneNames[i])==8:
                self.sceneNames[i].append([])
                somethingChanged=True
            for y in reversed(xrange(len(self.sceneNames[i][8]))):
                if self.sceneNames[i][8][y] not in self.viewsIDArray:
                    self.sceneNames[i][8].pop(y)
                    somethingChanged=True
            self.sceneNamesIds[self.sceneNames[i][0]]=i
        if somethingChanged:
            self.saveConfig(self.sceneNames,u'sceneNames.json',False)
        #============================sceneNames End=============================
        #============================sceneActions Start=========================
        try:
            file=codecs.open(self.configDir+u'\\web\\config\\sceneActions.json','r',eg.systemEncoding)
            self.sceneActions=json.load(file)
            file.close()
        except:
            try:
                file.close()
            except:
                pass
            self.sceneActions = defaultConfig.sceneActions()
            self.saveConfig(self.sceneActions,u'sceneActions.json',False)
        #============================sceneActions End===========================
        #============================userSettings Start=========================
        try:
            file=codecs.open(self.configDir+u'\\web\\config\\userSettings.json','r',eg.systemEncoding)
            self.userSettings=json.load(file)
            file.close()
        except:
            try:
                file.close()
            except:
                pass
            self.userSettings = defaultConfig.userSettings()
            self.saveConfig(self.userSettings,u'userSettings.json',False)
        if self.cleanUserSettings():
            self.saveConfig(self.userSettings,u'userSettings.json',False)
        #============================userSettings End===========================
        self.createButtonResponseCategories()
        tmpKeys=self.buttonStates.keys()
        for id in tmpKeys:
            if id not in self.buttonsIDArray:
                del self.buttonStates[id]
        return pluginList


    def cleanUserSettings(self):
        result=False
        tmpKeys=self.userSettings.keys()
        userIds=[]
        for user in self.users:
            userIds.append(user[0])
            result=True
        for id in tmpKeys:
            if id not in userIds:
                del self.userSettings[id]
                result=True
        return result

        
    def createButtonResponseCategories(self):
        self.buttonResponseCategories=[[[],[],[]],[[],[],[]],[[],[],[]]]
        for id in self.buttonsRIds:
            tempButton=self.buttons[self.buttonsIDArray[id]]
            thisButtonInterestingStates=self.buttonInterestingStates[id]
            for j in thisButtonInterestingStates:#j=state
                brake2=False
                for responses in tempButton[6][j]:
                    response=responses[0].split(".")
                    try:
                        tempNumber=ord(response[1][0])
                    except:
                        tempNumber=937
                    try:
                        tempNumber2=ord(response[2][0])
                    except:
                        tempNumber2=937
                    if tempNumber<78:
                        if tempNumber==42 or tempNumber==63:
                            for i1 in [0,1,2]:
                                for i2 in [0,1,2]:
                                    if id not in self.buttonResponseCategories[i1][i2]:
                                        self.buttonResponseCategories[i1][i2].append(id)
                            brake2=True
                            break
                        catID1=0
                    elif tempNumber<91:
                        catID1=1
                    else:
                        catID1=2
                    if tempNumber2<78:
                        if tempNumber2==42 or tempNumber2==63:
                            for i2 in [0,1,2]:
                                if id not in self.buttonResponseCategories[catID1][i2]:
                                    self.buttonResponseCategories[catID1][i2].append(id)
                            continue
                        catID2=0
                    elif tempNumber2<91:
                        catID2=1
                    else:
                        catID2=2
                    if id not in self.buttonResponseCategories[catID1][catID2]:
                        self.buttonResponseCategories[catID1][catID2].append(id)
                if brake2:
                    break
               
               
    def createActionEventCategories(self):
        self.actionEventCategories=[[[],[],[]],[[],[],[]],[[],[],[]]]
        self.actionEventsIds={}
        for id in xrange(len(self.actionEvents)):
            self.actionEventsIds[self.actionEvents[id][0]]=id
            for responses in self.actionEvents[id][1]:
                response=responses[0].split(".")
                try:
                    tempNumber=ord(response[1][0])
                except:
                    tempNumber=937
                try:
                    tempNumber2=ord(response[2][0])
                except:
                    tempNumber2=937
                if tempNumber<78:
                    if tempNumber==42 or tempNumber==63:
                        for i1 in [0,1,2]:
                            for i2 in [0,1,2]:
                                if id not in self.actionEventCategories[i1][i2]:
                                    self.actionEventCategories[i1][i2].append(id)
                        break
                    catID1=0
                elif tempNumber<91:
                    catID1=1
                else:
                    catID1=2
                if tempNumber2<78:
                    if tempNumber2==42 or tempNumber2==63:
                        for i2 in [0,1,2]:
                            if id not in self.actionEventCategories[catID1][i2]:
                                self.actionEventCategories[catID1][i2].append(id)
                        continue
                    catID2=0
                elif tempNumber2<91:
                    catID2=1
                else:
                    catID2=2
                if id not in self.actionEventCategories[catID1][catID2]:
                    self.actionEventCategories[catID1][catID2].append(id)
    
    
    def merge_two_dicts(self,x, y):
        z = x.copy()   # start with x's keys and values
        z.update(y)    # modifies z with y's keys and values & returns None
        return z
    
    
    def replaceVariableInText(self,oldText,target):
        toReplace=re.findall('\{(.*?)\}',oldText)
        for newText in toReplace:
            tempResult=newText
            try:
                tempResult=json.loads(newText)
            except:
                tempResultParts=newText.split(".")
                if tempResultParts[0]=="target":
                    tempTargetParts=target.split("/")
                    tempData=[]
                    if tempTargetParts[0]=="devices":
                        tempData=self.devices[self.devicesIDArray[tempTargetParts[1]]]
                    elif tempTargetParts[0]=="programs":
                        tempData=self.programs[self.programsIDArray[tempTargetParts[1]]]
                    elif tempTargetParts[0]=="interfaces":
                        tempData=self.interfaces[self.interfacesIDArray[tempTargetParts[1]]]
                    if len(tempData)!=0:
                        if len(tempResultParts)==2:
                            tempResult=tempData[int(tempResultParts[1])]
                        elif len(tempResultParts)==3:
                            tempResult=tempData[int(tempResultParts[1])][tempResultParts[2]]
            if newText!=tempResult:
                #print target+": replace "+newText+" with "+tempResult
                oldText=oldText.replace('{'+newText+'}',tempResult,1)
        return oldText
     
  
    def TriggerEnduringEvent2(self, prefix, suffix, payload=None):
        #payload=json.loads(unquote(payload))
        newEvent=eg.TriggerEnduringEvent(prefix=prefix, suffix=suffix, payload=payload)
        i=0
        while str(i) in self.cachedEvents:
            i+=1
        eventRef=str(i)
        self.cachedEvents[eventRef]=newEvent
        return eventRef
            
            
    def updateBrowserDataState(self, targetPC, inst, what="reset",value=0):
        if self.pluginServer:
            inst=str(inst)
            if what=="reset":
                self.States["devices"][targetPC]["browser"][inst]={}
                self.States["devices"][targetPC]["browser"][inst]["newSearchData"]=value
                self.States["devices"][targetPC]["browser"][inst]["newData"]=value
                self.incrementHash("devices")
            elif self.States["devices"][targetPC]["browser"][inst][what]!=value:
                self.States["devices"][targetPC]["browser"][inst][what]=value
                self.incrementHash("devices")
        else:
            self.RequestData(self.serverIP, self.info.args[0], self.info.args[1], u'self.updateBrowserDataState(\''+targetPC+'\','+unicode(inst)+',\''+what+'\','+unicode(value)+')')
        
        
    def getBrowerSearchResult(self, inst):
        self.updateBrowserDataState(self.thisPc, inst, "reset", 0)
        return json.dumps(self.browserSearchDataForInst[inst])
    
    
    def getBrowserValue(self ,inst, val, target, reload):
        self.updateBrowserDataState(self.thisPc, inst, "reset", 0)
        return json.dumps([eg.plugins.OMEGA.GetValue(val, inst, target, reload),eg.plugins.OMEGA.GetValue(3, inst)])
    
    
    def getBrowserValues(self ,inst, val, targets):
        result=[]
        #targets=json.loads(targets)
        for target in targets:
            result.append(eg.plugins.OMEGA.GetValue(val, inst, int(target)))
        return json.dumps(result)
    
    
    def startBrowserMenu(self, target, filter, hidehidden):
        inst=eg.plugins.OMEGA.StartMenu(u'O-MEGA', target, filter, hidehidden)
        if inst!=False:
            self.updateBrowserDataState(self.thisPc, inst, "reset", 0)
            self.browserSearchIDForInst[inst]=0
            self.browserSearchDataForInst[inst]=[]
        return inst
    
    
    def browserGoBack(self, inst):
        self.updateBrowserDataState(self.thisPc, inst, "reset", 0)
        self.browserSearchIDForInst[inst]+=1
        return eg.plugins.OMEGA.GoBack(inst)
        
    
    def browserGoToParent(self, inst):
        self.updateBrowserDataState(self.thisPc, inst, "reset", 0)
        self.browserSearchIDForInst[inst]+=1
        return eg.plugins.OMEGA.GoToParent(inst)
            
    
    def serachSubFolders(self, inst,searchString):
        self.updateBrowserDataState(self.thisPc, inst, "reset", 0)
        thread = Thread(
            target=self.serachSubFolders1,
            args=(inst,searchString,(self.browserSearchIDForInst[inst]+1) )
        )
        thread.start()
        return True

    
    def serachSubFolders1(self, inst, searchString,searchid):
        self.browserSearchIDForInst[inst]=searchid
        folderPath=eg.plugins.OMEGA.GetValue(4, inst, 1)
        searchString=unicode(searchString.decode("latin1"))#utf-8 geht nicht gescheid
        #print folderPath
        #print searchString
        inst2=eg.plugins.OMEGA.StartMenu(u'O-MEGA', folderPath, u'*', True, None, True, False)
        data =self.searchSubFolders2(inst2,searchString)
        #print data
        eg.plugins.OMEGA.Cancel(inst2)
        if self.browserSearchIDForInst[inst]==searchid:
            self.browserSearchDataForInst[inst] = json.dumps(data[1]+data[0])
            self.updateBrowserDataState(self.thisPc,inst,"newSearchData",1)
    
    
    def searchSubFolders2(self, inst, searchString):
        tempArr=eg.plugins.OMEGA.GetValue(3, inst, False)
        data=[]
        folder=[]
        folder2=[]
        i=0
        while i<len(tempArr):
            if tempArr[i].find(shortcut_ID)==-1:
                if tempArr[i].find(folder_ID)==-1:
                    if tempArr[i].lower().find(searchString.lower())!=-1:
                        data+=eg.plugins.OMEGA.GetValue(2, inst, i, False)
                else:
                    if tempArr[i].lower().find(searchString.lower())!=-1:
                        folder2+=eg.plugins.OMEGA.GetValue(2, inst, i, False)
                    folder.append(eg.plugins.OMEGA.GetValue(1, inst, i, False))
            i+=1
        for folderPath in folder:
            eg.plugins.OMEGA.StartMenu(u'O-MEGA', folderPath, u'*', True, inst, False, False)
            temp=self.searchSubFolders2(inst,searchString)
            data+=temp[0]
            folder2+=temp[1]
        return [data,folder2]
    
    
    def browserOpenLocation(self,inst,location):
        self.updateBrowserDataState(self.thisPc, inst, "reset", 0)
        #location=unquote(location)
        self.browserSearchIDForInst[inst]+=1
        return eg.plugins.OMEGA.StartMenu(u'O-MEGA', location, u'*', True, inst, False)

    
    def browserExecute(self,bla1,bla2,bla3,inst,target):
        #self.updateBrowserDataState(self.thisPc, inst, "reset", 0)
        return json.dumps(eg.plugins.OMEGA.Execute(bla1, bla2, bla3, inst, target))
    
    
    def getProperties(self, inst,targets,mode):
        #targets=json.loads(targets)
        if len(targets)==1:
            target = targets[0]
            tempArr = []
            for i in 1,7,8,9,10,11:
                if i==7 and mode==-1:
                    tempArr.append(u"False")
                else:
                    tempArr.append(eg.plugins.OMEGA.GetValue(i, inst, target))
            return json.dumps(tempArr)
        else:
            j=0
            size=0
            files=0
            folders=0
            while j<len(targets):
                output = eg.plugins.OMEGA.GetValue(7, inst, targets[j])
                size+=output[0]
                files+=output[1]
                folders+=output[2]
                j+=1
            return json.dumps([u"False",[size,files,folders],u"False",u"False",u"False",u"False"])

    
    def browserClose(self, inst):
        return eg.plugins.OMEGA.Cancel(inst)
            
    
    sendKeysActive=False
    def sendKeys(self, data, hotKey=True, mode=2):
        while self.sendKeysActive:
            time.sleep(0.1)
        self.sendKeysActive=True
        #data = unicode(unquote(data).decode("utf-8"))
        #print data
        if hotKey:
            eg.plugins.Window.SendKeys(data, False)
        else:
            while True:
                try:
                    OpenClipboard(None)
                    break
                except:
                    self.PrintError("O-MEGA: OpenClipboard failed! Retrying..")
                    time.sleep(0.1)
            cDatas={}
            cForms=[]
            rc= EnumClipboardFormats(0)
            while rc and rc < 16:
                try:
                    cDatas[rc]=GetClipboardData(rc)
                    cForms.append(rc)
                except:
                    pass
                rc= EnumClipboardFormats(rc)
            EmptyClipboard()
            SetClipboardText(data)
            while True:
                try:
                    CloseClipboard()
                    break
                except:
                    self.PrintError("O-MEGA: CloseClipboard failed! Retrying..")
                    time.sleep(0.1)
            time.sleep(0.1)
            eg.plugins.Window.SendKeys("{Ctrl+v}", False)
            time.sleep(0.1)
            while True:
                try:
                    OpenClipboard(None)
                    break
                except:
                    self.PrintError("O-MEGA: OpenClipboard failed! Retrying..")
                    time.sleep(0.1)
            EmptyClipboard()
            for y in cForms:
                SetClipboardData(y,cDatas[y])
            while True:
                try:
                    CloseClipboard()
                    break
                except:
                    self.PrintError("O-MEGA: CloseClipboard failed! Retrying..")
                    time.sleep(0.1)
        self.sendKeysActive=False
        return data
    
    
    def mouseButton(self, button,what):
        if button==1 and what=="[click]":
            eg.plugins.Mouse.LeftButton()
        elif button==2 and (what=="[click]" or what=="[up]"):
            eg.plugins.Mouse.RightButton()
        elif button==1 and what=="[up]":
            eg.plugins.Mouse.ToggleLeftButton(1)
        elif button==1 and what=="[down]":
            eg.plugins.Mouse.ToggleLeftButton(2)
        point = POINT()
        GetCursorPos(point)
        return json.dumps([point.x,point.y])
    
    
    def mouseMove(self, dataX, dataY):
        eg.plugins.Mouse.MoveRelative(int(dataX),int(dataY), True)
            
            
    def mouseScroll(self, dataX, dataY):
        eg.plugins.Mouse.MouseWheel(int(dataY))
        
    
    def makeBackup(self):
        return omegalib.makeBackup()
        
        
    def cleanBackup(self,days):
        return ", ".join(omegalib.cleanBackup(int(days)))
    
    
    #def saveConfig1(self, data,filename,saveOthers=True):
    #    data=json.loads(unquote(data))#.decode("utf-8")
    #    self.saveConfig(data,filename,saveOthers)
    #    return True
    
    
    def saveConfig(self, data,filename,saveOthers=True):
        file=codecs.open(self.configDir+u'\\web\\config\\'+filename,'w',eg.systemEncoding)
        json.dump(data,file)
        file.close()
        if saveOthers and (filename=="files.json" or filename=="devices.json" or filename=="interfaces.json" or filename=="programs.json"):
            self.saveStates()
            self.loadDataFromConfig()
        return True
            

    def saveStates(self):
        self.saveConfig(self.buttonStates,"buttonStates.json",False)
        for item in self.States["devices"].keys():
            if item not in self.devicesIDArray:
                del self.States["devices"][item]
        for item in self.States["programs"].keys():
            if item not in self.programsIDArray:
                del self.States["programs"][item]
        self.saveConfig(self.States,"States.json",False)
            
    
    def saveUserSettings(self, user,setting,value):
        if setting=="all":
            self.userSettings[user]=value
        else:
            self.userSettings[user][setting]=value
        file=codecs.open(self.configDir+u'\\web\\config\\userSettings.json','w',eg.systemEncoding)
        json.dump(self.userSettings,file)
        file.close()
        return True
        
        
    def getUserSettings(self, user,setting):
        if setting=="all":
            return self.userSettings[user]
        else:
            return self.userSettings[user][setting]
        
    
    def loadActionEventsFor(self, action):
        action=unquote(action)
        if action in self.actionEventsIds:
            return json.dumps(self.actionEvents[self.actionEventsIds[action]][1])
        return False
    
    
    def saveActionEventsFor(self, action, events):
        action=unquote(action)
        events=json.loads(unquote(events))
        result = self.saveActionEventsFor2(action, events)
        if result:
            self.saveConfig(self.actionEvents,"actionEvents.json")
        return result
        
        
    def saveActionEventsFor2(self, action, events):
        if action in self.actionEventsIds:
            self.actionEvents[self.actionEventsIds[action]][1]=events
        else:
            self.actionEvents.append([action,events])
            #self.actionEventsIds[action]=len(self.actionEvents)-1
        self.createActionEventCategories()
        return True
        
        
    def removeActionEventsFor(self, action):
        action=unquote(action)
        result = self.removeActionEventsFor2(action)
        if result:
            self.saveConfig(self.actionEvents,"actionEvents.json")
        return result
        
    
    def removeActionEventsFor2(self, search):
        found=False
        try:
            for action in self.actionEventsIds:
                if fnmatch(action,search):
                    found = True
                    del self.actionEvents[self.actionEventsIds[action]]
        except:
            return self.removeActionEventsFor2(search)
        if found:       
            self.createActionEventCategories() 
        return found
    
    
    uniWatchedVars=[]
    uniUpdateIps=[]
    uniUpdateHashOld={}
    uniUpdateData={}
    uniWatchedVarsByIp={}
    hashs={}
    hashs["uniUpdate"]=1
    hashmodes=["scene","sceneData","buttons","devices","programs"]
    
    def uniUpdate(self, ip,varName):
        if ip not in self.uniUpdateIps:
            self.uniUpdateIps.append(ip)
            self.uniWatchedVarsByIp[ip]=[]
        if varName not in self.uniWatchedVarsByIp[ip]:
            self.uniWatchedVarsByIp[ip].append(varName)
            self.uniUpdateHashOld[varName]=0
            if varName not in self.uniWatchedVars:
                self.uniUpdateData[varName]=""
                self.uniWatchedVars.append(varName)
            #print "registered "+varName+" for "+ip
            return True
        return False
        

    def uniUnregister(self,ip,varName):
        if varName in self.uniWatchedVarsByIp[ip]:
            self.uniWatchedVarsByIp[ip].remove(varName)
            if len(self.uniWatchedVarsByIp[ip])==0:
                self.uniUpdateIps.remove(ip)
                del self.uniWatchedVarsByIp[ip]
            varNotWatched=True
            for tempip in self.uniUpdateIps:
                if varName in self.uniWatchedVarsByIp[tempip]:
                    varNotWatched=False
                    break
            if varNotWatched:
                self.uniWatchedVars.remove(varName)
                del self.uniUpdateHashOld[varName]
            #print "unregistered "+varName+" for "+ip
            return True
        return False
        

    def uniUpdateCheck(self,stopThreadEvent):
        while not stopThreadEvent.isSet():
            for currentVar in self.uniWatchedVars:
                tempData=eval(unquote(currentVar))
                tempHash=hash(repr(tempData))
                if self.uniUpdateHashOld[currentVar]!= tempHash:
                    self.uniUpdateHashOld[currentVar] = tempHash
                    self.uniUpdateData[currentVar] = tempData
                    self.hashs["uniUpdate"]+=1
            time.sleep(0.2)
    
    
    def incrementHash(self, targetHash):
        self.hashs[targetHash]+=1
        try:
            eg.scheduler.CancelTask(self.saveStatesWait)
        except:
            pass
        self.saveStatesWait = eg.scheduler.AddTask(3.0, self.saveStates)
    
    
    def calcMulti(self, indexes,vals):
        multi=0
        for i in indexes:
            multi+=int(vals[i])
        return multi
    
    
    connectedHttpClients={}
    registeredHttpClients={}
    connectedHttpClientsTimeout={}
    registeredHttpClientsTimeout={}
    
    def dataUpdate(self,codeOld,uniHashs,ip,reload=0):
        try:
            eg.scheduler.CancelTask(self.connectedHttpClientsTimeout[ip])
        except:
            pass
        try:
            eg.scheduler.CancelTask(self.registeredHttpClientsTimeout[ip])
        except:
            pass
        if ip not in self.registeredHttpClients or not self.registeredHttpClients[ip]:
            self.registerClient2(ip)
        self.connectedHttpClientsTimeout[ip]=eg.scheduler.AddTask(28.0, self.unregisterClient, ip)
        self.connectedHttpClients[ip]=True
        codeOld=json.loads(codeOld)
        uniHashs=json.loads(uniHashs)
        #print "remote device "+str(ip)+" has versions nr. "+str(codeOld)+", the latest are "+str(self.hashs)
        uniResult=[]
        tempHash=self.calcMulti(self.hashmodes,codeOld)
        tempHash2=tempHash+codeOld["uniUpdate"]
        while self.connectedHttpClients[ip]:
            while self.connectedHttpClients[ip] and tempHash2==self.calcMulti(self.hashmodes,self.hashs)+self.hashs["uniUpdate"]:
                time.sleep(0.3)
            if ip in self.uniUpdateIps and self.hashs["uniUpdate"]!=codeOld["uniUpdate"]:
                for currentVar in self.uniWatchedVarsByIp[ip]:
                    if currentVar not in uniHashs or self.uniUpdateHashOld[currentVar]!= uniHashs[currentVar]:
                        uniResult.append([currentVar,json.dumps(self.uniUpdateData[currentVar]),self.uniUpdateHashOld[currentVar]])
            if uniResult!=[] or tempHash!=self.calcMulti(self.hashmodes,self.hashs):
                break
            else:
                codeOld["uniUpdate"]=self.hashs["uniUpdate"]
        #print str(ip)+" will be reloaded"
        self.connectedHttpClients[ip]=False
        return json.dumps([self.hashs,uniResult])

    
    def dataUpdate2(self, mode):
        if mode=="scene":
            return json.dumps(self.sceneNames)
        elif mode=="sceneData":
            sheds=len(eg.plugins.SchedulGhost.plugin.data)
            nextRunTimes=[]
            for i in range(sheds):
                nextRunTimes.append(eg.plugins.SchedulGhost.plugin.NextRun(eg.plugins.SchedulGhost.plugin.data[i][2],eg.plugins.SchedulGhost.plugin.data[i][3]))
            return json.dumps([json.dumps(eg.plugins.SchedulGhost.plugin.data),json.dumps(nextRunTimes)])
        elif mode=="buttons":
            return json.dumps(self.buttonStates)
        elif mode=="devices":
            for dev in self.devices:
                ext=self.extensions[self.extensionsIDArray[dev[1]]]
                if self.States[u"devices"][dev[0]][u"power"]=="[on]" and self.States[u"devices"][dev[3]][u"power"]=="[on]" and "reloadFunction" in ext[4]:
                    try:
                        self.RequestDataFromClient(dev[3],ext[4]["reloadFunction"])
                    except:
                        pass
            return json.dumps(self.States["devices"])
        elif mode=="programs":
            for prog in self.programs:
                ext=self.extensions[self.extensionsIDArray[prog[1]]]
                if self.States[u"programs"][prog[0]][u"power"]=="[on]" and self.States[u"devices"][prog[3]][u"power"]=="[on]" and "reloadFunction" in ext[4]:
                    try:
                        self.RequestDataFromClient(prog[3],ext[4]["reloadFunction"])
                    except:
                        pass
            return json.dumps(self.States["programs"])
        else:
            return False

    
    def registerClient(self, ip):
        ip=ip[0]+"_"+str(ip[1])
        self.connectedHttpClients[ip]=False
        self.registerClient2(ip)
        return ip
        
        
    def registerClient2(self, ip):
        self.registeredHttpClients[ip]=True
        eg.TriggerEvent(prefix="O-MEGA", suffix="HTTP Client connected",payload=ip)

    
    def unregisterClient(self, ip):
        try:
            eg.scheduler.CancelTask(self.connectedHttpClientsTimeout[ip])
        except:
            pass
        try:
            eg.scheduler.CancelTask(self.registeredHttpClientsTimeout[ip])
        except:
            pass
        self.registeredHttpClientsTimeout[ip]=eg.scheduler.AddTask(5.0, self.unregisterClient2, ip)
        self.connectedHttpClients[ip]=False #+"load"
        return ip
        
    
    def unregisterClient2(self, ip):
        try:
            eg.scheduler.CancelTask(self.registeredHttpClientsTimeout[ip])
        except:
            pass
        self.registeredHttpClients[ip]=False
        eg.TriggerEvent(prefix="O-MEGA",suffix="HTTP Client disconnected",payload=ip)
    
    
    def valueSave(self, id,value):
        if id in self.buttonStates and self.buttonStates[id]["value"]!=value:
            oldValue=self.buttonStates[id]["value"]
            self.buttonStates[id]["value"]=value
            #print u'state '+id+' value = '+value
            eg.TriggerEvent(prefix="O-EVT", suffix="Button.Value."+id,payload={"id":id,"new":value,"old":oldValue})
            #eg.TriggerEvent(prefix="O-EVT", suffix="Button.Value",payload=[id,value])
            self.incrementHash("buttons")
   
   
    def updateDataFromClientPC(self, targetPC):
        clientPlugins=self.RequestData(self.devices[self.devicesIDArray[targetPC]][2]["host"], self.info.args[0], self.info.args[1], u'self.loadedPlugins')
        for plugin in clientPlugins:
            if plugin!="" and plugin not in self.allLoadedPlugins:
                self.allLoadedPlugins.append(plugin)
   
   
    def connectClientPC(self, targetPC, count=0):
        time.sleep(5)
        try:
            self.RequestData(self.devices[self.devicesIDArray[targetPC]][2]["host"], self.info.args[0], self.info.args[1], u'eg.TriggerEvent(prefix=\'O-CMD\',suffix=\'registerClientForServer\',payload='+unicode(json.dumps([self.thisPcName,targetPC,self.info.version]))+u')')
        except:
            if count<60:
                time.sleep(5)
                self.connectClientPC(targetPC,count+1)
            else:
                eg.TriggerEvent(prefix='O-MEGA', suffix='ClientPC.ConnectFailed', payload=targetPC)
            
    
    regPath = r'Software\EventGhost\O-MEGA'
    
    def saveToReg(self,name,val):
        try:
            key = _winreg.OpenKey(_winreg.HKEY_CURRENT_USER, self.regPath, 0, _winreg.KEY_ALL_ACCESS)
        except:
            key = _winreg.CreateKey(_winreg.HKEY_CURRENT_USER, self.regPath)
        _winreg.SetValueEx(key, name, 0, _winreg.REG_SZ, val)
        _winreg.CloseKey(key)
        return True
        
        
    def readFromReg(self,name):
        try:
            key = _winreg.OpenKey(_winreg.HKEY_CURRENT_USER, self.regPath, 0, _winreg.KEY_ALL_ACCESS)
            try:
                val = _winreg.QueryValueEx(key, name)[0]
            except:
                val = ""
            _winreg.CloseKey(key)
            return val
        except:
            return ""
        
            
    def getVarValue(self,vari):
        if self.pluginServer:
            return eval(vari)
        else:
            return self.RequestData(self.serverIP, self.info.args[0], self.info.args[1], vari)
    
    
    def saveMac(self,targetPc,newMac):
        if "mac" not in self.devices[self.devicesIDArray[targetPc]][2] or not fnmatch(self.devices[self.devicesIDArray[targetPc]][2]["mac"],"??-??-??-??-??-??"):
            self.devices[self.devicesIDArray[targetPc]][2]["mac"]=newMac
            self.devices2[self.devicesIDArray[targetPc]][2]=json.dumps(self.devices[self.devicesIDArray[targetPc]][2])
            self.saveConfig(self.devices2,"devices.json",False)
            return True
        return False
    
    
    def getGlobalDicts(self):
        self.ServerExecute(u'self.States["devices"]["'+self.thisPc+'"]["browser"]["root"]="'+self.thisPcRoot+'"')
        self.views=self.getVarValue('eg.plugins.OMEGA.plugin.views')
        self.viewsIDArray={}
        for i in xrange(len(self.views)):
            self.viewsIDArray[self.views[i][0]]=i
        self.files=self.getVarValue('eg.plugins.OMEGA.plugin.files')
        self.filesIDArray={}
        for i in xrange(len(self.files)):
            self.filesIDArray[self.files[i][0]]=i
        self.buttons=self.getVarValue('eg.plugins.OMEGA.plugin.buttons')
        self.buttonsIDArray=self.getVarValue('eg.plugins.OMEGA.plugin.buttonsIDArray')
        self.extensions=self.getVarValue('eg.plugins.OMEGA.plugin.extensions')
        self.extensionsIDArray={}
        for i in xrange(len(self.extensions)):
            self.extensionsIDArray[self.extensions[i][0]]=i
        self.interfaces=self.getVarValue('eg.plugins.OMEGA.plugin.interfaces')
        self.interfacesIDArray={}
        for i in xrange(len(self.interfaces)):
            self.interfacesIDArray[self.interfaces[i][0]]=i
        self.devices=self.getVarValue('eg.plugins.OMEGA.plugin.devices')
        self.devicesIDArray={}
        for i in xrange(len(self.devices)):
            self.devicesIDArray[self.devices[i][0]]=i
        self.programs=self.getVarValue('eg.plugins.OMEGA.plugin.programs')
        self.programsIDArray={}
        for i in xrange(len(self.programs)):
            self.programsIDArray[self.programs[i][0]]=i
        self.programsForPCsByType=self.getVarValue('eg.plugins.OMEGA.plugin.programsForPCsByType')
        self.primaryFilesTarget=self.getVarValue('eg.plugins.OMEGA.plugin.primaryFilesTarget')
        
        
    def createShortcut(self, path, target='', wDir='', icon=''):    
        ext = path[-3:]
        if ext == 'url':
            shortcut = file(path, 'w')
            shortcut.write('[InternetShortcut]\n')
            shortcut.write('URL=%s' % target)
            shortcut.close()
        else:
            shell = Dispatch('WScript.Shell')
            shortcut = shell.CreateShortCut(path)
            shortcut.Targetpath = target
            shortcut.WorkingDirectory = wDir
            if icon == '':
                pass
            else:
                shortcut.IconLocation = icon
            shortcut.save()
        
        
    def RequestDataFromClient(self, targetPC, function):
        if targetPC==self.thisPc:
            try:
                return self.ExecuteString(function)
            except:
                eg.PrintError("O-MEGA: Could not call function: "+function)
        else:
            try:
                return self.RequestData(self.devices[self.devicesIDArray[targetPC]][2]["host"], self.info.args[0], self.info.args[1], function)
            except socket.timeout, err:
                eg.PrintError("O-MEGA: Could not call function: "+function+" on client: "+targetPC+", the connection timed out. The client will be shown as [off]!")
                self.ShowDeviceAsOff(targetPC)
            except Exception, err:
                eg.PrintError("O-MEGA: Could not call function: "+function+" on client: "+targetPC+". %s" % str(err))
        return None
        
        
    def ShowDeviceAsOff(self, deviceID):
        self.LogWrapper.desolveDependencie(self.devices[self.devicesIDArray[deviceID]],None,"devices")
        oldState=self.States[u"devices"][deviceID][u"power"]
        if oldState!="[off]":# and oldState!="#[off]":
            id=u"devices/"+deviceID+u"/power"
            self.buttonStates[id]["state"]="#[off]"
            self.States["devices"][deviceID]["power"]="[off]"
            self.incrementHash("devices")
            self.incrementHash("buttons")
            eg.TriggerEvent(prefix="O-EVT", suffix="Button.State."+id+".#[off]",payload={"id":id,"new":"#[off]","old":oldState})
        
            
    def changePassword(self, userId, oldPw, newPw):
        if userId in self.usersIDArray:
            if oldPw == self.users[self.usersIDArray[userId]][1]:
                self.users[self.usersIDArray[userId]][1]=newPw
                self.saveConfig(self.users,u'users.json',False)
                return True
        return False
#--------------------------------Scene Start-----------------------------------#
    lastSceneConditionResult={}
    sceneWait={}
    macroWait={}
    
    def sceneCheckCondition(self,data):
        return str(self.sceneCondition(1,json.loads(data),True))
    
    
    def sceneLoad(self):
        eg.plugins.SchedulGhost.ReloadXML()
        return json.dumps(eg.plugins.SchedulGhost.plugin.data)
    
    
    def sceneCondition(self, conditiontype,dataArr,lastSceneConditionResult=True):
        if conditiontype==1:
            result=False
            for i in range(0,len(dataArr),4):
                result=self.sceneConditionTwo(dataArr[i],dataArr[i+1],dataArr[i+2])
                if (i+3)<len(dataArr):
                    if dataArr[i+3]=="OR":
                        if result:
                            return True
                    elif dataArr[i+3]=="AND" and result:
                        pass
                    else:
                        return False
            return result
        elif conditiontype==2 and lastSceneConditionResult==False:
            return True
        else:
            return False
                
            
    def sceneConditionTwo(self,data1,mode,data2):
        val=""
        data1parts=unicode(data1).split("/")
        if len(data1parts)==4 or len(data1parts)==3:
            if data1 in self.buttonsIDArray:
                button=self.buttons[self.buttonsIDArray[data1]]
                if button[6]=={} and button[2]=="power" and button[1].split("/")[0]!="interfaces":
                    val=self.buttonStates[button[1]+"/"+button[2]]["state"]
                elif data1 in self.buttonStates:
                    val=self.buttonStates[data1]["state"]
        else:
            try:
                val=eval(data1)
            except:
                val=data1
        if isinstance(data2, basestring) and data2[0]=="=":
            data2=data2[1:]
            if mode=="IS" and val==data2:
                return True
            elif mode=="NOT" and val!=data2:
                return True
            else:
                return False
        elif mode=="IS" and (val==data2 or val==(u'#'+unicode(data2))):
            return True
        elif mode=="NOT" and (val!=data2 and val!=(u'#'+unicode(data2))):
            return True
        elif mode=="PYTHON":
            try:
                tempExp=json.loads(data2)
                tempExp=self.replaceTimeVars(tempExp)
                if "{value}" in tempExp:
                    if unicode(data1) in self.buttonStates:
                        tempExp=tempExp.replace('{value}',unicode(self.buttonStates[unicode(data1)]['value']))
                    else:
                        eg.PrintError("O-MEGA: Scene: Could not get value of button ->"+unicode(data1))
                i=len(tempExp)
                while i > 0:
                    i=tempExp.rfind('self.States[',0,i)
                    if i!=-1:
                        e=[]
                        e.append(tempExp.find(' ',i))
                        e.append(tempExp.find('<',i))
                        e.append(tempExp.find('>',i))
                        e.append(tempExp.find('=',i))
                        e.append(tempExp.find('!',i))
                        end=len(tempExp)
                        for element in e:
                            if element!=-1 and element<end:
                                end=element
                        try:
                            temp=eval(tempExp[i:end])
                            tempExp=tempExp[:i]+unicode(temp)+tempExp[end:]
                        except:
                            pass
                print "O-MEGA: Scene: Checking condition ->"+tempExp
                return eval(tempExp)
            except:
                eg.PrintError("O-MEGA: Scene: Something is wrong with the python expression ->"+unicode(data2))
                return False
        else:
            return False
               
            
    def sceneAction(self,id,pos=0,remove=False,behave=0):
        pos2=pos
        if behave==1:
            pos2="*"
            remove=True
        if remove:
            self.removeActionEventsFor2('eg.plugins.OMEGA.plugin.sceneAction('+str(id)+','+str(pos2)+',True)')
            try:
                eg.scheduler.CancelTask(self.sceneWait[id])
            except:
                pass
        if pos==0:
            if self.sceneNames[self.sceneNamesIds[id]][2]=="[activate]" and behave!=1:
                if behave==2:
                    eg.scheduler.AddTask(1.0, self.sceneAction, id, 0, False, behave)
                return False
            else:
                if id not in self.lastSceneConditionResult:
                    self.lastSceneConditionResult[id]={}
                #self.hashs["sceneData"]+=1
                oldState=self.sceneNames[self.sceneNamesIds[id]][2]
                self.sceneNames[self.sceneNamesIds[id]][2]="[activate]"
                self.hashs["scene"]+=1
                eg.TriggerEvent(prefix="O-EVT", suffix="Scene.State."+str(id)+".[activate]",payload={"id":id,"new":"[none]","old":oldState,"name":self.sceneNames[self.sceneNamesIds[id]][1]})
        if self.sceneNames[self.sceneNamesIds[id]][2]!="[activate]":
            return False
        try:
            eg.scheduler.CancelTask(self.saveSceneStateWait)
        except:
            pass
        data=self.sceneActions[unicode(id)]
        while pos<len(data):
            activated=1
            if len(data[pos])>4:
                activated=int(data[pos][4])
            if activated==1:
                self.sceneNames[self.sceneNamesIds[id]][4]=pos
                self.hashs["scene"]+=1
                runAction=json.loads(data[pos][0])
                level=int(data[pos][1])
                conditiontype=int(data[pos][2])
                if conditiontype==0:
                    if runAction["suffix"]=="[wait]":
                        pos+=1
                        try:
                            self.saveActionEventsFor2('eg.plugins.OMEGA.plugin.sceneAction('+str(id)+','+str(pos)+',True)',runAction["payload"][0])
                        except:
                            eg.PrintError('O-MEGA: Event string "'+str(runAction["payload"][0])+'" is not valid and will be ignored!')
                        if int(runAction["payload"][1])==0 and int(runAction["payload"][2])>0:
                            self.sceneWait[id]=eg.scheduler.AddTask(float(runAction["payload"][2]), self.sceneAction, int(id), pos, True)
                        elif int(runAction["payload"][1])==1:
                            targetTime=time.mktime((time.localtime().tm_year, time.localtime().tm_mon, time.localtime().tm_mday, int(runAction["payload"][2]), int(runAction["payload"][3]), int(runAction["payload"][4]), 0,0,-1))
                            self.sceneWait[id]=eg.scheduler.AddTaskAbsolute(targetTime, self.sceneAction, int(id), pos, True)
                        break
                        #return True
                    else:
                        suffixParts=runAction["suffix"].split(".")
                        if suffixParts[-1]=="browserCopy" and suffixParts[-2]=="PC_WIN" and runAction["payload"]["data"]["wait"]:
                            pos+=1
                            runAction["payload"]["data"]["scene"]=int(id)
                            runAction["payload"]["data"]["scenePos"]=pos
                            eg.TriggerEvent(prefix="O-MEGA",suffix=runAction["suffix"],payload=runAction["payload"])
                            #tempEvent=self.LogWrapper.emptyEvent(prefix="O-MEGA",suffix=runAction["suffix"],payload=runAction["payload"])
                            #self.LogWrapper.LogEvent(tempEvent)
                            return True
                        else:
                            eg.TriggerEvent(prefix="O-MEGA",suffix=runAction["suffix"],payload=runAction["payload"])
                            #tempEvent=self.LogWrapper.emptyEvent(prefix="O-MEGA",suffix=runAction["suffix"],payload=runAction["payload"])
                            #self.LogWrapper.LogEvent(tempEvent)
                else:
                    if level not in self.lastSceneConditionResult[id]:
                        self.lastSceneConditionResult[id][level]=True
                    self.lastSceneConditionResult[id][level]=self.sceneCondition(conditiontype,runAction,self.lastSceneConditionResult[id][level])
                    if self.lastSceneConditionResult[id][level]==False:
                        while len(data)-1>pos and int(data[pos+1][1])>level:
                            pos+=1
            pos+=1
        if pos>len(data)-1:
            #if self.sceneNames[self.sceneNamesIds[id]][2]!="[none]":
            self.removeActionEventsFor2('eg.plugins.OMEGA.plugin.sceneAction('+str(id)+',*,True)')
            try:
                eg.scheduler.CancelTask(self.sceneWait[id])
            except:
                pass
            oldState=self.sceneNames[self.sceneNamesIds[id]][2]
            self.sceneNames[self.sceneNamesIds[id]][2]="[none]"
            self.hashs["scene"]+=1
            eg.TriggerEvent(prefix="O-EVT", suffix="Scene.State."+str(id)+".[none]",payload={"id":id,"new":"[none]","old":oldState,"name":self.sceneNames[self.sceneNamesIds[id]][1],"source":"sceneEnd"})
        self.saveSceneStateWait = eg.scheduler.AddTask(3.0, self.saveConfig, self.sceneNames, "sceneNames.json")
        return True
                
                
    def getSceneActions(self,sceneid):
        return json.dumps(self.sceneActions[unicode(sceneid)])
        
        
    def sceneSave(self,id,newData):
        newData=json.loads(newData)
        eg.plugins.SchedulGhost.AddSchedule(unicode(newData))
        eg.plugins.SchedulGhost.DataToXML()
        self.hashs["sceneData"]+=1
        
        
    def sceneSaveActions(self,id,newData):
        id=unicode(id)
        actionData=json.loads(unquote(newData))
        self.sceneActions[id]=actionData
        self.saveConfig(self.sceneActions,"sceneActions.json")
        self.hashs["sceneData"]+=1
        
        
    def sceneRemove(self,id):
        id=int(id)
        for i in xrange(len(self.sceneNames)):
            if self.sceneNames[i][0]==id:
                self.sceneNames.pop(i)
                break
        del self.sceneActions[unicode(id)]
        self.sceneNamesIds={}
        for i in xrange(len(self.sceneNames)):
            self.sceneNamesIds[self.sceneNames[i][0]]=i
        self.removeActionEventsFor("eg.plugins.SchedulGhost.RunScheduleImmediately(u'scene"+unicode(id)+"',True)")
        try:
            eg.scheduler.CancelTask(self.sceneWait[id])
        except:
            pass
        self.saveConfig(self.sceneNames,"sceneNames.json")
        self.saveConfig(self.sceneActions,"sceneActions.json")
        eg.plugins.SchedulGhost.DeleteSchedule("scene"+unicode(id))
        eg.plugins.SchedulGhost.DataToXML()
        self.hashs["scene"]+=1
        self.hashs["sceneData"]+=1
        
        
    def sceneRename(self,id,newName):
        id=int(id)
        newName=unquote(newName)
        self.sceneNames[self.sceneNamesIds[id]][1]=newName
        self.saveConfig(self.sceneNames,"sceneNames.json")
        self.hashs["scene"]+=1
        
        
    def sceneNew(self, view):
        datalen=len(eg.plugins.SchedulGhost.plugin.data)
        usednumbers=[]
        for i in range(0,datalen):
            if eg.plugins.SchedulGhost.plugin.data[i][1][:5]=="scene":
                usednumbers.append(int(eg.plugins.SchedulGhost.plugin.data[i][1][5:]))
        i=0
        while i in usednumbers:
            i+=1
        nr=i
        data=[0, u'scene'+unicode(nr), 0, [u'00:00:00', u'00:00:00', '2000-01-01', 0], '', 'O-CMD', 'sceneStart', '', unicode(nr)]
        self.sceneNames.append([int(nr),"","[none]",0,0,0,0,0,[view]])
        self.sceneNamesIds={}
        self.sceneActions[unicode(nr)]=[]
        for i in xrange(len(self.sceneNames)):
            self.sceneNamesIds[self.sceneNames[i][0]]=i
        self.saveConfig(self.sceneNames,"sceneNames.json")
        self.saveConfig(self.sceneActions,"sceneActions.json")
        eg.plugins.SchedulGhost.AddSchedule(unicode(data))
        eg.plugins.SchedulGhost.DataToXML()
        self.hashs["scene"]+=1
        self.hashs["sceneData"]+=1
        
    
    def sceneSetting(self,id,settingId,value):
        id=int(id)
        settingId=int(settingId)
        #value=int(value)
        if len(self.sceneNames[self.sceneNamesIds[id]])==settingId:
            self.sceneNames[self.sceneNamesIds[id]].append(value)
            self.saveConfig(self.sceneNames,"sceneNames.json")
            self.hashs["scene"]+=1
        elif self.sceneNames[self.sceneNamesIds[id]][settingId]!=value:
            self.sceneNames[self.sceneNamesIds[id]][settingId]=value
            self.saveConfig(self.sceneNames,"sceneNames.json")
            self.hashs["scene"]+=1
            
            
    def sceneMove(self,id,direction,view):
        id=int(id)
        oldindex=self.sceneNamesIds[id]
        level=self.sceneNames[oldindex][3]
        changed=False
        if direction=="up":
            newindex=self.sceneNamesIds[id]-1
            while newindex >= 0:
                if level == self.sceneNames[newindex][3] and (view=="-" or view in self.sceneNames[newindex][8]):
                    self.sceneNames.insert(newindex, self.sceneNames.pop(oldindex))
                    changed=True
                    break
                newindex-=1
        elif direction=="down":
            newindex=self.sceneNamesIds[id]+1
            while newindex < len(self.sceneNames):
                if level == self.sceneNames[newindex][3] and (view=="-" or view in self.sceneNames[newindex][8]):
                    self.sceneNames.insert(newindex, self.sceneNames.pop(oldindex))
                    changed=True
                    break
                newindex+=1
        if changed:
            self.sceneNamesIds={}
            for i in xrange(len(self.sceneNames)):
                self.sceneNamesIds[self.sceneNames[i][0]]=i
            self.saveConfig(self.sceneNames,"sceneNames.json")
            self.hashs["scene"]+=1
#---------------------------------Scene End------------------------------------#
    def ImportXML(self,targetFile,xmlstring):
        result=True
        egFileTree = ET.parse(targetFile)
        egFileRoot = egFileTree.getroot()
        #create O-MEGA_Extensions folder if not exist
        extensionsFolder = self.searchForXmlRecursive("O-MEGA_Extensions", egFileRoot)
        if (extensionsFolder is None):
            print "O-MEGA: O-MEGA_Extensions Folder not found! Will create it!"
            extensionsFolder = ET.Element("Folder")
            extensionsFolder.set("Expanded", "False")
            extensionsFolder.set("Name", "O-MEGA_Extensions")
            egFileRoot.append(extensionsFolder)
        else:
            extensionsFolder.clear()
            extensionsFolder.set("Expanded", "False")
            extensionsFolder.set("Name", "O-MEGA_Extensions")
        #import new extensions folder
        importRoot = ET.fromstring(xmlstring)
        for folder in importRoot.findall("Folder"):
            print "O-MEGA: Checking prerequisites for type ", folder.get("Name")
            if folder.get("Name") in self.extensionsIDArray:
                prereqsMet=True
                missingPlugins=""
                for pluginToCheck in self.extensions[self.extensionsIDArray[folder.get("Name")]][3]:
                    if pluginToCheck!="" and pluginToCheck not in self.loadedPlugins:
                        prereqsMet=False
                        missingPlugins+=pluginToCheck+","
                if prereqsMet:
                    print "O-MEGA: Importing Folder", folder.get("Name"), "to .xml"
                    extensionsFolder.append(folder)
                else:
                    eg.PrintError("O-MEGA: "+folder.get("Name")+" cannot be imported, because the plugins "+missingPlugins[:-1]+" are missing, please add the plugins to this configuration and restart EventGhost!")
                    result=False
            else:
                eg.PrintError("O-MEGA: "+folder.get("Name")+" cannot be imported, the type is unknown by your configuration")
                result=False
        #write XML file
        egFileTree.write(targetFile)
        return result
    

    def searchForXmlRecursive(self, name, root):
        for folder in root.findall("Folder"):
            #print folder.get("Name")
            if folder.get("Name") == name:
                return folder
            else:
                result = self.searchForXmlRecursive(name, folder)
                if result:
                    return result
        return None

    
    def GetOMEGAXML(self, targetPC=None):
        extensionsToCopy=[]
        if targetPC:
            for i in self.devices:
                if i[3]==targetPC:
                    if i[1] not in extensionsToCopy:
                        extensionsToCopy.append(i[1])
            for i in self.interfaces:
                if i[3]==targetPC:
                    if i[1] not in extensionsToCopy:
                        extensionsToCopy.append(i[1])
            for i in self.programs:
                if i[3]==targetPC:
                    if i[1] not in extensionsToCopy:
                        extensionsToCopy.append(i[1])
        data=eg.document.root.GetXmlString()
        #export eg-xml
        egFileRoot = ET.fromstring(data)
        #find extensions folder
        extensionsFolder = self.searchForXmlRecursive("O-MEGA_Extensions", egFileRoot)
        #generate empty XML structure
        root = ET.Element("EventGhost")
        root.set("Version", str(eg.revision))
        if (extensionsFolder is None):
            eg.PrintError("O-MEGA: O-MEGA_Extensions Folder not found!!")
        else:
            for folder in extensionsFolder.findall("Folder"):
                if targetPC==None or folder.get("Name") in extensionsToCopy:
                    root.append(folder)
        data=ET.tostring(root)
        return data
    
    
    def UpFunc2(self,eventRef):
        newEvent=self.cachedEvents[eventRef]
        #print "up2!"
        newEvent.SetShouldEnd()
        del self.cachedEvents[eventRef]
        return True
        
        
    def ExecuteString(self,command):
        try:
            return eval(command)
        except:
            exec(command)
            if command[:12] == "self.States[" or command[:31] == "eg.plugins.OMEGA.plugin.States[":#efficient?
                for mode in self.hashmodes:#efficient?
                    beg=command.find("[")#efficient?
                    if mode in command[beg:command.find("]",beg)]:#efficient?
                        self.incrementHash(mode)#efficient?
                        break#efficient?
            return True
    

    def ServerExecute(self,command):
        if self.pluginServer:
            return self.ExecuteString(command)
        else:
            if self.serverOnline:
                return self.RequestData(self.serverIP, self.info.args[0], self.info.args[1], command)
            else:
                eg.PrintError("O-MEGA: Server ("+self.serverIP+":"+str(self.info.args[0])+") is not online!")
        
        
    def ResolveAudioDependencies(self,event):
        return self.ServerExecute(u'self.ResolveAudioDependenciesTwo(\''+self.thisPc+u'\',\''+event.prefix+u'\',\''+event.suffix+u'\','+unicode(event.payload)+u')')
        
        
    def ResolveAudioDependenciesTwo(self,targetPC,prefix,suffix,payload):
        #payload=json.loads(unquote(payload))
        deviceprogid=payload["target"]
        suffParts=suffix.split(".")
        tempEvent=self.LogWrapper.emptyEvent(prefix="O-MEGA",suffix="EXT."+targetPC+"."+suffix,payload=payload)
        target=suffParts[0]+u"/"+deviceprogid+u"/power"
        interface=None
        if "activeAudioEndpoint" in self.States["devices"][targetPC]:
            infid=self.States["devices"][targetPC]["activeAudioEndpoint"]
            if infid[0]=="#":
                infid=infid[1:]
            interface=self.interfacesIDArray[infid]
            audioInterface=self.interfaces[interface]
        if target not in self.LogWrapper.powerTimers or self.LogWrapper.powerTimers[target]["targetState"]!="[on]":
            if not self.LogWrapper.turnO(deviceprogid,tempEvent,"[on]",suffParts[0]):
                return False
        if not interface or ("hifiId" in audioInterface[2] and audioInterface[2]["hifiId"] in self.hifiDevices):
            id=self.primaryFilesTarget[suffParts[0]+'/'+deviceprogid][0]#!!!!!!!!!!!!!!!!
            thisFiles=self.files[id]
            primHifiID=""
            if interface:
                primHifiID=audioInterface[2]["hifiId"]
            else:
                connectedHifis=[]
                for hifiDevice in self.hifiDevices:
                    if hifiDevice in thisFiles[4] and thisFiles[4][hifiDevice][0]!="":
                        connectedHifis.append(hifiDevice)
                if len(connectedHifis)==1:
                    primHifiID=connectedHifis[0]
                elif len(connectedHifis)>1 and "view" in payload and payload["view"] in self.viewsIDArray and self.views[self.viewsIDArray[payload["view"]]][1] in connectedHifis:
                    primHifiID=self.views[self.viewsIDArray[payload["view"]]][1]
            if primHifiID!="":
                primHiFiDevice=self.devices[self.devicesIDArray[primHifiID]]
                if not self.LogWrapper.turnO(primHiFiDevice[0],None,"[on]","devices"):
                    return False
                temp=self.States["devices"][primHiFiDevice[0]]
                if "input" in temp and temp["input"] not in thisFiles[4][primHiFiDevice[0]]:
                    eg.TriggerEvent(prefix="O-MEGA", suffix='EXT.'+primHiFiDevice[3]+'.devices.'+primHiFiDevice[1]+'.input',payload={u"target":primHiFiDevice[0],u"targetState":'[value]',u"targetValue":[thisFiles[4][primHiFiDevice[0]][0]],u"data":{"inputId":thisFiles[4][primHiFiDevice[0]][0]}})
                    eg.scheduler.AddTask(6.0, eg.TriggerEvent, prefix=tempEvent.prefix, suffix=tempEvent.suffix, payload=tempEvent.payload)
                    return False
        return True


    def ActiveMedia(self,action,targetState,view="",targetValue=""):
        if action not in self.mediaCfgIDArray:
            eg.PrintError("O-MEGA: '"+action+"' is not a valid media action!")
            return False
        items=[]
        for device in self.primaryFilesTarget:
            item=device.split("/")
            for fileId in self.primaryFilesTarget[device]:
                file=self.files[fileId]
                targetValue2=targetValue
                primHifiID=""
                value=0
                filePrimButtonState=self.States[item[0]][item[1]][u"power"]
                if file[2] in self.mediaPlayers:
                    connectedHifis=[]
                    for hifiDevice in self.hifiDevices:
                        if hifiDevice in file[4] and file[4][hifiDevice][0]!="":
                            connectedHifis.append(hifiDevice)
                    if len(connectedHifis)==1:
                        primHifiID=connectedHifis[0]
                    elif len(connectedHifis)>1 and view in self.viewsIDArray and self.views[self.viewsIDArray[view]][1] in connectedHifis:
                        primHifiID=self.views[self.viewsIDArray[view]][1]
                    if view != "" and view in file[10]:
                        value+=100
                    if primHifiID=="" and view in self.viewsIDArray:
                        primHifiID=self.views[self.viewsIDArray[view]][1]
                    primHiFiDevice=None
                    if primHifiID!="":
                        primHiFiDevice=self.devices[self.devicesIDArray[primHifiID]]
                        primHiFiDeviceState=self.States["devices"][primHiFiDevice[0]]
                    if filePrimButtonState=="[on]" or filePrimButtonState=="#[on]":
                        value+=2
                        if "play" in self.States[item[0]][item[1]] and "pause" in self.States[item[0]][item[1]]:
                            if (self.States[item[0]][item[1]]["play"]=="[on]" or self.States[item[0]][item[1]]["play"]=="#[on]") and not (self.States[item[0]][item[1]]["pause"]=="[on]" or self.States[item[0]][item[1]]["pause"]=="#[on]"):
                                value+=2
                            elif self.States[item[0]][item[1]]["pause"]=="[on]" or self.States[item[0]][item[1]]["pause"]=="#[on]":
                                value+=1
                    if (primHifiID!="" and (primHiFiDeviceState["power"]=="[on]" or primHiFiDeviceState["power"]=="#[on]")) and (primHifiID=="" or "input" not in primHiFiDeviceState or (primHiFiDevice[0] in file[4] and primHiFiDeviceState["input"] in file[4][primHiFiDevice[0]])):
                        value+=5
                    elif primHifiID=="" or "input" not in primHiFiDeviceState or (primHiFiDevice[0] in file[4] and primHiFiDeviceState["input"] in file[4][primHiFiDevice[0]]):
                        value+=1
                elif item[1] in self.hifiDevices and self.mediaCfg[self.mediaCfgIDArray[action]][3]:
                    connectedHifis=[]
                    for hifiDevice in self.hifiDevices:
                        if hifiDevice in file[4] and file[4][hifiDevice][0]!="":
                            connectedHifis.append(hifiDevice)
                    if len(connectedHifis)==1:
                        primHifiID=connectedHifis[0]
                    elif len(connectedHifis)>1 and view in self.viewsIDArray and self.views[self.viewsIDArray[view]][1] in connectedHifis:
                        primHifiID=self.views[self.viewsIDArray[view]][1]
                    elif view in self.viewsIDArray:
                        primHifiID=self.views[self.viewsIDArray[view]][1]
                    if view != "" and item[1] == self.views[self.viewsIDArray[view]][1]:
                        value+=10
                    if view != "" and view in file[10]:
                        value+=100
                    if filePrimButtonState=="[on]" or filePrimButtonState=="#[on]":
                        value+=2
                #else:
                #    print item[1]
                if action=="input" and targetState=="[value]" and value>0:
                    if targetValue in self.filesIDArray:
                        if primHifiID in self.files[self.filesIDArray[targetValue]][4] and self.files[self.filesIDArray[targetValue]][4][primHifiID][0]!="":
                            targetValue2=self.files[self.filesIDArray[targetValue]][4][primHifiID][0]
                            value+=200
                    else:
                        value+=150
                if value>0:
                    items.append([item,value,primHifiID,targetValue2,file[0]])
        items=sorted(items, key=lambda x: x[1])
        items=items[::-1]
        #print items
        if len(items)==0 or action=="input" and targetState=="[value]" and items[0][1]<150:
            eg.PrintError("O-MEGA: No media devices found, will do nothing!")
            return False
        targetValue=items[0][3]
        primHifiID=items[0][2]
        item=items[0][0]
        kind=item[0]
        if kind=="devices":
            thing=self.devices[self.devicesIDArray[item[1]]]
        elif kind=="programs":
            thing=self.programs[self.programsIDArray[item[1]]]
            if primHifiID=="":
                primHifiID=thing[3]
            #if thing[2]["forwardToMasterAudio"]=="1" and primHifiID!="":
            #    pass
            #else:
            #    primHifiID=thing[3]
        else:
            eg.PrintError("O-MEGA: Media command invalid!")
            return False
        if self.mediaCfg[self.mediaCfgIDArray[action]][3] and thing[2]["forwardToMasterAudio"]=="1" and primHifiID!="":
            thing=self.devices[self.devicesIDArray[primHifiID]]
            kind="devices"
        #print "Media is: "+kind+u"/"+thing[0]
        if action=="power":
            thisFilesPrimButtonID=kind+u"/"+thing[0]+u"/power"
            if targetState != "[on]" and targetState != "[off]":
                thisFilesPrimButtonState=self.buttonStates[thisFilesPrimButtonID]["state"]
                if thisFilesPrimButtonState=="[on]" or thisFilesPrimButtonState=="#[on]":
                    targetState="[off]"
                else:
                    targetState="[on]"
            eg.TriggerEvent(prefix="O-MEGA", suffix="CMD.buttons", payload={"target":thisFilesPrimButtonID,"targetState":targetState,"view":view,"targetValue":[targetValue,None,None,None]})
            #tempEvent=self.LogWrapper.emptyEvent(prefix="O-MEGA", suffix="CMD.buttons", payload={"target":thisFilesPrimButtonID,"targetState":targetState,"view":view,"targetValue":[targetValue,None,None,None]}))
            #self.LogWrapper.LogEvent(tempEvent)
        else:
            #eg.TriggerEvent(prefix="O-MEGA", suffix="EXT."+thing[3]+"."+kind+"."+thing[1]+"."+action, payload={"target":thing[0],"targetState":targetState,"view":view,"targetValue":[targetValue,None,None,None]})
            tempEvent=self.LogWrapper.emptyEvent(prefix="O-MEGA", suffix="EXT."+thing[3]+"."+kind+"."+thing[1]+"."+action, payload={"target":thing[0],"targetState":targetState,"view":view,"targetValue":[targetValue,None,None,None]})
            wx.CallAfter(self.LogWrapper.LogEvent,tempEvent,True)
                
                
    def getFilesForDropdown(self,dropdownid):
        if not os.path.exists(self.configDir+u'\\web\\img\\'+dropdownid):
            os.mkdir(self.configDir+u'\\web\\img\\'+dropdownid)
        tempFiles=os.listdir(self.configDir+u'\\web\\img\\'+dropdownid)
        try:
            tempFiles.remove("Thumbs.db")
        except:
            pass
        return json.dumps(tempFiles)
        
        
    def getAllLoadedPlugins(self):
        return self.allLoadedPlugins
        
        
    def getTimestamp(self):
        return time.strftime("%d;%m;%Y;%H;%M;%S", time.localtime()).split(";")


    def replaceTimeVars(self, string):
        timestamp=time.localtime()
        if "{time}" in string or "{TIME}" in string:
            timestring=str(timestamp.tm_hour).zfill(2)+"-"+str(timestamp.tm_min).zfill(2)+"-"+str(timestamp.tm_sec).zfill(2)
            string=string.replace("{TIME}",timestring).replace("{time}",timestring)
        if "{date}" in string or "{DATE}" in string:   
            datestring=str(timestamp.tm_year)+"-"+str(timestamp.tm_mon).zfill(2)+"-"+str(timestamp.tm_mday).zfill(2)
            string=string.replace("{DATE}",datestring).replace("{date}",datestring)
        return string

#---------------------------------------------------------------------------
    def EndLastEnduringEvent(self):
        if self.lastEnduringEvent:
            self.lastEnduringEvent.SetShouldEnd()
        

    def ProcessTheArguments(
        self,
        handler,
        methodName,
        args,
        kwargs,
        targetpc,
    ):
        sender = handler.clAddr
        result = None
        if methodName == "TriggerEvent":
            if 'payload' in kwargs:
                if isinstance(kwargs['payload'], (str, unicode)):
                    if kwargs['payload'] == 'client_address':
                        kwargs['payload'] = [sender]
                elif isinstance(kwargs['payload'], (list, tuple)):
                    tmp = list(kwargs['payload'])
                    for i, item in enumerate(tmp):
                        if item == 'client_address':
                            tmp[i] = sender
                    kwargs['payload'] = tmp
            if 'prefix' not in kwargs:
                kwargs['prefix'] = "O-HTTP"
            eg.TriggerEvent(*args, **kwargs)
        elif methodName == "TriggerEnduringEvent":
            self.EndLastEnduringEvent()
            if 'prefix' not in kwargs:
                kwargs['prefix'] = "O-HTTP"
            self.lastEnduringEvent=eg.TriggerEnduringEvent(*args, **kwargs)
            handler.repeatTimer.Reset(2000)
        elif methodName == "RepeatEnduringEvent":
            handler.repeatTimer.Reset(2000)
        elif methodName == "EndLastEvent":
            handler.repeatTimer.Reset(None)
            #self.EndLastEvent()
            self.EndLastEnduringEvent()
        elif methodName == "RegisterClient":
            result = self.registerClient(handler.clAddr)
        else:
            if not targetpc or targetpc == self.thisPc:
                result = self.ExecuteWebFunction(methodName,args,kwargs)
            else:
                print "self.ExecuteWebFunction(\""+methodName+"\","+unicode(args)+","+unicode(kwargs)+")"
                result = self.RequestDataFromClient(targetpc, "self.ExecuteWebFunction(\""+methodName+"\","+unicode(args)+","+unicode(kwargs)+")")
        return result
    

    def ExecuteWebFunction(
        self,
        methodName,
        args,
        kwargs,
    ):
        result = None
        if methodName in self.registeredWebFunctions.keys():
            try:
                result = self.registeredWebFunctions[methodName](*args, **kwargs)
            except Exception, err:
                eg.PrintError(u"O-MEGA: Web-request failed - method: " + methodName + u" args: " + unicode(args) + u" kwargs: " + unicode(kwargs))
                print_exc()
        else:
            eg.PrintError(u"O-MEGA: Web-request failed - method: " + methodName + u" is not registered!")
        return result
        
    
    def RegisterWebFunction(self, function, alias):
        self.registeredWebFunctions[alias]=function
        return True
        
        
    def UnregisterWebFunction(self, alias):
        if alias in self.registeredWebFunctions:
            del self.registeredWebFunctions[alias]
            return True
        return False
    

    def ReplaceCharForCompare(self,text):
        text=self.uml.unescape(unicode(text).lower().replace("&nbsp;"," "))
        return text.replace(u"ä","a").replace(u"ü","u").replace(u"ö","o").replace(u"ß","s").replace("<br/>"," ").replace("<br>"," ").replace("  "," ").strip()
    
        
    def InterpretSpokenCommand(self, text, targetUser, defaultView=""):
        command = " "+self.ReplaceCharForCompare(text)+" "
        commandParts=[0]
        newIndex=0
        while newIndex!=-1:
            newIndex=command.find(", ",newIndex)
            if newIndex!=-1:
                commandParts.append(newIndex)
                newIndex+=1
        command = command.replace(","," ").replace("."," ")
        languageId=0
        matchingViews=[["-",-1,"","v",0,0]]
        if targetUser in self.userSettings:
            languageId=self.userSettings[targetUser]["language"]
            if defaultView=="":
                try:
                    view=self.userSettings[targetUser]["selectedView"]
                    viewIndex=self.viewsIDArray[view]
                    matchingViews=[[view,-1,"","v",self.views[viewIndex][2],viewIndex]]
                except:
                    pass
            elif defaultView in self.viewsIDArray:
                viewIndex=self.viewsIDArray[defaultView]
                matchingViews=[[defaultView,-1,"","v",self.views[viewIndex][2],viewIndex]]
        matchingStates=[]
        viewIndicators=[]
        for state in self.dictionary["statesCfg.jsonvoice"]:
            stateNames=self.dictionary["statesCfg.jsonvoice"][state][languageId].split(",")
            for stateName in stateNames:
                stateName=self.ReplaceCharForCompare(stateName)
                if stateName != "":
                    newIndex=0
                    while newIndex!=-1:
                        newIndex=command.find(" "+stateName+" ",newIndex)
                        if newIndex!=-1:
                            newIndex+=1
                            if state=="[set]":
                                valueStart=newIndex+len(stateName)+1
                                valueEnd=command.find(" ",valueStart)
                                value=command[valueStart:valueEnd]
                                value=value.replace(u"%",u"").replace(u"°C",u"").replace(u"°F",u"").replace(u"°",u"").replace(u",",u".")
                                if value!="":
                                    for state2 in ["and"]:
                                        state2Names=self.dictionary["statesCfg.jsonvoice"][state2][languageId].split(",")
                                        for state2Name in state2Names:
                                            state2Name=self.ReplaceCharForCompare(state2Name)
                                            if value == state2Name:
                                                state=state2
                                                break
                                        if state!="[set]":
                                            break
                                    if state=="[set]":
                                        matchingStates.append([state,newIndex,stateName,"s",value])
                            elif state=="and":
                                commandParts.append(newIndex)
                            elif state=="inthe":
                                viewIndicators.append([state,newIndex,stateName,"s"])
                            else:
                                matchingStates.append([state,newIndex,stateName,"s"])
        if len(matchingStates)>0:
            matchingStates=sorted(matchingStates, key=lambda x: x[1])
            if matchingStates[-1][0]=="again" or matchingStates[-1][0]=="times":
                timesFound=False
                times=1
                somethingElseFound=False
                for tempState in matchingStates:
                    if tempState[0]=="times":
                        timesFound=True
                    elif tempState[0][0]=="N":
                        times=int(tempState[0][1:])
                    elif tempState[0]=="again":
                        pass
                    else:
                        somethingElseFound=True
                        break
                if not somethingElseFound:
                    if not timesFound:
                        times=1
                    processThread = Thread(
                        target=self.processInterpretCommandThread,
                        args=(self.spokenCommandCache[targetUser]["lastCommand"], targetUser, times, )
                    )
                    processThread.start()
                    return True
        matchingMediaActions=[]
        for actionId in self.dictionary["mediaCfg.jsonvoice"]:
            actionNames=self.dictionary["mediaCfg.jsonvoice"][actionId][languageId].split(",")
            for actionName in actionNames:
                actionName=self.ReplaceCharForCompare(actionName)
                if actionName != "":
                    newIndex=0
                    while newIndex!=-1:
                        newIndex=command.find(" "+actionName+" ",newIndex)
                        if newIndex!=-1:
                            newIndex+=1
                            if actionId=="voiceCommand":
                                valueStart=text.find(" ",newIndex+5)+1
                                value=text[valueStart:]
                                matchingMediaActions.append([actionId,newIndex,actionName,"m",value])
                                break
                            elif actionId=="scene":
                                valueStart=newIndex+len(actionName)+1
                                for scene in self.sceneNames:
                                    sceneNames=scene[1].split(",")
                                    for sceneName in sceneNames:
                                        sceneName=self.ReplaceCharForCompare(sceneName)
                                        if len(command)>=(valueStart+len(sceneName)):
                                            matchString=command[valueStart:(valueStart+len(sceneName))]
                                            if matchString==sceneName:
                                                matchingMediaActions.append([actionId,newIndex,actionName+" "+sceneName,"m",scene[0]])
                                                break
                            else:
                                matchingMediaActions.append([actionId,newIndex,actionName,"m",None])
        for view in self.dictionary["views.json"]:
            viewNames=self.dictionary["views.json"][view][languageId].split(",")
            for viewName in viewNames:
                viewName=self.ReplaceCharForCompare(viewName)
                if viewName != "":
                    newIndex=0
                    while newIndex!=-1:
                        newIndex=command.find(" "+viewName,newIndex)
                        if newIndex!=-1:
                            newIndex+=1
                            if matchingViews[0][1]==-1:
                                matchingViews.pop(0)
                            viewIndex=self.viewsIDArray[view]
                            matchingViews.append([view,newIndex,viewName,"v",self.views[viewIndex][2],viewIndex])
                            for viewIndicator in viewIndicators:
                                if (newIndex-1-len(viewIndicator[2]))==viewIndicator[1]:
                                    command=command[:newIndex]+" "*len(viewName)+command[newIndex+len(viewName):]
                                    break
        matchingFiles=[]
        matchingButtons=[]
        for file in self.files:
            fileId=file[0]
            if fileId in self.dictionary["files.json"]:
                fileNames=self.dictionary["files.json"][fileId][languageId].split(",")
                for fileName in fileNames:
                    fileName=self.ReplaceCharForCompare(fileName)
                    if fileName != "":
                        indexStart=1
                        while True:
                            indexEnd=command.find(" ",indexStart)
                            if indexEnd!=-1:
                                indexLen=indexEnd-indexStart
                                if (indexLen>2 and indexLen*2>=len(fileName) and command[indexStart:indexEnd] == fileName[:indexLen]) or command[indexStart:indexEnd] == fileName:
                                    matchingFiles.append([fileId,indexStart,fileName,"f"])
                                if indexEnd+1>=len(command):
                                    break
                                else:
                                    indexStart=indexEnd+1
                            else:
                                break
            fileButtons="files.json"+fileId
            if fileButtons in self.dictionary:
                for button in self.dictionary[fileButtons]:
                    buttonNames=self.dictionary[fileButtons][button][languageId].split(",")
                    for buttonName1 in buttonNames:
                        buttonName1=self.ReplaceCharForCompare(buttonName1)
                        buttonNames2=buttonName1.split(" ")
                        if buttonName1 != "":
                            newIndex=0
                            while newIndex!=-1:
                                newIndex=command.find(" "+buttonName1+" ",newIndex)
                                if newIndex!=-1:
                                    newIndex+=1
                                    matchingButtons.append([fileId+"/"+button,newIndex,buttonName1,"b",1,len(buttonNames2)+3,fileId,fileName])
                        if len(buttonNames2)>1:
                            newIndex=0
                            while newIndex!=-1:
                                newIndex=command.find(" "+buttonNames2[0]+" ",newIndex)
                                if newIndex!=-1:
                                    newIndex+=1
                                    count=0#Key(4) is -1 because of the first match and +1 because the page it is on has not been validated yet to be found
                                    for buttonName in buttonNames2[1:]:
                                        if buttonName != "":
                                            newIndex2=command.find(" "+buttonName+" ",0)
                                            if newIndex2!=-1:
                                                count+=1
                                    matchingButtons.append([fileId+"/"+button,newIndex,buttonName1,"b",(len(buttonNames2)-count),len(buttonNames2),fileId,fileName]) 
        if targetUser not in self.usersIDArray:
            eg.PrintError("O-MEGA: User %s not found!" % unicode(targetUser))
            return False
        for i in reversed(xrange(len(matchingViews))):
            if matchingViews[i][0] in self.users[self.usersIDArray[targetUser]][2]:
                self.userSettings[targetUser]["selectedView"]=matchingViews[i][0]
            else:
                matchingViews.pop(i)
        if len(matchingViews)==0:
            view=self.users[self.usersIDArray[targetUser]][2][0]
            viewIndex=self.viewsIDArray[view]
            matchingViews.append([view,-1,"","v",self.views[viewIndex][2],viewIndex])
        matchingViews=sorted(matchingViews, key=lambda x: x[1])
        print u"O-MEGA: Found matching views: %s" % unicode(matchingViews)
        print u"O-MEGA: Found matching states: %s" % unicode(matchingStates)
        matchingMediaActions=sorted(matchingMediaActions, key=lambda x: x[1])
        print u"O-MEGA: Found matching media actions: %s" % unicode(matchingMediaActions)
        matchingFiles=sorted(matchingFiles, key=lambda x: x[1])
        print u"O-MEGA: Found matching pages: %s" % unicode(matchingFiles)
        matchingButtons=sorted(matchingButtons, key=lambda x: x[1])
        print u"O-MEGA: Found matching buttons: %s" % unicode(matchingButtons)
        commandParts.append(len(command))
        commandParts=sorted(commandParts)
        
        oneButtonMode=False
        matchingButtons2=self.InterpretSpokenCommandButtonFilter(matchingViews,matchingStates,matchingMediaActions,matchingFiles,matchingButtons,commandParts,languageId,command)
        if len(matchingButtons2)==0:
            print u"O-MEGA: Didn't find anything in the current view(s), trying all views of the user now.."
            oneButtonMode=True
            allUsersViews=[]
            for view in self.users[self.usersIDArray[targetUser]][2]:
                viewIndex=self.viewsIDArray[view]
                allUsersViews.append([view,1,"","v",self.views[viewIndex][2],viewIndex])
            matchingButtons2=self.InterpretSpokenCommandButtonFilter(allUsersViews,matchingStates,matchingMediaActions,matchingFiles,matchingButtons,commandParts,languageId,command)
        if len(matchingButtons2)==0:
            print u"O-MEGA: Didn't find anything again, will do nothing."
            return False
        print u"O-MEGA: Found combined: %s" % unicode(matchingButtons2)
        if oneButtonMode:
            for part in matchingButtons2:
                if len(part)>1 and part[0][4] == part[1][4] and part[0][5] == part[1][5]:
                    print u"O-MEGA: Now we found too much, will do nothing."
                    return False
        self.spokenCommandCache[targetUser]["lastCommand"]=matchingButtons2
        self.userSettings[targetUser]["selectedView"]=matchingButtons2[0][0][8][0]
        processThread = Thread(
            target=self.processInterpretCommandThread,
            args=(matchingButtons2, targetUser, )
        )
        processThread.start()
        return True
        
        
    def processInterpretCommandThread(self,matchingButtons2,targetUser, times=1):
        executedThings=[]
        for t in xrange(times):
            for part in matchingButtons2:
                for i in xrange(len(part)):
                    if i==0 or part[i][4]==part[i-1][4] and part[i][5]==part[i-1][5]:
                        thing=part[i]
                        executedThings.append(thing)
                        if thing[3]=="m":
                            if thing[0]=="scene":
                                self.LogWrapper.sceneOnOff(thing[7],thing[9][0])
                            elif thing[0]=="voiceCommand":
                                self.ActiveMedia(thing[6],thing[9][0],thing[8][0],thing[7])
                            elif thing[0]=="wait":
                                time.sleep(thing[9][4])
                            else:
                                self.ActiveMedia(thing[6],thing[9][0],thing[8][0],thing[9][4])
                        else:
                            eg.TriggerEvent(prefix="O-MEGA", suffix="CMD.buttons", payload={"target":thing[0], "targetState":thing[9][0],"view":thing[8][0],"targetValue":[thing[9][4],None,None,None],"user":targetUser})
                    else:
                        break
        #print executedThings
        return executedThings
        
    
    def InterpretSpokenCommandButtonFilter(self,matchingViews,matchingStates,matchingMediaActions,matchingFiles,matchingButtons,commandParts,languageId,command):
        result=[]
        matchingButtonsPerPart=[]
        for j in xrange(len(commandParts)-1):
            useAll=False
            value=None
            times=1
            tempLastNumber=0
            secs=0
            matchingStates2=[]
            for state in matchingStates:
                inThisPart=False
                if state[1]>=commandParts[j] and state[1]<commandParts[j+1]:
                    inThisPart=True
                if state[0]=="[all]":
                    if inThisPart:
                        useAll=True
                elif state[0]=="[set]":
                    if inThisPart:
                        value=state[4]
                        matchingStates2.append(["[value]",state[1],state[2],state[3]])
                elif state[0]=="times":
                    if inThisPart:
                        times=tempLastNumber
                elif state[0]=="seconds":
                    if inThisPart:
                        secs+=tempLastNumber
                elif state[0]=="minutes":
                    if inThisPart:
                        secs+=(tempLastNumber*60)
                elif state[0]=="hours":
                    if inThisPart:
                        secs+=(tempLastNumber*3600)
                elif state[0][0]=="#":
                    if inThisPart:
                        value=state[0]
                        matchingStates2.append(["[value]",state[1],state[2],state[3]])
                elif state[0][0]=="N":
                    if inThisPart:
                        tempLastNumber=int(state[0][1:])
                else:
                    matchingStates2.append(state)
            if len(matchingMediaActions)!=0 or len(matchingStates2)!=0:# and (len(matchingFiles)!=0 or len(matchingButtons)!=0):
                if j==0:
                    tempStates=[]
                    for state in matchingStates2:
                        tempStates.append(state + [value])
                    tempButtonKey=len(command)
                    tempFiles=[]
                    if len(matchingFiles)!=0:
                        tempButtonKey=matchingFiles[0][1]
                        tempFiles=[matchingFiles[0][0]]
                    if len(matchingButtons)!=0 and matchingButtons[0][1]<tempButtonKey:
                        tempButtonKey=matchingButtons[0][1]
                    matchingButtonsPerPart.append({"view":[matchingViews[0]],"state":tempStates,"buttonsKey":[tempButtonKey],"useAll":useAll,"repeat":times,"files":tempFiles})
                else:
                    matchingButtonsPerPart.append({"view":matchingButtonsPerPart[j-1]["view"],"state":matchingButtonsPerPart[j-1]["state"],"buttonsKey":matchingButtonsPerPart[j-1]["buttonsKey"],"useAll":matchingButtonsPerPart[j-1]["useAll"],"repeat":matchingButtonsPerPart[j-1]["repeat"],"files":matchingButtonsPerPart[j-1]["files"]})
                foundView=False
                for view in matchingViews:
                    if view[1]<commandParts[j+1]:
                        if view[1]>=commandParts[j]:
                            if foundView==False:
                                foundView=True
                                matchingButtonsPerPart[j]["view"]=[]
                            matchingButtonsPerPart[j]["view"].append(view)
                    else:
                        break
                foundState=False
                for state in matchingStates2:
                    if state[1]<commandParts[j+1]:
                        if state[1]>=commandParts[j]:
                            if foundState==False:
                                foundState=True
                                matchingButtonsPerPart[j]["state"]=[]
                            matchingButtonsPerPart[j]["state"].append(state+[value])
                    else:
                        break
                if not foundState and value!=None:
                    for stateI in xrange(len(matchingButtonsPerPart[j]["state"])):
                        matchingButtonsPerPart[j]["state"][stateI][4]=value
                keysFoundInThisPart=[]
                for button in matchingButtons:
                    if button[1]>=commandParts[j]:
                        if button[1]<commandParts[j+1]:
                            if button[1] not in keysFoundInThisPart:
                                keysFoundInThisPart.append(button[1])
                        else:
                            break
                actionsFoundInThisPart=[]
                for action in matchingMediaActions:
                    if action[1]>=commandParts[j]:
                        if action[1]<commandParts[j+1]:
                            if action[0] not in actionsFoundInThisPart:
                                actionsFoundInThisPart.append(action[0])
                        else:
                            break
                filesFoundInThisPart=[]
                for file in matchingFiles:
                    if file[1]>=commandParts[j]:
                        if file[1]<commandParts[j+1]:
                            if file[1] not in keysFoundInThisPart:
                                keysFoundInThisPart.append(file[1])
                            if file[0] not in filesFoundInThisPart:
                                filesFoundInThisPart.append(file[0])
                        else:
                            break
                #print keysFoundInThisPart
                if len(keysFoundInThisPart)==0 and len(actionsFoundInThisPart)==0 and not foundState and not foundView and value==None:
                    continue
                elif len(keysFoundInThisPart)!=0:
                    matchingButtonsPerPart[j]["buttonsKey"]=[]
                    for key in keysFoundInThisPart:
                        matchingButtonsPerPart[j]["buttonsKey"].append(key)
                    if len(filesFoundInThisPart)!=0:
                        matchingButtonsPerPart[j]["files"]=[]
                        for fileId in filesFoundInThisPart:
                            matchingButtonsPerPart[j]["files"].append(fileId)
                    matchingButtonsPerPart[j]["useAll"]=useAll
                matchingButtonsPerPart[j]["repeat"]=times
                #print matchingButtonsPerPart[j]
                tempResult=self.ProcessInterpretSpokenCommandButtonFilter(matchingMediaActions,matchingFiles,matchingButtons,commandParts,languageId,command,actionsFoundInThisPart,value,j,secs,matchingButtonsPerPart[j])
                if len(tempResult)==0 and j>0 and (len(actionsFoundInThisPart)!=0 or foundState or foundView or value!=None):
                    tempResult=self.ProcessInterpretSpokenCommandButtonFilter(matchingMediaActions,matchingFiles,matchingButtons,commandParts,languageId,command,actionsFoundInThisPart,value,j,secs,{"view":matchingButtonsPerPart[j]["view"],"state":matchingButtonsPerPart[j]["state"],"buttonsKey":matchingButtonsPerPart[j-1]["buttonsKey"],"useAll":matchingButtonsPerPart[j-1]["useAll"],"repeat":matchingButtonsPerPart[j]["repeat"],"files":matchingButtonsPerPart[j]["files"]})
                for n in reversed(xrange(len(tempResult))):
                    if tempResult[n][0]=="wait":
                        result.append([tempResult[n]])
                        tempResult.pop(n)
                if len(tempResult)>0:
                    tempResult=reversed(sorted(tempResult, key=lambda x: x[5]))
                    tempResult=sorted(tempResult, key=lambda x: x[4])
                    result.append(tempResult)
        return result

    
    def ProcessInterpretSpokenCommandButtonFilter(self,matchingMediaActions,matchingFiles,matchingButtons,commandParts,languageId,command,actionsFoundInThisPart,value,j,secs,matchingButtonsForThisPart):
        tempResult=[]
        foundSomething=False
        if matchingButtonsForThisPart["useAll"]==False:
            for matchingButton in matchingButtons:
                if matchingButton[1] in matchingButtonsForThisPart["buttonsKey"]:
                    if matchingButton[0] in self.buttonsIDArray:
                        if not self.buttonViewsForPage[matchingButton[6]]:
                            #tempMatchingViews=matchingButtonsForThisPart["view"]
                            tempMatchingViews=self.viewsInList(matchingButtonsForThisPart["view"],self.files[self.filesIDArray[matchingButton[6]]][10])
                        else:
                            tempMatchingViews=self.viewsInList(matchingButtonsForThisPart["view"],self.buttons[self.buttonsIDArray[matchingButton[0]]][9])
                        if len(tempMatchingViews)>0:
                            foundStateForThisButton=None
                            tempButton=self.buttons[self.buttonsIDArray[matchingButton[0]]]
                            for state in matchingButtonsForThisPart["state"]:
                                if state[0]=="[toggle]" or state[0] in tempButton[4]:
                                    foundStateForThisButton=state
                                    break
                            if (foundStateForThisButton==None or foundStateForThisButton[0]=="[value]") and tempButton[7]!={}:
                                for tempState in tempButton[4]:
                                    if tempState in tempButton[7] and "rename" in tempButton[7][tempState]:
                                        tempRenames=tempButton[7][tempState]["rename"].split(",")
                                        if self.ReplaceCharForCompare(tempRenames[0])=="":
                                            continue
                                        else:
                                            for tempRename in tempRenames:
                                                tempRename=" "+self.ReplaceCharForCompare(tempRename)+" "
                                                if tempRename in command[commandParts[j]:commandParts[j+1]]:
                                                    tempState2=state
                                                    tempState2[0]=tempState
                                                    foundStateForThisButton=tempState2
                                                    break
                                            if foundStateForThisButton!=None and foundStateForThisButton[0]!="[value]":
                                                break
                            if foundStateForThisButton!=None:
                                tempButtonValue=matchingButton[4]
                                if matchingButton[6] in matchingButtonsForThisPart["files"]:
                                    tempButtonValue-=1
                                for z in xrange(matchingButtonsForThisPart["repeat"]):
                                    tempResult.append([matchingButton[0],matchingButton[1],matchingButton[2],matchingButton[3],tempButtonValue,matchingButton[5],matchingButton[6],matchingButton[7],tempMatchingViews[0],foundStateForThisButton])
                                if tempButtonValue==0:
                                    foundSomething=True
        if foundSomething==False:
            for matchingFile in matchingFiles:
                if matchingFile[0] in matchingButtonsForThisPart["files"]:
                    if matchingFile[0] in self.filesIDArray:
                        tempMatchingViews=self.viewsInList(matchingButtonsForThisPart["view"],self.files[self.filesIDArray[matchingFile[0]]][10])
                        if len(tempMatchingViews)>0 and len(self.files[self.filesIDArray[matchingFile[0]]][5])!=0:
                            tempButtons=self.files[self.filesIDArray[matchingFile[0]]][5]
                            for tempButton in tempButtons:
                                if tempButton[8]:
                                    if self.buttonViewsForPage[matchingFile[0]]:
                                        tempMatchingViews=self.viewsInList(tempMatchingViews,tempButton[9])
                                    if not self.buttonViewsForPage[matchingFile[0]] or len(tempMatchingViews)>0:
                                        for state in matchingButtonsForThisPart["state"]:
                                            if state[0]=="[toggle]" or state[0] in tempButton[4]:
                                                tempButtonName=matchingFile[0]
                                                fileButtons="files.json"+matchingFile[0]
                                                if fileButtons in self.dictionary and tempButton[0] in self.dictionary[fileButtons]:
                                                    tempButtonName=self.ReplaceCharForCompare(self.dictionary[fileButtons][tempButton[0]][languageId])
                                                for z in xrange(matchingButtonsForThisPart["repeat"]):
                                                    tempResult.append([matchingFile[0]+"/"+tempButton[0],matchingFile[1],tempButtonName,"f",1,0,matchingFile[0],matchingFile[2],tempMatchingViews[0],state])
                                                foundSomething=True
                                                break
        if len(actionsFoundInThisPart)!=0:
            for mediaAction in self.mediaCfg:
                if mediaAction[0] in actionsFoundInThisPart:
                    for matchingMediaAction in matchingMediaActions:
                        if mediaAction[0] == matchingMediaAction[0]:
                            if matchingMediaAction[0]=="scene" and foundSomething==False:
                                tempScene=self.sceneNames[self.sceneNamesIds[matchingMediaAction[4]]]
                                if tempScene[3]==0:
                                    tempMatchingViews=self.viewsInList(matchingButtonsForThisPart["view"],tempScene[8])
                                    if len(tempMatchingViews)>0:
                                        tempView=tempMatchingViews[0]
                                        foundStateForThisAction=False
                                        for state in matchingButtonsForThisPart["state"]:
                                            if state[0] in mediaAction[2] and (tempScene[7]==0 or state[0] in ["[activate]","[stop]"]):
                                                foundStateForThisAction=True
                                                for z in xrange(matchingButtonsForThisPart["repeat"]):
                                                    tempResult.append([matchingMediaAction[0],matchingMediaAction[1],matchingMediaAction[2],"m",1,1,mediaAction[1],matchingMediaAction[4],tempView,state])
                                                break
                                        if foundStateForThisAction==False:
                                            for z in xrange(matchingButtonsForThisPart["repeat"]):
                                                tempResult.append([matchingMediaAction[0],matchingMediaAction[1],matchingMediaAction[2],"m",1,0,mediaAction[1],matchingMediaAction[4],tempView,[mediaAction[2][0],None,None,"s",value]])
                                        foundSomething=True
                            elif matchingMediaAction[0]=="selectInput" and foundSomething==False:
                                for fileId in matchingButtonsForThisPart["files"]:
                                    tempFile=self.files[self.filesIDArray[fileId]]
                                    tempMatchingViews=self.viewsInList(matchingButtonsForThisPart["view"],tempFile[10])
                                    if len(tempMatchingViews)>0:
                                        for tempView in tempMatchingViews:
                                            tempResult.append([matchingMediaAction[0],matchingMediaAction[1],matchingMediaAction[2],"m",1,1,mediaAction[1],matchingMediaAction[4],tempView,[mediaAction[2][0],None,None,"s",fileId]])
                                            foundSomething=True
                            elif matchingMediaAction[0]=="wait":
                                if secs>0:
                                    tempView=matchingButtonsForThisPart["view"][0]
                                    tempResult.append([matchingMediaAction[0],matchingMediaAction[1],matchingMediaAction[2],"m",1,1,mediaAction[1],matchingMediaAction[4],tempView,[mediaAction[2][0],None,None,"s",secs]])
                            elif matchingMediaAction[0] in self.mediaCfgIDArray and foundSomething==False:
                                tempView=matchingButtonsForThisPart["view"][0]
                                foundStateForThisAction=False
                                for state in matchingButtonsForThisPart["state"]:
                                    if state[0] in mediaAction[2]:
                                        for z in xrange(matchingButtonsForThisPart["repeat"]):
                                            tempResult.append([matchingMediaAction[0],matchingMediaAction[1],matchingMediaAction[2],"m",1,1,mediaAction[1],matchingMediaAction[4],tempView,state])
                                        foundStateForThisAction=True
                                        break
                                if foundStateForThisAction==False:
                                    for z in xrange(matchingButtonsForThisPart["repeat"]):
                                        tempResult.append([matchingMediaAction[0],matchingMediaAction[1],matchingMediaAction[2],"m",1,0,mediaAction[1],matchingMediaAction[4],tempView,[mediaAction[2][0],None,None,"s",value]])
                                foundSomething=True
                            break
                    if foundSomething:
                        break
        return tempResult
    
    
    def viewsInList(self, views, list):
        tempViews=[]
        for item in views:
            if item[0] in list:
                tempViews.append(item)
        tempViews=reversed(sorted(tempViews, key=lambda x: x[5]))
        tempViews=sorted(tempViews, key=lambda x: x[4])
        return tempViews

        
#===============================================================================
# O-MEGA functions End
#===============================================================================             
# Ping functions Start
#===============================================================================
    
class PingHost():

    def __init__(self):
        self.hosts={}
        pingString="=32"
        command=["ping.exe","127.0.0.1","-4","-n","1","-w","500"]
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags = subprocess.STARTF_USESHOWWINDOW
        prog = subprocess.Popen(command, stdout=subprocess.PIPE, bufsize=1, stderr=None,startupinfo=startupinfo)
        while True:
            if prog.poll():
                break
            else:
                output = prog.stdout.readline()
                if output:
                    start=output.find("=")
                    if start!=-1:
                        end=output[start:].find(" ")
                        if end!=-1:
                            pingString=output[start:start+end]
                            break
                time.sleep(0.1)
        print "O-MEGA.Ping.identString:"+pingString
        self.pingString=pingString
        
        
    def PausePings(self):
        for ID in self.hosts.keys():
            self.hosts[ID]["stopEvent"].set()
            
            
    def ResumePings(self):
        for ID in self.hosts.keys():
            self.Ping(self.hosts[ID]["IP"],ID)
            
            
    def Ping(self,IP,ID):
        if ID in self.hosts.keys() and not self.hosts[ID]["stopEvent"].isSet():
            self.hosts[ID]["stopEvent"].set()
        self.hosts[ID]={}
        self.hosts[ID]["IP"]=IP
        self.hosts[ID]["stopEvent"] = Event()
        pingThread = Thread(
            target=self.PingThread,
            args=(self.hosts[ID]["stopEvent"],self.hosts[ID]["IP"],ID, )
        )
        pingThread.daemon=True
        pingThread.start()
    
    
    def PingThread(self,stopThreadEvent, IP, ID):
        try:
            IP=socket.gethostbyname(IP)
        except:
            eg.PrintError("O-MEGA.Ping: "+IP+" not found on the Network, Ping will not start!")
            return False
        print "O-MEGA.Ping: " + IP + " is starting! ("+ID+")"
        status=""
        eventsAlive=0
        eventsDead=0
        lock=Lock()
        command=["ping.exe",IP,"-4","-t","-w","1000"]
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags = subprocess.STARTF_USESHOWWINDOW
        prog = subprocess.Popen(command, stdout=subprocess.PIPE, bufsize=1, stderr=None,startupinfo=startupinfo)
        while not stopThreadEvent.isSet():
            if prog.poll():
                prog = subprocess.Popen(command, stdout=subprocess.PIPE, bufsize=1, stderr=None,startupinfo=startupinfo)
            else:
                output = prog.stdout.readline()
                lock.acquire()
                if output:
                    if output.find(self.pingString)!=-1:
                        eventsAlive+=1
                        eventsDead=0
                        if eventsAlive>=1:
                            if status!="alive":
                                status="alive"
                                eg.TriggerEvent(prefix="O-MEGA",suffix="Ping."+ID+".ON")
                    else:
                        eventsAlive=0
                        eventsDead+=1
                        if eventsDead>=3:
                            if status!="dead":
                                status="dead"
                                eg.TriggerEvent(prefix="O-MEGA",suffix="Ping."+ID+".OFF")
                stopThreadEvent.wait(0.1)
                lock.release()
        print "O-MEGA.Ping: " + IP + " is ending! ("+ID+")"
        prog.terminate()
        stopThreadEvent.clear()

        
#===============================================================================             
# Ping functions End
#===============================================================================        

class ServerExecute(eg.ActionBase):
    name = "Execute command on server"
    description = "Executes a python command on your O-MEGA server PC."
    
    def __call__(self,command):
        if command[0:2]=='{"':
            command=json.loads(command)
            if isinstance(command["payload"],basestring):
                command["payload"]=u"\""+unicode(command["payload"])+u"\""
            else:
                command["payload"]=unicode(command["payload"])
            command=u"eg.TriggerEvent(prefix=\"O-MEGA\",suffix=\""+command["suffix"]+u"\",payload="+command["payload"]+u")"
        return self.plugin.ServerExecute(command)
            
    def Configure(self, command = ""):
        panel = eg.ConfigPanel(self)
        st1 = panel.StaticText(Text.pyOComm)
        pycommCtrl = panel.TextCtrl(command, size=(500,-1))
        st2 = panel.StaticText("")
        eg.EqualizeWidths((st1,st2))
        panel.AddLine(st1, pycommCtrl)
        while panel.Affirmed():
            panel.SetResult(
                pycommCtrl.GetValue(),
            )
            
            
class ClientExecute(eg.ActionBase):
    name = "Execute command on a PC client"
    description = "Executes a python command on target O-MEGA client PC."
    
    def __call__(self,targetDeviceId,command):
        return self.plugin.RequestDataFromClient(str(targetDeviceId),command)
            
    def Configure(self, targetDeviceId = "", command = ""):
        panel = eg.ConfigPanel(self)
        st1 = panel.StaticText(Text.targetDeviceId)
        targetCtrl = panel.TextCtrl(targetDeviceId)
        st2 = panel.StaticText(Text.pyComm)
        pycommCtrl = panel.TextCtrl(command, size=(500,-1))
        eg.EqualizeWidths((st1,st2))
        panel.AddLine(st1, targetCtrl)
        panel.AddLine(st2, pycommCtrl)
        while panel.Affirmed():
            panel.SetResult(
                targetCtrl.GetValue(),
                pycommCtrl.GetValue(),
            )

            
class Ping(eg.ActionBase):
    name = "Ping"
    description = "Starts to ping a device."
    
    def __call__(self,IP,ID):
        self.plugin.Ping.Ping(IP,"custom:"+ID)
        
    def Configure(self, IP = "", ID = "ID"):
        panel = eg.ConfigPanel(self)
        IPCtrl = panel.TextCtrl(IP)
        IDCtrl = panel.TextCtrl(ID)
        st1 = panel.StaticText("IP")
        st2 = panel.StaticText("ID")
        eg.EqualizeWidths((st1,st2))
        panel.AddLine(st1, IPCtrl)
        panel.AddLine(st2, IDCtrl)
        while panel.Affirmed():
            panel.SetResult(
                IPCtrl.GetValue(),
                IDCtrl.GetValue(),
            )
            
            
class ReadyForAudio(eg.ActionBase):
    name = "Ready to play audio?"
    description = """Turns on all devices and programs that are needed to hear something. Returns True if everything is ready, returns False if not and re-triggers the event after 6 sec. !!Only works with O-CMD events!!"""
    
    def __call__(self):
        tempEvent=eg.event
        if not self.plugin.ResolveAudioDependencies(tempEvent):
            eg.scheduler.AddTask(6.0, eg.TriggerEvent, prefix=tempEvent.prefix, suffix=tempEvent.suffix, payload=tempEvent.payload)
            return False
        else:
            return True
                  

class ActiveMedia(eg.ActionBase):
    name = "Control Active Media"
    description = "Send a command to the active media player."
    
    class text:
        action = "Target Action:"
        view = "View ID for context (Optional):"
        targetState = "Target State:"
        value = "Target Value (Optional):"
    
    def __call__(self,action,targetState,view="",value=""):
        view=eg.ParseString(view)
        value=eg.ParseString(value)
        if self.plugin.pluginServer:
            return self.plugin.ActiveMedia(action,targetState,view,value)
        else:
            return self.plugin.ServerExecute('self.ActiveMedia(\''+action+'\',\''+targetState+'\',\''+view+'\',\''+value+'\')')
            
    def Configure(self,action="play",targetState="[activate]",view="",value=""):
        text = self.text
        
        def onChoice(evt):
            tempAction=actionsCtrl.GetStringSelection()
            statesCtrl.Clear()
            statesCtrl.AppendItems(statesList[tempAction])
            if targetState in statesList[tempAction]:
                statesCtrl.SetSelection(statesList[tempAction].index(targetState))
            else:
                statesCtrl.SetSelection(0)
        
        statesList={}
        for action in self.plugin.mediaCfg:
            if not action[4]:
                statesList[action[1]]=action[2]
        actionsList=statesList.keys()
        #viewsList=[]
        #for v in self.plugin.views:
        #    viewsList.append(v[0])
        panel = eg.ConfigPanel(self)
        st1 = panel.StaticText(text.action)
        actionsCtrl = wx.Choice(panel, -1, choices=actionsList)
        if action in actionsList:
            actionsCtrl.SetSelection(actionsList.index(action))
        else:
            actionsCtrl.SetSelection(0)
        actionsCtrl.Bind(wx.EVT_CHOICE, onChoice)
        st2 = panel.StaticText(text.targetState)
        statesCtrl = wx.Choice(panel, -1, choices=statesList[actionsCtrl.GetStringSelection()])
        if targetState in statesList[actionsCtrl.GetStringSelection()]:
            statesCtrl.SetSelection(statesList[actionsCtrl.GetStringSelection()].index(targetState))
        else:
            statesCtrl.SetSelection(0)
        st3 = panel.StaticText(text.view)
        #viewsCtrl = wx.Choice(panel, -1, choices=viewsList)
        viewCtrl = panel.TextCtrl(view)
        #if str(view) in viewsList:
        #    viewsCtrl.SetSelection(viewsList.index(str(view)))
        #else:
        #    viewsCtrl.SetSelection(0)
        st4 = panel.StaticText(text.value)
        valueCtrl = panel.TextCtrl(value)
        eg.EqualizeWidths((st1,st2,st3,st4))
        panel.AddLine(st1, actionsCtrl)
        panel.AddLine(st2, statesCtrl)
        panel.AddLine(st3, viewCtrl)
        panel.AddLine(st4, valueCtrl)
        while panel.Affirmed():
            panel.SetResult(
                actionsCtrl.GetStringSelection(),
                statesCtrl.GetStringSelection(),
                viewCtrl.GetValue(),
                valueCtrl.GetValue(),
            )
         

class InterpretSpokenCommand(eg.ActionBase):

    class text:
        command = "Command:"
        userId = "O-MEGA User ID:"
        viewId = "Default O-MEGA View ID (Optional):"

    def __call__(self, command, userId, viewId=""):
        command=eg.ParseString(command)
        userId=eg.ParseString(str(userId))
        viewId=eg.ParseString(str(viewId))
        if self.plugin.pluginServer:
            return self.plugin.InterpretSpokenCommand(command, userId, viewId)
        else:
            return self.plugin.ServerExecute('self.InterpretSpokenCommand(\''+command+'\',\''+userId+'\',\''+viewId+'\')')


    def Configure(self, command="", userId="", viewId=""):
        text = self.text
        panel = eg.ConfigPanel(self)
        commandCtrl = panel.TextCtrl(command)
        userIdCtrl = panel.TextCtrl(userId)
        viewIdCtrl = panel.TextCtrl(viewId)
        fl = wx.EXPAND|wx.TOP
        box=wx.GridBagSizer(2, 3)
        box.Add(panel.StaticText(text.command), (0, 0), flag = wx.TOP, border=12)
        box.Add(commandCtrl, (0, 1), flag = fl, border=9)
        box.Add(panel.StaticText(text.userId), (1, 0), flag = wx.TOP, border=12)
        box.Add(userIdCtrl, (1, 1), flag = fl, border=9)
        box.Add(panel.StaticText(text.viewId), (2, 0), flag = wx.TOP, border=12)
        box.Add(viewIdCtrl, (2, 1), flag = fl, border=9)
        box.AddGrowableCol(1)
        panel.sizer.Add(box, 0, wx.EXPAND|wx.LEFT|wx.RIGHT, 10)
        while panel.Affirmed():
            panel.SetResult(
                commandCtrl.GetValue(),
                userIdCtrl.GetValue(),
                viewIdCtrl.GetValue(),
            )
            
            
class SetValueForProgram(eg.ActionBase):
    name = "Set Variable for Program"
    description = "Sets a value for a specific O-MEGA Program Variable."
    
    def __call__(self,vari,value,type="",parseNoVari=True,parseNoValue=True):
        if not parseNoVari:
            vari=eg.ParseString(unicode(vari))
        if isinstance(value, basestring) and not parseNoValue:
            value=eg.ParseString(value)
        type=unicode(type)
        if type=="" and eg.event.prefix=="O-CMD":
            type=eg.event.suffix.split(".")[1]
        deviceId=self.plugin.programsForPCsByType[self.plugin.thisPc][type]
        oldData=self.plugin.ServerExecute(u'self.States["programs"]["'+deviceId+u'"]')
        if vari=="play" and str(value)=="[on]" and (vari not in oldData or oldData[vari]=="[off]"):
            tempEvent=self.plugin.LogWrapper.emptyEvent(prefix="O-CMD", suffix="programs."+type+"."+vari, payload={"target":deviceId,"targetState":"[on]"})
            if not self.plugin.ResolveAudioDependencies(tempEvent):
                eg.TriggerEvent(prefix="O-CMD", suffix="programs."+type+".pause", payload={"target":deviceId,"targetState":"[on]"})
                return True
        if vari not in oldData or oldData[vari]!=value:
            if isinstance(value, basestring):
                value='"'+value+'"'
            command=u'self.States["programs"]["'+deviceId+u'"]["'+vari+u'"]='+unicode(value)
            self.plugin.ServerExecute(command)
        return True

    def GetLabel(self,vari="???",value="???",type="???",parseNoVari=True,parseNoValue=True):
        return "Set variable value for program "+type+": "+vari+" to "+unicode(value)
    
    def Configure(self,vari="play",value="[on]",type="",parseNoVari=False,parseNoValue=False):
        panel = eg.ConfigPanel(self)
        typeList=list(self.plugin.programsForPCsByType[self.plugin.thisPc].keys())
        st2 = panel.StaticText(Text.targetType)
        typeCtrl = wx.Choice(panel, -1, choices=typeList)
        if type in typeList:
            typeCtrl.SetSelection(typeList.index(type))
        else:
            typeCtrl.SetSelection(0)
        st3 = panel.StaticText(Text.variable)
        variCtrl = panel.TextCtrl(vari)
        parseNoVariCtrl = wx.CheckBox(panel, -1, Text.parsing)
        parseNoVariCtrl.SetValue(parseNoVari)
        st4 = panel.StaticText(Text.value)
        valueCtrl = panel.TextCtrl(unicode(value), size=(400,-1))
        parseNoValueCtrl = wx.CheckBox(panel, -1, Text.parsing)
        parseNoValueCtrl.SetValue(parseNoValue)
        eg.EqualizeWidths((st2,st3,st4))
        panel.AddLine(st3, variCtrl, parseNoVariCtrl)
        panel.AddLine(st4, valueCtrl, parseNoValueCtrl)
        panel.AddLine(st2, typeCtrl)
        while panel.Affirmed():
            panel.SetResult(
                variCtrl.GetValue(),
                valueCtrl.GetValue(),
                typeCtrl.GetStringSelection(),
                parseNoVariCtrl.GetValue(),
                parseNoValueCtrl.GetValue(),
            )
            
            
class GetValueForProgram(eg.ActionBase):
    name = "Get Variable for Program"
    description = "Returns the value for a specific O-MEGA Program Variable."
    
    def __call__(self,vari="",type="",parseNoVari=True):
        type=unicode(type)
        if type=="" and eg.event.prefix=="O-CMD":
            type=eg.event.suffix.split(".")[1]
        if not parseNoVari:
            vari=eg.ParseString(unicode(vari))
        if vari=="":
            command=u'self.States["programs"]["'+self.plugin.programsForPCsByType[self.plugin.thisPc][type]+u'"]'
        else:
            command=u'self.States["programs"]["'+self.plugin.programsForPCsByType[self.plugin.thisPc][type]+u'"]["'+vari+u'"]'
        try:
            return self.plugin.ServerExecute(command)
        except KeyError, e:
            eg.PrintError("O-MEGA: We have a KeyError, most likely the Target Type is invalid or the Variable is not defined yet - %s" % str(e))
            return None     
    
    def GetLabel(self,vari="???",type="???",parseNoVari=True):
        return "Get variable value for program "+type+": "+vari
    
    def Configure(self,vari="play",type="",parseNoVari=False):
        panel = eg.ConfigPanel(self)
        typeList=list(self.plugin.programsForPCsByType[self.plugin.thisPc].keys())
        st2 = panel.StaticText(Text.targetType)
        typeCtrl = wx.Choice(panel, -1, choices=typeList)
        if type in typeList:
            typeCtrl.SetSelection(typeList.index(type))
        else:
            typeCtrl.SetSelection(0)
        st3 = panel.StaticText(Text.variable+" ("+Text.optional+")")
        variCtrl = panel.TextCtrl(vari)
        parseNoVariCtrl = wx.CheckBox(panel, -1, Text.parsing)
        parseNoVariCtrl.SetValue(parseNoVari)
        eg.EqualizeWidths((st2,st3))
        panel.AddLine(st3, variCtrl, parseNoVariCtrl)
        panel.AddLine(st2, typeCtrl)
        while panel.Affirmed():
            panel.SetResult(
                variCtrl.GetValue(),
                typeCtrl.GetStringSelection(),
                parseNoVariCtrl.GetValue(),
            )

            
class SetValueForDevice(eg.ActionBase):
    name = "Set Variable for Device"
    description = "Sets a value for a specific O-MEGA Device Variable."
    
    def __call__(self,vari,value,deviceId="",parseNoVari=True,parseNoValue=True,parseNoDeviceId=True):
        if not parseNoVari:
            vari=eg.ParseString(unicode(vari))
        if not parseNoDeviceId:
            deviceId=eg.ParseString(unicode(deviceId))
        if deviceId=="" and eg.event.prefix=="O-CMD":
            deviceId=eg.event.payload["target"]
        if isinstance(value, basestring) and not parseNoValue:
            value=eg.ParseString(value)
        oldData=self.plugin.ServerExecute(u'self.States["devices"]["'+deviceId+u'"]')
        #if vari=="play" and str(value)=="[on]" and (vari not in oldData or oldData[vari]=="[off]"):
        #    type=self.plugin.devices[self.plugin.devicesIDArray[deviceId]][1]
        #    tempEvent=self.plugin.LogWrapper.emptyEvent(prefix="O-CMD", suffix="devices."+type+"."+vari, payload={"target":deviceId,"targetState":"[on]"})
        #    if not self.plugin.ResolveAudioDependencies(tempEvent):
        #        eg.TriggerEvent(prefix="O-CMD", suffix="devices."+type+".pause", payload={"target":deviceId,"targetState":"[on]"})
        #        return True
        if vari not in oldData or oldData[vari]!=value:
            if isinstance(value, basestring):
                value='"'+value+'"'
            command=u'self.States["devices"]["'+deviceId+u'"]["'+vari+u'"]='+unicode(value)
            self.plugin.ServerExecute(command)
        return True
    
    def GetLabel(self,vari="???",value="???",deviceId="???",parseNoVari=True,parseNoValue=True,parseNoDeviceId=True):
        return "Set variable value for device "+deviceId+": "+vari+" to "+unicode(value)
    
    def Configure(self,vari="play",value="[on]",deviceId="",parseNoVari=False,parseNoValue=False,parseNoDeviceId=False):
        panel = eg.ConfigPanel(self)
        st2 = panel.StaticText(Text.targetDeviceId)
        deviceIdCtrl = panel.TextCtrl(deviceId)
        parseNoDeviceIdCtrl = wx.CheckBox(panel, -1, Text.parsing)
        parseNoDeviceIdCtrl.SetValue(parseNoDeviceId)
        st3 = panel.StaticText(Text.variable)
        variCtrl = panel.TextCtrl(vari)
        parseNoVariCtrl = wx.CheckBox(panel, -1, Text.parsing)
        parseNoVariCtrl.SetValue(parseNoVari)
        st4 = panel.StaticText(Text.value)
        valueCtrl = panel.TextCtrl(unicode(value), size=(400,-1))
        parseNoValueCtrl = wx.CheckBox(panel, -1, Text.parsing)
        parseNoValueCtrl.SetValue(parseNoValue)
        eg.EqualizeWidths((st2,st3,st4))
        panel.AddLine(st3, variCtrl, parseNoVariCtrl)
        panel.AddLine(st4, valueCtrl, parseNoValueCtrl)
        panel.AddLine(st2, deviceIdCtrl, parseNoDeviceIdCtrl)
        while panel.Affirmed():
            panel.SetResult(
                variCtrl.GetValue(),
                valueCtrl.GetValue(),
                deviceIdCtrl.GetValue(),
                parseNoVariCtrl.GetValue(),
                parseNoValueCtrl.GetValue(),
                parseNoDeviceIdCtrl.GetValue(),
            )
            
            
class GetValueForDevice(eg.ActionBase):
    name = "Get Variable for Device"
    description = "Returns the value for a specific O-MEGA Device Variable."
    
    def __call__(self,vari="",deviceId="",parseNoVari=True,parseNoDeviceId=True):
        if not parseNoVari:
            vari=eg.ParseString(unicode(vari))
        if not parseNoDeviceId:
            deviceId=eg.ParseString(unicode(deviceId))
        if deviceId=="" and eg.event.prefix=="O-CMD":
            deviceId=eg.event.payload["target"]
        if vari=="":
            command=u'self.States["devices"]["'+deviceId+'"]'
        else:
            command=u'self.States["devices"]["'+deviceId+'"]["'+vari+u'"]'
        try:
            return self.plugin.ServerExecute(command)
        except KeyError, e:
            eg.PrintError("O-MEGA: We have a KeyError, most likely the Target Device ID is invalid or the Variable is not defined yet - %s" % str(e))
            return None 
            
    def GetLabel(self,vari="???",deviceId="???",parseNoVari=True,parseNoDeviceId=True):
        return "Get variable value for device "+deviceId+": "+vari
    
    def Configure(self,vari="play",deviceId="",parseNoVari=False,parseNoDeviceId=False):
        panel = eg.ConfigPanel(self)
        st2 = panel.StaticText(Text.targetDeviceId)
        deviceIdCtrl = panel.TextCtrl(deviceId)
        parseNoDeviceIdCtrl = wx.CheckBox(panel, -1, Text.parsing)
        parseNoDeviceIdCtrl.SetValue(parseNoDeviceId)
        st3 = panel.StaticText(Text.variable+" ("+Text.optional+")")
        variCtrl = panel.TextCtrl(vari)
        parseNoVariCtrl = wx.CheckBox(panel, -1, Text.parsing)
        parseNoVariCtrl.SetValue(parseNoVari)
        eg.EqualizeWidths((st2,st3))
        panel.AddLine(st3, variCtrl, parseNoVariCtrl)
        panel.AddLine(st2, deviceIdCtrl, parseNoDeviceIdCtrl)
        while panel.Affirmed():
            panel.SetResult(
                variCtrl.GetValue(),
                deviceIdCtrl.GetValue(),
                parseNoVariCtrl.GetValue(),
                parseNoDeviceIdCtrl.GetValue(),
            )
            
            
class SetSettingForProgram(eg.ActionBase):
    name = "Set Setting for Program"
    description = "Sets a setting for a specific O-MEGA Program."
    
    def __call__(self,vari,value,type="",parseNoVari=True,parseNoValue=True):
        if not parseNoVari:
            vari=eg.ParseString(unicode(vari))
        type=unicode(type)
        if type=="" and eg.event.prefix=="O-CMD":
            type=eg.event.suffix.split(".")[1]
        if isinstance(value, basestring) and not parseNoValue:
            value=eg.ParseString(value)
        deviceId=self.plugin.programsForPCsByType[self.plugin.thisPc][type]
        command=u'self.programs[self.programsIDArray["'+deviceId+u'"]][2]'
        oldData=self.plugin.ServerExecute(command)
        if vari not in oldData or oldData[vari]!=value:
            if isinstance(value, basestring):
                value='"'+value+'"'
            command=u'self.programs[self.programsIDArray["'+deviceId+u'"]][2]["'+vari+u'"]='+unicode(value)
            self.plugin.ServerExecute(command)
        return True

    def GetLabel(self,vari="???",value="???",type="???",parseNoVari=True,parseNoValue=True):
        return "Set setting for program "+type+": "+vari+" to "+unicode(value)
    
    def Configure(self,vari="",value="",type="",parseNoVari=False,parseNoValue=False):
        panel = eg.ConfigPanel(self)
        typeList=list(self.plugin.programsForPCsByType[self.plugin.thisPc].keys())
        st2 = panel.StaticText(Text.targetType)
        typeCtrl = wx.Choice(panel, -1, choices=typeList)
        if type in typeList:
            typeCtrl.SetSelection(typeList.index(type))
        else:
            typeCtrl.SetSelection(0)
        st3 = panel.StaticText(Text.variable)
        variCtrl = panel.TextCtrl(vari)
        parseNoVariCtrl = wx.CheckBox(panel, -1, Text.parsing)
        parseNoVariCtrl.SetValue(parseNoVari)
        st4 = panel.StaticText(Text.value)
        valueCtrl = panel.TextCtrl(unicode(value), size=(400,-1))
        parseNoValueCtrl = wx.CheckBox(panel, -1, Text.parsing)
        parseNoValueCtrl.SetValue(parseNoValue)
        eg.EqualizeWidths((st2,st3,st4))
        panel.AddLine(st3, variCtrl, parseNoVariCtrl)
        panel.AddLine(st4, valueCtrl, parseNoValueCtrl)
        panel.AddLine(st2, typeCtrl)
        while panel.Affirmed():
            panel.SetResult(
                variCtrl.GetValue(),
                valueCtrl.GetValue(),
                typeCtrl.GetStringSelection(),
                parseNoVariCtrl.GetValue(),
                parseNoValueCtrl.GetValue(),
            )
            
            
class GetSettingForProgram(eg.ActionBase):
    name = "Get Setting for Program"
    description = "Returns a setting for a specific O-MEGA Program."
    
    def __call__(self,vari="",type="",parseNoVari=True):
        if not parseNoVari:
            vari=eg.ParseString(unicode(vari))
        type=unicode(type)
        if type=="" and eg.event.prefix=="O-CMD":
            type=eg.event.suffix.split(".")[1]
        if vari=="":
            command=u'self.programs[self.programsIDArray["'+self.plugin.programsForPCsByType[self.plugin.thisPc][type]+u'"]][2]'
        else:
            command=u'self.programs[self.programsIDArray["'+self.plugin.programsForPCsByType[self.plugin.thisPc][type]+u'"]][2]["'+vari+u'"]'
        return self.plugin.ServerExecute(command)
    
    def GetLabel(self,vari="???",type="???",parseNoVari=True):
        return "Get setting for program "+type+": "+vari
    
    def Configure(self,vari="",type="",parseNoVari=False):
        panel = eg.ConfigPanel(self)
        typeList=list(self.plugin.programsForPCsByType[self.plugin.thisPc].keys())
        st2 = panel.StaticText(Text.targetType)
        typeCtrl = wx.Choice(panel, -1, choices=typeList)
        if type in typeList:
            typeCtrl.SetSelection(typeList.index(type))
        else:
            typeCtrl.SetSelection(0)
        st3 = panel.StaticText(Text.variable+" ("+Text.optional+")")
        variCtrl = panel.TextCtrl(vari)
        parseNoVariCtrl = wx.CheckBox(panel, -1, Text.parsing)
        parseNoVariCtrl.SetValue(parseNoVari)
        eg.EqualizeWidths((st2,st3))
        panel.AddLine(st3, variCtrl, parseNoVariCtrl)
        panel.AddLine(st2, typeCtrl)
        while panel.Affirmed():
            panel.SetResult(
                variCtrl.GetValue(),
                typeCtrl.GetStringSelection(),
                parseNoVariCtrl.GetValue(),
            )

            
class SetSettingForDevice(eg.ActionBase):
    name = "Set Setting for Device"
    description = "Sets a setting for a specific O-MEGA Device."
    
    def __call__(self,vari,value,deviceId="",parseNoVari=True,parseNoValue=True,parseNoDeviceId=True):
        if not parseNoVari:
            vari=eg.ParseString(unicode(vari))
        if not parseNoDeviceId:
            deviceId=eg.ParseString(unicode(deviceId))
        if deviceId=="" and eg.event.prefix=="O-CMD":
            deviceId=eg.event.payload["target"]
        if isinstance(value, basestring) and not parseNoValue:
            value=eg.ParseString(value)
        command=u'self.devices[self.devicesIDArray["'+deviceId+u'"]][2]'
        oldData=self.plugin.ServerExecute(command)
        if vari not in oldData or oldData[vari]!=value:
            if isinstance(value, basestring):
                value='"'+value+'"'
            command=u'self.devices[self.devicesIDArray["'+deviceId+u'"]][2]["'+vari+u'"]='+unicode(value)
            self.plugin.ServerExecute(command)
        return True
    
    def GetLabel(self,vari="???",value="???",deviceId="???",parseNoVari=True,parseNoValue=True,parseNoDeviceId=True):
        return "Set setting for device "+deviceId+": "+vari+" to "+unicode(value)
    
    def Configure(self,vari="",value="",deviceId="",parseNoVari=False,parseNoValue=False,parseNoDeviceId=False):
        panel = eg.ConfigPanel(self)
        st2 = panel.StaticText(Text.targetDeviceId)
        deviceIdCtrl = panel.TextCtrl(deviceId)
        parseNoDeviceIdCtrl = wx.CheckBox(panel, -1, Text.parsing)
        parseNoDeviceIdCtrl.SetValue(parseNoDeviceId)
        st3 = panel.StaticText(Text.variable)
        variCtrl = panel.TextCtrl(vari)
        parseNoVariCtrl = wx.CheckBox(panel, -1, Text.parsing)
        parseNoVariCtrl.SetValue(parseNoVari)
        st4 = panel.StaticText(Text.value)
        valueCtrl = panel.TextCtrl(unicode(value), size=(400,-1))
        parseNoValueCtrl = wx.CheckBox(panel, -1, Text.parsing)
        parseNoValueCtrl.SetValue(parseNoValue)
        eg.EqualizeWidths((st2,st3,st4))
        panel.AddLine(st3, variCtrl, parseNoVariCtrl)
        panel.AddLine(st4, valueCtrl, parseNoValueCtrl)
        panel.AddLine(st2, deviceIdCtrl, parseNoDeviceIdCtrl)
        while panel.Affirmed():
            panel.SetResult(
                variCtrl.GetValue(),
                valueCtrl.GetValue(),
                deviceIdCtrl.GetValue(),
                parseNoVariCtrl.GetValue(),
                parseNoValueCtrl.GetValue(),
                parseNoDeviceIdCtrl.GetValue(),
            )
            
            
class GetSettingForDevice(eg.ActionBase):
    name = "Get Setting for Device"
    description = "Returns a setting for a specific O-MEGA Device."
    
    def __call__(self,vari="",deviceId="",parseNoVari=True,parseNoDeviceId=True):
        deviceId=eg.ParseString(unicode(deviceId))
        if deviceId=="" and eg.event.prefix=="O-CMD":
            deviceId=eg.event.payload["target"]
        vari=eg.ParseString(unicode(vari))
        if vari=="":
            command=u'self.devices[self.devicesIDArray["'+deviceId+u'"]][2]'
        else:
            command=u'self.devices[self.devicesIDArray["'+deviceId+u'"]][2]["'+vari+u'"]'
        return self.plugin.ServerExecute(command)
            
    def GetLabel(self,vari="???",deviceId="???",parseNoVari=True,parseNoDeviceId=True):
        return "Get setting for device "+deviceId+": "+vari
    
    def Configure(self,vari="",deviceId="",parseNoVari=False,parseNoDeviceId=False):
        panel = eg.ConfigPanel(self)
        st2 = panel.StaticText(Text.targetDeviceId)
        deviceIdCtrl = panel.TextCtrl(deviceId)
        parseNoDeviceIdCtrl = wx.CheckBox(panel, -1, Text.parsing)
        parseNoDeviceIdCtrl.SetValue(parseNoDeviceId)
        st3 = panel.StaticText(Text.variable+" ("+Text.optional+")")
        variCtrl = panel.TextCtrl(vari)
        parseNoVariCtrl = wx.CheckBox(panel, -1, Text.parsing)
        parseNoVariCtrl.SetValue(parseNoVari)
        eg.EqualizeWidths((st2,st3))
        panel.AddLine(st3, variCtrl, parseNoVariCtrl)
        panel.AddLine(st2, deviceIdCtrl, parseNoDeviceIdCtrl)
        while panel.Affirmed():
            panel.SetResult(
                variCtrl.GetValue(),
                deviceIdCtrl.GetValue(),
                parseNoVariCtrl.GetValue(),
                parseNoDeviceIdCtrl.GetValue(),
            )
            
            
class GetDevicesByType(eg.ActionBase):
    name = "Get Devices by Type"
    description = "Returns an array with all device IDs of a specific device type assigned to this PC."
    
    def __call__(self,type=""):
        type=unicode(type)
        if type=="" and eg.event.prefix=="O-CMD":
            type=eg.event.suffix.split(".")[1]
        ids=[]
        for tempDevice in self.plugin.devices:
            if tempDevice[1]==type and tempDevice[3]==self.plugin.thisPc:
                ids.append(tempDevice[0])
        return ids
            
    def GetLabel(self,type="???"):
        return "Get all devices of type: "+type
    
    def Configure(self,type=""):
        panel = eg.ConfigPanel(self)
        typeList=[]
        for tempType in self.plugin.extensions:
            if tempType[2]=="device":
                typeList.append(tempType[0])
        st2 = panel.StaticText(Text.targetType)
        typeCtrl = wx.Choice(panel, -1, choices=typeList)
        if type in typeList:
            typeCtrl.SetSelection(typeList.index(type))
        else:
            typeCtrl.SetSelection(0)
        panel.AddLine(st2, typeCtrl)
        while panel.Affirmed():
            panel.SetResult(
                typeCtrl.GetStringSelection(),
            )


class GetInterfacesByType(eg.ActionBase):
    name = "Get Interfaces by Type"
    description = "Returns an array with all interface IDs of a specific interface type assigned to this PC."
    
    def __call__(self,type=""):
        type=unicode(type)
        if type=="" and eg.event.prefix=="O-CMD":
            type=eg.event.suffix.split(".")[1]
        ids=[]
        for tempInterface in self.plugin.interfaces:
            if tempInterface[1]==type and tempInterface[3]==self.plugin.thisPc:
                ids.append(tempInterface[0])
        return ids
            
    def GetLabel(self,type="???"):
        return "Get all interfaces of type: "+type
    
    def Configure(self,type=""):
        panel = eg.ConfigPanel(self)
        typeList=[]
        for tempType in self.plugin.extensions:
            if tempType[2]=="interface":
                typeList.append(tempType[0])
        st2 = panel.StaticText(Text.targetType)
        typeCtrl = wx.Choice(panel, -1, choices=typeList)
        if type in typeList:
            typeCtrl.SetSelection(typeList.index(type))
        else:
            typeCtrl.SetSelection(0)
        panel.AddLine(st2, typeCtrl)
        while panel.Affirmed():
            panel.SetResult(
                typeCtrl.GetStringSelection(),
            )
            
            
class SetSettingForInterface(eg.ActionBase):
    name = "Set Setting for Interface"
    description = "Sets a setting for a specific O-MEGA Interface."
    
    def __call__(self,vari,value,interfaceId="",parseNoVari=True,parseNoValue=True,parseNoInterfaceId=True):
        if not parseNoVari:
            vari=eg.ParseString(unicode(vari))
        if not parseNoInterfaceId:
            interfaceId=eg.ParseString(unicode(interfaceId))
        if interfaceId=="" and eg.event.prefix=="O-CMD":
            interfaceId=eg.event.payload["target"]
        if isinstance(value, basestring) and not parseNoValue:
            value=eg.ParseString(value)
        command=u'self.interfaces[self.interfacesIDArray["'+interfaceId+u'"]][2]'
        oldData=self.plugin.ServerExecute(command)
        if vari not in oldData or oldData[vari]!=value:
            if isinstance(value, basestring):
                value='"'+value+'"'
            command=u'self.interfaces[self.interfacesIDArray["'+interfaceId+u'"]][2]["'+vari+u'"]='+unicode(value)
            self.plugin.ServerExecute(command)
        return True
    
    def GetLabel(self,vari="???",value="???",interfaceId="???",parseNoVari=True,parseNoValue=True,parseNoInterfaceId=True):
        return "Set setting for interface "+interfaceId+": "+vari+" to "+unicode(value)
    
    def Configure(self,vari="",value="",interfaceId="",parseNoVari=False,parseNoValue=False,parseNoInterfaceId=False):
        panel = eg.ConfigPanel(self)
        st2 = panel.StaticText(Text.targetInterfaceId)
        interfaceIdCtrl = panel.TextCtrl(interfaceId)
        parseNoInterfaceIdCtrl = wx.CheckBox(panel, -1, Text.parsing)
        parseNoInterfaceIdCtrl.SetValue(parseNoInterfaceId)
        st3 = panel.StaticText(Text.variable)
        variCtrl = panel.TextCtrl(vari)
        parseNoVariCtrl = wx.CheckBox(panel, -1, Text.parsing)
        parseNoVariCtrl.SetValue(parseNoVari)
        st4 = panel.StaticText(Text.value)
        valueCtrl = panel.TextCtrl(unicode(value), size=(400,-1))
        parseNoValueCtrl = wx.CheckBox(panel, -1, Text.parsing)
        parseNoValueCtrl.SetValue(parseNoValue)
        eg.EqualizeWidths((st2,st3,st4))
        panel.AddLine(st3, variCtrl, parseNoVariCtrl)
        panel.AddLine(st4, valueCtrl, parseNoValueCtrl)
        panel.AddLine(st2, interfaceIdCtrl, parseNoInterfaceIdCtrl)
        while panel.Affirmed():
            panel.SetResult(
                variCtrl.GetValue(),
                valueCtrl.GetValue(),
                interfaceIdCtrl.GetValue(),
                parseNoVariCtrl.GetValue(),
                parseNoValueCtrl.GetValue(),
                parseNoInterfaceIdCtrl.GetValue(),
            )
            
            
class GetSettingForInterface(eg.ActionBase):
    name = "Get Setting for Interface"
    description = "Returns a setting for a specific O-MEGA Interface."
    
    def __call__(self,vari="",interfaceId="",parseNoVari=True,parseNoInterfaceId=True):
        interfaceId=eg.ParseString(unicode(interfaceId))
        if interfaceId=="" and eg.event.prefix=="O-CMD":
            interfaceId=eg.event.payload["target"]
        vari=eg.ParseString(unicode(vari))
        if vari=="":
            command=u'self.interfaces[self.interfacesIDArray["'+interfaceId+u'"]][2]'
        else:
            command=u'self.interfaces[self.interfacesIDArray["'+interfaceId+u'"]][2]["'+vari+u'"]'
        return self.plugin.ServerExecute(command)
            
    def GetLabel(self,vari="???",interfaceId="???",parseNoVari=True,parseNoInterfaceId=True):
        return "Get setting for interface "+interfaceId+": "+vari
    
    def Configure(self,vari="",interfaceId="",parseNoVari=False,parseNoInterfaceId=False):
        panel = eg.ConfigPanel(self)
        st2 = panel.StaticText(Text.targetInterfaceId)
        interfaceIdCtrl = panel.TextCtrl(interfaceId)
        parseNoInterfaceIdCtrl = wx.CheckBox(panel, -1, Text.parsing)
        parseNoInterfaceIdCtrl.SetValue(parseNoInterfaceId)
        st3 = panel.StaticText(Text.variable+" ("+Text.optional+")")
        variCtrl = panel.TextCtrl(vari)
        parseNoVariCtrl = wx.CheckBox(panel, -1, Text.parsing)
        parseNoVariCtrl.SetValue(parseNoVari)
        eg.EqualizeWidths((st2,st3))
        panel.AddLine(st3, variCtrl, parseNoVariCtrl)
        panel.AddLine(st2, interfaceIdCtrl, parseNoInterfaceIdCtrl)
        while panel.Affirmed():
            panel.SetResult(
                variCtrl.GetValue(),
                interfaceIdCtrl.GetValue(),
                parseNoVariCtrl.GetValue(),
                parseNoInterfaceIdCtrl.GetValue(),
            )
            

class SetButtonValue(eg.ActionBase):
    name = "Set Button Value"
    description = "Sets the value for a specific O-MEGA Button."
    
    def __call__(self,value,buttonId="",parseNoValue=True,parseNoButtonId=True):
        if not parseNoButtonId:
            buttonId=eg.ParseString(unicode(buttonId))
        if buttonId=="":
            buttonId=eg.event.payload["id"]
        if isinstance(value, basestring) and not parseNoValue:
            value=eg.ParseString(value)
        command=u'self.buttonStates["'+buttonId+u'"]["value"]'
        try:
            oldValue=self.plugin.ServerExecute(command)
        except KeyError, e:
            command=u'self.buttonStates["'+buttonId+u'"]={u"value": u"?", u"state": u"[?]"}'
            self.plugin.ServerExecute(command)
            oldValue="?"
        if oldValue!=value:
            if isinstance(value, basestring):
                value='"'+value+'"'
            command=u'self.buttonStates["'+buttonId+u'"]["value"]='+unicode(value)
            self.plugin.ServerExecute(command)
            command=u'self.hashs["buttons"]+=1'
            self.plugin.ServerExecute(command)
        return True
    
    def GetLabel(self,value="???",buttonId="???",parseNoValue=True,parseNoButtonId=True):
        return "Set value for button "+buttonId+" to "+unicode(value)
    
    def Configure(self,value="",buttonId="",parseNoValue=False,parseNoButtonId=False):
        panel = eg.ConfigPanel(self)
        st2 = panel.StaticText(Text.targetButtonId)
        buttonIdCtrl = panel.TextCtrl(buttonId)
        parseNoButtonIdCtrl = wx.CheckBox(panel, -1, Text.parsing)
        parseNoButtonIdCtrl.SetValue(parseNoButtonId)
        st4 = panel.StaticText(Text.value)
        valueCtrl = panel.TextCtrl(unicode(value), size=(400,-1))
        parseNoValueCtrl = wx.CheckBox(panel, -1, Text.parsing)
        parseNoValueCtrl.SetValue(parseNoValue)
        eg.EqualizeWidths((st2,st4))
        panel.AddLine(st4, valueCtrl, parseNoValueCtrl)
        panel.AddLine(st2, buttonIdCtrl, parseNoButtonIdCtrl)
        while panel.Affirmed():
            panel.SetResult(
                valueCtrl.GetValue(),
                buttonIdCtrl.GetValue(),
                parseNoValueCtrl.GetValue(),
                parseNoButtonIdCtrl.GetValue(),
            )
            
            
class GetButtonValue(eg.ActionBase):
    name = "Get Button Value"
    description = "Returns the value for a specific O-MEGA Button."
    
    def __call__(self,buttonId="",parseNoButtonId=True):
        if not parseNoButtonId:
            buttonId=eg.ParseString(unicode(buttonId))
        if buttonId == "":
            buttonId = eg.event.payload["id"]
        command=u'self.buttonStates["'+buttonId+u'"]["value"]'
        return self.plugin.ServerExecute(command)
            
    def GetLabel(self,buttonId="???",parseNoButtonId=True):
        return "Get value for button: "+buttonId
    
    def Configure(self,buttonId="",parseNoButtonId=False):
        panel = eg.ConfigPanel(self)
        st2 = panel.StaticText(Text.targetButtonId)
        buttonIdCtrl = panel.TextCtrl(buttonId)
        parseNoButtonIdCtrl = wx.CheckBox(panel, -1, Text.parsing)
        parseNoButtonIdCtrl.SetValue(parseNoButtonId)
        panel.AddLine(st2, buttonIdCtrl, parseNoButtonIdCtrl)
        while panel.Affirmed():
            panel.SetResult(
                buttonIdCtrl.GetValue(),
                parseNoButtonIdCtrl.GetValue(),
            )


class SetButtonState(eg.ActionBase):
    name = "Set Button State"
    description = "Sets the state for a specific O-MEGA Button."
    
    def __call__(self,state,buttonId="",parseNoState=True,parseNoButtonId=True):
        if not parseNoState:
            state=eg.ParseString(unicode(state))
        if state in self.plugin.validStates or (state[0]=="#" and state[1:] in self.plugin.validStates):
            pass
        else:
            eg.PrintError("O-MEGA: The state "+state+" is not a valid O-MEGA state!")
            return False
        if not parseNoButtonId:
            buttonId=eg.ParseString(unicode(buttonId))
        if buttonId=="":
            buttonId=eg.event.payload["id"]
        command=u'self.buttonStates["'+buttonId+u'"]["state"]'
        try:
            oldState=self.plugin.ServerExecute(command)
        except KeyError, e:
            command=u'self.buttonStates["'+buttonId+u'"]={u"value": u"?", u"state": u"[?]"}'
            self.plugin.ServerExecute(command)
            oldState="[?]"
        if oldState!=state:
            if isinstance(state, basestring):
                state='"'+state+'"'
            command=u'self.buttonStates["'+buttonId+u'"]["state"]='+unicode(state)
            self.plugin.ServerExecute(command)
            command=u'self.hashs["buttons"]+=1'
            self.plugin.ServerExecute(command)
        return True
    
    def GetLabel(self,state="???",buttonId="???",parseNoState=True,parseNoButtonId=True):
        return "Set state for button "+buttonId+" to "+unicode(state)
    
    def Configure(self,state="",buttonId="",parseNoState=False,parseNoButtonId=False):
        panel = eg.ConfigPanel(self)
        st2 = panel.StaticText(Text.targetButtonId)
        buttonIdCtrl = panel.TextCtrl(buttonId)
        parseNoButtonIdCtrl = wx.CheckBox(panel, -1, Text.parsing)
        parseNoButtonIdCtrl.SetValue(parseNoButtonId)
        st4 = panel.StaticText(Text.state)
        stateCtrl = wx.Choice(panel, -1, choices=self.plugin.validStates)
        parseNoStateCtrl = wx.CheckBox(panel, -1, Text.parsing)
        parseNoStateCtrl.SetValue(parseNoState)
        if state in self.plugin.validStates:
            stateCtrl.SetSelection(self.plugin.validStates.index(state))
        else:
            stateCtrl.SetSelection(0)
        eg.EqualizeWidths((st2,st4))
        panel.AddLine(st4, stateCtrl, parseNoStateCtrl)
        panel.AddLine(st2, buttonIdCtrl, parseNoButtonIdCtrl)
        while panel.Affirmed():
            panel.SetResult(
                stateCtrl.GetStringSelection(),
                buttonIdCtrl.GetValue(),
                parseNoStateCtrl.GetValue(),
                parseNoButtonIdCtrl.GetValue(),
            )
            
            
class GetButtonState(eg.ActionBase):
    name = "Get Button State"
    description = "Returns the state for a specific O-MEGA Button."
    
    def __call__(self,buttonId="",simplify=True,parseNoButtonId=True):
        if not parseNoButtonId:
            buttonId=eg.ParseString(unicode(buttonId))
        if buttonId == "":
            buttonId = eg.event.payload["id"]
        command=u'self.buttonStates["'+buttonId+u'"]["state"]'
        state=self.plugin.ServerExecute(command)
        if simplify and state[0]=="#":
            state=state[1:]
        return state
            
    def GetLabel(self,buttonId="???",simplify=True,parseNoButtonId=True):
        return "Get state for button: "+buttonId
    
    def Configure(self,buttonId="",simplify=True,parseNoButtonId=False):
        panel = eg.ConfigPanel(self)
        st2 = panel.StaticText(Text.targetButtonId)
        buttonIdCtrl = panel.TextCtrl(buttonId)
        parseNoButtonIdCtrl = wx.CheckBox(panel, -1, Text.parsing)
        parseNoButtonIdCtrl.SetValue(parseNoButtonId)
        simplifyCtrl = wx.CheckBox(panel, -1, Text.simplify)
        simplifyCtrl.SetValue(simplify)
        panel.AddLine(st2, buttonIdCtrl, parseNoButtonIdCtrl)
        panel.AddLine(simplifyCtrl)
        while panel.Affirmed():
            panel.SetResult(
                buttonIdCtrl.GetValue(),
                simplifyCtrl.GetValue(),
                parseNoButtonIdCtrl.GetValue(),
            )
            
    
class ProgramPower(eg.ActionBase):
    name = "Program Power"
    description = """Convenience function to power [on]/[off] programs.<br>
                  It can use the following extension settings:<br>
                  <br>
                  filePath : Absolute path to the executable (.exe) (required!)<br>
                  runParameter : Parameters that will be added when execution the executable / starting the program<br>
                  runAsAdmin : Run as Administrator (works only if EventGhost is executed as Administrator)<br>
                  <br>
                  To power off the program, it will be killed.<br>
                  <br>
                  !!Only works with O-CMD events!!"""
    
    def __call__(self):
        self.plugin.LogWrapper.programPower(eg.event)
 
#===============================================================================
# EventListner Start
#===============================================================================

class LogWrapper():
        
    def __init__(self,plugin):
        self.plugin  = plugin
        self.powerTimers={}
        

    def AddEventListener(self):
        if self not in eg.log.eventListeners:
            eg.log.AddEventListener(self)
            

    def StopAllEventListeners(self):
        if self in eg.log.eventListeners:
            eg.log.RemoveEventListener(self)
    
    
    def UpFunc(self,newEvent):
        #print "up!"
        newEvent.SetShouldEnd()
        
        
    def UpFuncRemote(self,eventRef,target):
        self.plugin.RequestData(target, self.plugin.info.args[0], self.plugin.info.args[1], u'self.UpFunc2(\''+eventRef+u'\')')
    
    
    def resolveDeviceDependencies(self,event):
        button=self.plugin.buttons[self.plugin.buttonsIDArray[event.payload["target"]]]
        target=button[1]+"/power"
        targetParts=button[1].split("/")
        if targetParts[0]=="devices":
            if button[2]=="power" and event.payload["targetState"]=="[off]":
                dev=self.plugin.devices[self.plugin.devicesIDArray[targetParts[1]]]
                if self.desolveDependencie(dev,event,"devices"):
                    if not self.isO(dev[0],"[off]","devices")[0]:
                        self.scheduleO(dev[0],event,event,"[off]","devices")
                else:
                    if self.plugin.buttonStates[target]["state"]!="#[off]" and self.plugin.buttonStates[target]["state"]!="[off]":
                        oldState=self.plugin.buttonStates[target]["state"]
                        self.plugin.States["devices"][targetParts[1]]["power"]="#"+event.payload["targetState"]
                        self.plugin.buttonStates[target]["state"]="#"+event.payload["targetState"] #still need to reset buttonStatesPre
                        self.plugin.incrementHash("devices")
                        self.plugin.incrementHash("buttons")
                        eg.TriggerEvent(prefix="O-EVT", suffix="Button.State."+target+".#"+event.payload["targetState"],payload={"id":target,"new":"#"+event.payload["targetState"],"old":oldState})
                    return False
            elif self.plugin.buttonStates[target]["state"]=="[on]":
                pass
            elif ("[on]" in self.plugin.buttons[self.plugin.buttonsIDArray[target]][6] and self.plugin.buttons[self.plugin.buttonsIDArray[target]][6]["[on]"][0][0]!="") or ("[on]" not in self.plugin.buttons[self.plugin.buttonsIDArray[target]][6] or self.plugin.buttons[self.plugin.buttonsIDArray[target]][6]["[on]"][0][0]==""):
                if button[2]=="power" and event.payload["targetState"]=="[on]":
                    dev=self.plugin.devices[self.plugin.devicesIDArray[targetParts[1]]]
                    if self.resolveDependencie(dev,event,"devices"):
                        if not self.isO(dev[0],"[on]","devices")[0]:
                            self.scheduleO(dev[0],event,event,"[on]","devices")
                    else:
                        if self.plugin.buttonStates[target]["state"]!="#[on]" and self.plugin.buttonStates[target]["state"]!="[on]":
                            oldState=self.plugin.buttonStates[target]["state"]
                            self.plugin.States["devices"][targetParts[1]]["power"]="#"+event.payload["targetState"]
                            self.plugin.buttonStates[target]["state"]="#"+event.payload["targetState"] #still need to reset buttonStatesPre
                            self.plugin.incrementHash("devices")
                            self.plugin.incrementHash("buttons")
                            eg.TriggerEvent(prefix="O-EVT", suffix="Button.State."+target+".#"+event.payload["targetState"],payload={"id":target,"new":"#"+event.payload["targetState"],"old":oldState})
                        return False
        elif targetParts[0]=="interfaces":
            intf=self.plugin.interfaces[self.plugin.interfacesIDArray[targetParts[1]]]
            return self.resolveDependencie(intf,event,"interfaces")
        elif targetParts[0]=="programs":
            if button[2]=="power" and event.payload["targetState"]=="[off]":
                prog=self.plugin.programs[self.plugin.programsIDArray[targetParts[1]]]
                if not self.isO(prog[0],"[off]","programs")[0]:
                    self.scheduleO(prog[0],event,event,"[off]","programs")
            elif self.plugin.buttonStates[target]["state"]=="[on]":
                pass
            elif ("[on]" in self.plugin.buttons[self.plugin.buttonsIDArray[target]][6] and self.plugin.buttons[self.plugin.buttonsIDArray[target]][6]["[on]"][0][0]!="") or ("[on]" not in self.plugin.buttons[self.plugin.buttonsIDArray[target]][6] or self.plugin.buttons[self.plugin.buttonsIDArray[target]][6]["[on]"][0][0]==""):
                if button[2]=="power" and event.payload["targetState"]=="[on]":
                    prog=self.plugin.programs[self.plugin.programsIDArray[targetParts[1]]]
                    if self.resolveDependencie(prog,event,"programs"):
                        if not self.isO(prog[0],"[on]","programs")[0]:
                            self.scheduleO(prog[0],event,event,"[on]","programs")
                    else:
                        if self.plugin.buttonStates[target]["state"]!="#[on]" and self.plugin.buttonStates[target]["state"]!="[on]":
                            oldState=self.plugin.buttonStates[target]["state"]
                            self.plugin.States["programs"][targetParts[1]]["power"]="#"+event.payload["targetState"]
                            self.plugin.buttonStates[target]["state"]="#"+event.payload["targetState"] #still need to reset buttonStatesPre
                            self.plugin.incrementHash("programs")
                            self.plugin.incrementHash("buttons")
                            eg.TriggerEvent(prefix="O-EVT", suffix="Button.State."+target+".#"+event.payload["targetState"],payload={"id":target,"new":"#"+event.payload["targetState"],"old":oldState})
                        return False
        return True

    
    resolvedDevices={"[on]":[],"[off]":[]}
    
    def resolveDependencie(self,item,event,type):
        if type+"/"+item[0] in self.resolvedDevices["[off]"]:
            self.resolvedDevices["[off]"].remove(type+"/"+item[0])
        if type+"/"+item[0] not in self.resolvedDevices["[on]"]:
            self.resolvedDevices["[on]"].append(type+"/"+item[0])
        allTrue=True
        for dependencie in item[4]:
            if dependencie!="":
                if "devices/"+dependencie not in self.resolvedDevices["[on]"]:
                    if not self.turnO(dependencie,event,"[on]","devices",True):
                        allTrue=False
        if not allTrue:
            return False
        self.resolvedDevices["[on]"].remove(type+"/"+item[0])
        return True
    
    
    def isO(self,deviceID,targetState,type):
        target=type+"/"+deviceID+"/power"
        dev2PowerButton=self.plugin.buttons[self.plugin.buttonsIDArray[target]]
        if self.plugin.buttonStates[target]["state"]==targetState:
            if target in self.powerTimers:
                try:
                    eg.scheduler.CancelTask(self.powerTimers[target]["task"])
                except:
                    pass
                del self.powerTimers[target]
            return [True, True]
        elif targetState in dev2PowerButton[6] and dev2PowerButton[6][targetState][0][0]!="":
            return [False, True]
        elif (targetState not in dev2PowerButton[6] or dev2PowerButton[6][targetState][0][0]=="") and self.plugin.buttonStates[target]["state"]!="#"+targetState:
            return [False, False]
        else:
            if target in self.powerTimers:
                try:
                    eg.scheduler.CancelTask(self.powerTimers[target]["task"])
                except:
                    pass
                del self.powerTimers[target]
            return [True, False]#[state, sure]
    
    
    def turnO(self,deviceID,event,targetState,type,forDependencie=False):
        target=type+"/"+deviceID+"/power"
        if type=="devices" and self.plugin.devices[self.plugin.devicesIDArray[deviceID]][1]=="Pseudo_Device":
            target=self.plugin.devices[self.plugin.devicesIDArray[deviceID]][2]["buttonIDSelector"]
        dev2PowerButton=self.plugin.buttons[self.plugin.buttonsIDArray[target]]
        #print "turn "+targetState+" "+target
        if self.plugin.buttonStates[target]["state"]==targetState:
            pass
        elif targetState in dev2PowerButton[6] and dev2PowerButton[6][targetState][0][0]!="":
            if target in self.powerTimers and self.powerTimers[target]["targetState"]==targetState:
                if not self.powerTimers[target]["task"] in eg.scheduler.heap:
                    print "OMEGA: Turning "+targetState+" "+target+", because it's not and no schedule for it is running"
                    eg.TriggerEvent(prefix="O-MEGA", suffix="CMD.buttons",payload={"target":target,"targetState":targetState})
            else:
                print "OMEGA: Turning "+targetState+" "+target+", because it's not and no schedule for it existis"
                eg.TriggerEvent(prefix="O-MEGA", suffix="CMD.buttons",payload={"target":target,"targetState":targetState})
            tempEvent=self.emptyEvent(prefix="O-MEGA", suffix="CMD.buttons",payload={"target":target,"targetState":targetState})
            #self.LogEvent(tempEvent,True)
            if event is not None:
                if self.scheduleO(deviceID,event,tempEvent,targetState,type,forDependencie):
                    return False
        elif (targetState not in dev2PowerButton[6] or dev2PowerButton[6][targetState][0][0]=="") and self.plugin.buttonStates[target]["state"]!="#"+targetState:
            if target in self.powerTimers and self.powerTimers[target]["targetState"]==targetState:
                if not self.powerTimers[target]["task"] in eg.scheduler.heap:
                    print "OMEGA: Turning "+targetState+" "+target+", because it's not (not even planned) and no schedule for it is running"
                    eg.TriggerEvent(prefix="O-MEGA", suffix="CMD.buttons",payload={"target":target,"targetState":targetState})
            else:
                print "OMEGA: Turning "+targetState+" "+target+", because it's not (not even planned) and no schedule for it existis"
                eg.TriggerEvent(prefix="O-MEGA", suffix="CMD.buttons",payload={"target":target,"targetState":targetState})
            tempEvent=self.emptyEvent(prefix="O-MEGA", suffix="CMD.buttons",payload={"target":target,"targetState":targetState})
            #self.LogEvent(tempEvent,True)
            if event is not None:
                self.scheduleO(deviceID,event,tempEvent,targetState,type,forDependencie)
            return False
        return True
    
    
    def scheduleO(self,deviceID,sourceEvent,triggerEvent,targetState,type="devices",forDependencie=False):
        if type=="programs":
            dev2=self.plugin.programs[self.plugin.programsIDArray[deviceID]]
        else:
            type="devices"
            dev2=self.plugin.devices[self.plugin.devicesIDArray[deviceID]]
        target=type+"/"+deviceID+"/power"
        #print "schedule for "+target+" "+targetState
        powerCounter=0
        if target in self.powerTimers and self.powerTimers[target]["targetState"]==targetState:
            if not self.powerTimers[target]["task"] in eg.scheduler.heap:
                powerCounter=self.powerTimers[target]["counter"]
                powerCounter+=1
            #    print "powerCounter "+str(powerCounter)
            else:
                #print "nope, sorry"
                return True
        if targetState=="[on]":
            maxRetry=int(dev2[2]["maxOnRetry"])
            maxTime=float(dev2[2]["maxOnTime"])
        elif targetState=="[off]":
            maxRetry=int(dev2[2]["maxOffRetry"])
            maxTime=float(dev2[2]["maxOffTime"])
        try:
            eg.scheduler.CancelTask(self.powerTimers[target]["task"])
        except:
            pass
        #print "maxRetry: " +str(maxRetry)
        if maxRetry<0 or powerCounter<maxRetry or powerCounter==0:
            task=eg.scheduler.AddTask(maxTime, eg.TriggerEvent, prefix=triggerEvent.prefix, suffix=triggerEvent.suffix, payload=triggerEvent.payload)
            if target not in self.powerTimers or self.powerTimers[target]["targetState"]!=targetState:
                self.powerTimers[target]={"event":sourceEvent,"targetState":targetState,"forDependencie":forDependencie}
            self.powerTimers[target]["task"]=task
            self.powerTimers[target]["counter"]=powerCounter
        #    print "True"
            return True
        elif powerCounter>=maxRetry and self.powerTimers[target]["event"] is not None: #generates endless loops?
            if type+"/"+deviceID not in self.resolvedDevices[targetState]:
                self.resolvedDevices[targetState].append(type+"/"+deviceID)
            tempEvent=self.powerTimers[target]["event"]
            eg.TriggerEvent(prefix=tempEvent.prefix, suffix=tempEvent.suffix, payload=tempEvent.payload)
            self.powerTimers[target]["event"]=None
        #print "False"
        return False
        
            
    
    def desolveDependencie(self,item,event,type):
        if type+"/"+item[0] in self.resolvedDevices["[on]"]:
            self.resolvedDevices["[on]"].remove(type+"/"+item[0])
        if type+"/"+item[0] not in self.resolvedDevices["[off]"]:
            self.resolvedDevices["[off]"].append(type+"/"+item[0])
        allTrue=True
        for dev in self.plugin.devices:
            for dependencie in dev[4]:
                if dependencie!="" and dependencie==item[0]:
                    if "devices/"+dev[0] not in self.resolvedDevices["[off]"]:
                        if not self.turnO(dev[0],event,"[off]","devices",True):
                            allTrue=False
        for prog in self.plugin.programs:
            for dependencie in prog[4]:
                if dependencie!="" and dependencie==item[0]:
                    if "programs/"+prog[0] not in self.resolvedDevices["[off]"]:
                        if not self.turnO(prog[0],event,"[off]","programs",True):
                            allTrue=False
        if not allTrue:
            return False
        self.resolvedDevices["[off]"].remove(type+"/"+item[0])
        return True
    
    
    def resolveButton(self,event):
        id=event.payload["target"]
        targetState=event.payload["targetState"]
        if "targetValue" in event.payload:
            targetValue=event.payload["targetValue"]
        else:
            targetValue=[]
        buttonData=self.plugin.buttons[self.plugin.buttonsIDArray[id]]
        target=buttonData[1].split("/")
        targetMode=buttonData[2]
        if target[0]=="macro" and targetMode=="copy":#[u'24/0', u'macro', u'copy', [u'0', u'2', u'2'], [u'[on]', u'[off]'], u'{"[on]":["[on]"],"[off]":["[off]"],"buttonID":"2/lg-32lm611s-za/0"}', u'', u'', 1, [u'']]
            id=buttonData[5]["buttonID"]
            targetState=buttonData[5][targetState][0]
            buttonData=self.plugin.buttons[self.plugin.buttonsIDArray[id]]
            target=buttonData[1].split("/")
            targetMode=buttonData[2]
        if buttonData[6]=={} and targetMode=="power" and target[0]!="interfaces":
            id=buttonData[1]+"/"+targetMode
            buttonData=self.plugin.buttons[self.plugin.buttonsIDArray[id]]
        if targetState=="[value]" and (buttonData[6]=={} or "[value]" in buttonData[6] and buttonData[6]["[value]"][0][0]=="") and len(targetValue)>0 and targetValue[0]!=None:
            self.plugin.valueSave(id,targetValue[0])#????????????????????????????
        eventname=target[0]
        if target[0]=="devices":
            tempData=self.plugin.devices[self.plugin.devicesIDArray[target[1]]]
            if tempData[1]=="PC_WIN":
                eventname="EXT."+target[1]+"."+target[0]+"."+tempData[1]+"."+targetMode
            else:
                eventname="EXT."+tempData[3]+"."+target[0]+"."+tempData[1]+"."+targetMode
            #    eventname="CMD."+target[0]+"."+tempData[1]+"."+targetMode
        elif target[0]=="interfaces":
            tempData=self.plugin.interfaces[self.plugin.interfacesIDArray[target[1]]]
            eventname="EXT."+tempData[3]+"."+target[0]+"."+tempData[1]+"."+targetMode
        elif target[0]=="programs":
            tempData=self.plugin.programs[self.plugin.programsIDArray[target[1]]]
            eventname="EXT."+tempData[3]+"."+target[0]+"."+tempData[1]+"."+targetMode
        if len(target)==2:
            tempData=buttonData[5]
            tempData2=tempData #.replace("{value}",self.plugin.buttonStates[id]["value"])
            if targetState[0]!="[":
                try:
                    targetState=eval(targetState)
                except:
                    pass
            if tempData!={}:
                if targetState not in tempData and "[value]" in tempData:
                    tempData[targetState]=tempData["[value]"]
                if targetState in tempData:
                    tempData=tempData[targetState]
                    tempData2=tempData
                    if type(tempData) is dict:
                        tempData2={}
                        for parameter in tempData:
                            if tempData[parameter][1]!=0 and len(targetValue)>=tempData[parameter][1] and targetValue[(tempData[parameter][1]-1)]!=None:
                                tempData2[parameter]=targetValue[(tempData[parameter][1]-1)]
                            else:
                                tempData2[parameter]=tempData[parameter][0]
                            if isinstance(tempData2[parameter], basestring):
                                if "{value}" in tempData2[parameter] and id in self.plugin.buttonStates:
                                    tempData2[parameter]=tempData2[parameter].replace("{value}",self.plugin.buttonStates[id]["value"])
                                tempData2[parameter]=eg.ParseString(tempData2[parameter])
                else:
                    eg.PrintError("O-MEGA: State "+targetState+" does not exist on button "+id+"!")
            event.payload={"target":target[1],"targetState":targetState,"data":tempData2,"id":id}
            if id in self.plugin.buttonStates:
                event.payload["oldState"]=self.plugin.buttonStates[id]["state"]
            else:
                event.payload["oldState"]="[?]"
        else: #for integrated macros (does only trigger a button)
            eventname="CMD."+target[0]
            event.payload={"target":id,"targetState":targetState,"targetValue":targetValue,"view":event.payload["view"],"user":event.payload["user"]}
        event.suffix=eventname
        if (targetState!="[value]" or len(targetValue)==0) and id in self.plugin.buttonStates and self.plugin.buttonStates[id]["state"]!=targetState and self.plugin.buttonStates[id]["state"]!="#"+targetState and (targetState in buttonData[6] and buttonData[6][targetState][0][0]!="" or buttonData[0]=="power"):
            oldState=self.plugin.buttonStates[id]["state"]
            self.plugin.buttonStates[id]["state"]="#"+targetState
            if targetMode=="power" and target[0]!="interfaces":
                self.plugin.States[target[0]][target[1]][targetMode]="#"+targetState
                self.plugin.incrementHash(target[0])
                #eg.TriggerEvent(prefix="O-EVT", suffix="Button.State."+target[0]+"/"+target[1]+"/power.#"+targetState,payload={"id":id,"new":"#"+targetState,"old":oldState})
            if id in self.plugin.buttonsRIds:
                thisButtonStatesPre=self.plugin.buttonStatesPre[id]
                thisButtonInterestingStates=self.plugin.buttonInterestingStates[id]
                for k1 in thisButtonInterestingStates:
                    thisButtonStatesPre[k1]=[]
                    for k in buttonData[6][k1]:
                        thisButtonStatesPre[k1].append(False)
            self.plugin.incrementHash("buttons")
            eg.TriggerEvent(prefix="O-EVT", suffix="Button.State."+id+".#"+targetState,payload={"id":id,"new":"#"+targetState,"old":oldState})
        return event
    
    
    def resolveToggleButton(self,event):
        id = event.payload["target"]
        buttonData = self.plugin.buttons[self.plugin.buttonsIDArray[id]]
        target=buttonData[1].split("/")
        targetMode=buttonData[2]
        statesDict=None
        if target[0]=="macro" and targetMode=="copy":
            id=buttonData[5]["buttonID"]
            statesDict=buttonData[5]
            buttonData=self.plugin.buttons[self.plugin.buttonsIDArray[id]]
            target=buttonData[1].split("/")
            targetMode=buttonData[2]
        if buttonData[6]=={} and targetMode=="power" and target[0]!="interfaces":
            id=buttonData[1]+"/"+targetMode
            buttonData=self.plugin.buttons[self.plugin.buttonsIDArray[id]]
        if id in self.plugin.buttonStates:
            if len(buttonData[5].keys())==2:
                tempKeys=buttonData[5].keys()
                if self.plugin.buttonStates[id]["state"]==tempKeys[0] or self.plugin.buttonStates[id]["state"]=="#"+tempKeys[0]:
                    event.payload["targetState"]=tempKeys[1]
                else:
                    event.payload["targetState"]=tempKeys[0]
            elif "[on]" in buttonData[4] and "[off]" in buttonData[4]:
                if self.plugin.buttonStates[id]["state"]=="[on]" or self.plugin.buttonStates[id]["state"]=="#[on]":
                    event.payload["targetState"]="[off]"
                elif self.plugin.buttonStates[id]["state"]=="[off]" or self.plugin.buttonStates[id]["state"]=="#[off]":
                    event.payload["targetState"]="[on]"
            elif "[open]" in buttonData[4] and "[close]" in buttonData[4]:
                if self.plugin.buttonStates[id]["state"]=="[open]" or self.plugin.buttonStates[id]["state"]=="#[open]":
                    event.payload["targetState"]="[close]"
                elif self.plugin.buttonStates[id]["state"]=="[close]" or self.plugin.buttonStates[id]["state"]=="#[close]":
                    event.payload["targetState"]="[open]"
            else:
                return event
            if statesDict:
                for tempState in statesDict:
                    if statesDict[tempState][0]==event.payload["targetState"]:
                        event.payload["targetState"]=tempState
        return event

    
    def LogEvent(self, event, priority=False):
        if event.prefix=="O-CMD":
            eSuffix=event.suffix
            if eSuffix=="devices.PC_WIN.power":
                self.winPcPower(event)
            elif eSuffix=="devices.PC_WIN.pyCommand":
                self.winPcPyCommand(event)
            elif eSuffix=="devices.PC_WIN.browserRename":
                self.browserRename(event)
            elif eSuffix=="devices.PC_WIN.browserNewFolder":
                self.browserNewFolder(event)
            elif eSuffix=="devices.PC_WIN.browserRun":
                self.browserRun(event)
            elif eSuffix=="devices.PC_WIN.browserDelete":
                self.browserDelete(event)
            elif eSuffix=="devices.PC_WIN.openWith":
                self.browserOpenWith(event)
            elif eSuffix=="devices.PC_WIN.browserCopy":
                self.browserPaste(event)
            elif eSuffix=="devices.PC_WIN.browserLink":
                self.browserNewLink(event)
            elif eSuffix=="devices.PC_WIN.mouseButton":
                self.mouseButton(event)
            elif eSuffix=="devices.PC_WIN.keyboardType":
                self.keyboardType(event)
            elif eSuffix=="devices.PC_WIN.volume":
                self.winPcVolume(event)
            elif eSuffix=="devices.PC_WIN.mute":
                self.winPcMute(event)
            elif eSuffix=="programs.Generic_Prog.power":
                self.programPower(event)
            elif eSuffix=="devices.Pseudo_Device.power":
                self.turnO(event.payload["target"],event,event.payload["targetState"],"devices")
        elif event.prefix=="System":
            if event.suffix=="Application.Terminated.robocopy.browserCopy":
                self.browserPaste2(event)
            elif event.suffix=="Volume":
                self.resVolume(event)
            elif event.suffix=="Mute":
                self.resMute(event)
            elif event.suffix=="UnMute":
                self.resUnMute(event)
        if not self.plugin.pluginServer:
            if event.prefix!="O-CMD" and self.plugin.serverIP!="" and self.plugin.serverOnline:
                try:
                    eventRef=self.plugin.RequestData(self.plugin.serverIP, self.plugin.info.args[0], self.plugin.info.args[1], u'self.TriggerEnduringEvent2(prefix=\'O-EVT\',suffix=\'PC.'+event.prefix+u'.'+event.suffix+u'\',payload='+unicode([self.plugin.thisPc,event.payload])+u')')
                    if eventRef:
                        event.AddUpFunc(self.UpFuncRemote,eventRef,self.plugin.serverIP)
                except:
                    eg.PrintError("O-MEGA: Server ("+self.plugin.serverIP+":"+str(self.plugin.info.args[0])+") is not reachable!")
                    self.plugin.serverOnline = False
            elif event.prefix=="O-CMD" and event.suffix=="registerClientForServer":
                self.registerThisClient(event)
        else:
            if event.prefix=="O-MEGA":
                if event.suffix=="CMD.buttons":
                    if event.payload["targetState"]=="[toggle]":
                        event=self.resolveToggleButton(event)
                    if self.resolveDeviceDependencies(event):
                        event=self.resolveButton(event)
                    else:
                        return False
                suffparts=event.suffix.split(".")
                if suffparts[0]=="EXT":#button events
                    tempSuffix=".".join(suffparts[2:])
                    if tempSuffix=="devices.PC_WIN.event" and len(event.payload)>2 and "suffix" in event.payload["data"]:
                        tempSuffix=tempSuffix+"."+event.payload["data"]["suffix"]
                        event.payload["data"]=event.payload["data"]["payload"]
                    if suffparts[1]==self.plugin.thisPc:
                        if priority:
                            eg.TriggerEvent(prefix="O-CMD",suffix=tempSuffix,payload=event.payload)
                        else:
                            newEvent=eg.TriggerEnduringEvent(prefix="O-CMD",suffix=tempSuffix,payload=event.payload)
                            #event.AddUpFunc(self.UpFunc,newEvent)
                            thread = Thread(
                                target=self.forwardShouldEnd,
                                args=(event,newEvent, )
                            )
                            thread.start()
                    else:
                        if tempSuffix=="devices.PC_WIN.power" and event.payload["targetState"]=="[on]" and event.payload["oldState"]!="[on]":
                            eg.plugins.System.WakeOnLan(self.plugin.devices[self.plugin.devicesIDArray[suffparts[1]]][2]["mac"])
                        elif self.plugin.States[u"devices"][suffparts[1]][u"power"]=="[on]" or self.plugin.States[u"devices"][suffparts[1]][u"power"][0]=="#":
                            try:
                                if isinstance(event.payload,basestring):
                                    tempPayload=u"\""+unicode(event.payload)+u"\""
                                else:
                                    tempPayload=unicode(event.payload)
                                if priority:
                                    self.plugin.RequestDataFromClient(suffparts[1], u'eg.TriggerEvent(prefix=\'O-CMD\',suffix=\''+tempSuffix+u'\',payload='+tempPayload+u')')
                                else:
                                    eventRef=self.plugin.RequestDataFromClient(suffparts[1], u'self.TriggerEnduringEvent2(prefix=\'O-CMD\',suffix=\''+tempSuffix+u'\',payload='+tempPayload+u')')
                                    if eventRef:
                                        event.AddUpFunc(self.UpFuncRemote,eventRef,self.plugin.devices[self.plugin.devicesIDArray[suffparts[1]]][2]["host"])
                            except:
                                eg.PrintError("O-MEGA: Client "+suffparts[1]+" ("+self.plugin.devices[self.plugin.devicesIDArray[suffparts[1]]][2]["host"]+":"+str(self.plugin.info.args[0])+") is not reachable, the client will be shown as [off]!")
                                self.plugin.ShowDeviceAsOff(suffparts[1])
                        else:
                            eg.PrintError("O-MEGA: Client "+suffparts[1]+" ("+self.plugin.devices[self.plugin.devicesIDArray[suffparts[1]]][2]["host"]+":"+str(self.plugin.info.args[0])+") is not on!")
                elif suffparts[0]=="CMD":#For O-MEGA internal commands that are no button commands, important for unblocking
                    if priority:
                        eg.TriggerEvent(prefix="O-CMD",suffix=".".join(suffparts[1:]),payload=event.payload)
                    else:
                        newEvent=eg.TriggerEnduringEvent(prefix="O-CMD",suffix=".".join(suffparts[1:]),payload=event.payload)
                        #event.AddUpFunc(self.UpFunc,newEvent)
                        thread = Thread(
                            target=self.forwardShouldEnd,
                            args=(event,newEvent, )
                        )
                        thread.start()
                elif suffparts[0]=="Ping" and suffparts[1]=="PC" and suffparts[-1]=="ON":
                        tempPCID=".".join(suffparts[2:-1])
                        id=u"devices/"+tempPCID+u"/power"
                        oldState=self.plugin.buttonStates[id]["state"]
                        if oldState!="[on]":
                            self.plugin.buttonStates[id]["state"]="#[on]"
                            self.plugin.States["devices"][tempPCID]["power"]="#[on]"
                            self.plugin.incrementHash("devices")
                            self.plugin.incrementHash("buttons")
                            eg.TriggerEvent(prefix="O-EVT", suffix="Button.State."+id+".#[on]",payload={"id":id,"new":"#[on]","old":oldState})
                            thread = Thread(
                                target=self.plugin.connectClientPC,
                                args=(tempPCID, )
                            )
                            thread.start()
                elif suffparts[0]=="ClientPC" and suffparts[1]=="Connected":
                    self.plugin.updateDataFromClientPC(event.payload)
                else:
                    newEvent=eg.TriggerEnduringEvent(prefix="O-EVT",suffix="PC."+event.prefix+"."+event.suffix,payload=[self.plugin.thisPc,event.payload])
                    #event.AddUpFunc(self.UpFunc,newEvent)
                    thread = Thread(
                        target=self.forwardShouldEnd,
                        args=(event,newEvent, )
                    )
                    thread.start()
            elif event.prefix=="O-CMD":
                if event.suffix=="macro":
                    self.integratedMacro(event)
                elif event.suffix=="sceneStart":
                    self.sceneStart(event)
                elif event.suffix=="sceneOnOff":
                    self.sceneOnOff(event.payload["data"],event.payload["targetState"])
            elif event.prefix=="O-EVT":
                self.progressEvent(event)
            else: 
                newEvent=eg.TriggerEnduringEvent(prefix="O-EVT",suffix="PC."+event.prefix+"."+event.suffix,payload=[self.plugin.thisPc,event.payload])
                #event.AddUpFunc(self.UpFunc,newEvent)
                thread = Thread(
                    target=self.forwardShouldEnd,
                    args=(event,newEvent, )
                )
                thread.start()
                

    def forwardShouldEnd(self, oldEvent, newEvent):
        while not oldEvent.shouldEnd.isSet() and not newEvent.shouldEnd.isSet():
            time.sleep(0.01)
        newEvent.SetShouldEnd()
    
    
    def progressEvent(self, event):
        tempEvent=event.suffix
        suffparts=tempEvent.split(".")
        try:
            tempPayload=json.dumps(event.payload,ensure_ascii=False,separators=(',', ':'))
            self.plugin.eventLog.append([time.strftime("%H:%M:%S", time.localtime()),tempEvent,event.payload])
        except:
            tempPayload=[event.payload[0],unicode(event.payload[1])]
            self.plugin.eventLog.append([time.strftime("%H:%M:%S", time.localtime()),tempEvent,tempPayload])
            tempPayload=json.dumps(tempPayload,ensure_ascii=False,separators=(',', ':'))
        while len(self.plugin.eventLog)>128:
            self.plugin.eventLog.pop(0)
        try:
            tempNumber=ord(suffparts[1][0])
        except:
            tempNumber=937
        try:
            tempNumber2=ord(suffparts[2][0])
        except:
            tempNumber2=937
        if tempNumber<78:
            catID1=0
        elif tempNumber<91:
            catID1=1
        else:
            catID1=2
        if tempNumber2<78:
            catID2=0
        elif tempNumber2<91:
            catID2=1
        else:
            catID2=2
        for id in self.plugin.buttonResponseCategories[catID1][catID2]:
            tempButton=self.plugin.buttons[self.plugin.buttonsIDArray[id]]
            stateForThisButtonChanged=False
            thisButtonInterestingStates=self.plugin.buttonInterestingStates[id]
            for j in thisButtonInterestingStates:#j=state
                tempData=tempButton[6][j]
                lastTrueThen=-10
                for y in xrange(len(tempData)):#y=condition Index
                    if j!="[value]" or ("[value]" in tempButton[4] and "{value}" not in tempData[y][0] and "{value}" not in tempData[y][1]):
                        #if fnmatch(tempEvent,re.sub(r'[\[\]]',r'[\g<0>]',tempData[y][0].replace("{value}","*"))):
                        value=self.matchString(tempEvent,tempData[y][0])
                        oK=False  
                        if value!=False:
                            if tempData[y][1]!="":
                                #print tempButton[0]+": "+tempPayload+" <> "+tempData[y][1]
                                #if fnmatch(tempPayload,re.sub(r'[\[\]]',r'[\g<0>]',tempData[y][1].replace("{value}","*"))):
                                value2=self.matchString(tempPayload,tempData[y][1])
                                if value2!=False:
                                    oK=True
                            else:
                                oK=True
                        thisButtonStatesPre=self.plugin.buttonStatesPre[id]
                        if y>0 and tempData[y-1][2]=="ANDNOT" and thisButtonStatesPre[j][y-1]==True:
                            if oK:
                                continue
                            else:
                                oK=True
                        if oK:
                            if lastTrueThen==(y-1):
                                #if tempData[y][2]=="THEN":
                                #    lastTrueThen=y
                                continue
                            if thisButtonStatesPre[j][y]==False:
                                thisButtonStatesPre[j][y]=True
                                if tempData[y][2]=="THEN":
                                    lastTrueThen=y
                            if tempData[y][2]=="AND" or tempData[y][2]=="ANDNOT":
                                continue
                            elif tempData[y][2]=="THEN":
                                if y==0 or tempData[y-1][2]!="THEN" or thisButtonStatesPre[j][y-1]==True:
                                    pass
                                else:
                                    thisButtonStatesPre[j][y]=False
                                continue
                            elif y>0 and tempData[y-1][2]=="THEN":
                                oK=thisButtonStatesPre[j][y-1]
                            if oK and self.plugin.buttonStates[id]["state"]!=j:
                                for k1 in thisButtonInterestingStates:#
                                    thisButtonStatesPre[k1]=[]#
                                    for k in tempButton[6][k1]:#
                                        thisButtonStatesPre[k1].append(False)#
                                oldState=self.plugin.buttonStates[id]["state"]
                                self.plugin.buttonStates[id]["state"]=j
                                #print u'state '+id+" = "+j
                                self.plugin.incrementHash("buttons")
                                thisButton=self.plugin.buttons[self.plugin.buttonsIDArray[id]]
                                if thisButton[2]=="power":
                                    targetParts=thisButton[1].split("/")
                                    if targetParts[0]!="interfaces":
                                        self.plugin.States[targetParts[0]][targetParts[1]][thisButton[2]]=j
                                        self.plugin.incrementHash(targetParts[0])
                                        if thisButton[1]+"/power" in self.powerTimers and self.powerTimers[thisButton[1]+"/power"]["targetState"]==j:
                                            try:
                                                eg.scheduler.CancelTask(self.powerTimers[thisButton[1]+"/power"]["task"])
                                                if self.powerTimers[thisButton[1]+"/power"]["forDependencie"]:
                                                    tempEvent2=self.powerTimers[thisButton[1]+"/power"]["event"]
                                                    eg.TriggerEvent(prefix=tempEvent2.prefix, suffix=tempEvent2.suffix, payload=tempEvent2.payload)
                                            except:
                                                pass
                                            del self.powerTimers[thisButton[1]+"/power"]
                                        if j=="[on]":
                                            if targetParts[0]=="devices":
                                                tempDevice=self.plugin.devices[self.plugin.devicesIDArray[targetParts[1]]]
                                                allTrue=True
                                                for dependencie in tempDevice[4]:
                                                    if dependencie!="":
                                                        if "devices/"+dependencie in self.resolvedDevices["[off]"]:
                                                            allTrue=False
                                                            break
                                                if allTrue:
                                                    self.resolveDependencie(tempDevice,None,"devices")
                                            else:
                                                self.resolveDependencie(self.plugin.programs[self.plugin.programsIDArray[targetParts[1]]],None,targetParts[0])
                                        elif j=="[off]":
                                            if targetParts[0]=="devices":
                                                tempDevice=self.plugin.devices[self.plugin.devicesIDArray[targetParts[1]]]
                                                allTrue=True
                                                for dev in self.plugin.devices:
                                                    for dependencie in dev[4]:
                                                        if dependencie!="" and dependencie==tempDevice[0]:
                                                            if "devices/"+dev[0] in self.resolvedDevices["[on]"]:
                                                                allTrue=False
                                                                break
                                                if allTrue:
                                                    self.desolveDependencie(tempDevice,None,"devices")
                                eg.TriggerEvent(prefix="O-EVT", suffix="Button.State."+id+"."+j,payload={"id":id,"new":j,"old":oldState})
                                stateForThisButtonChanged=True
                                break#
                        elif tempData[y][2]!="THEN":
                            thisButtonStatesPre[j][y]=False
                if stateForThisButtonChanged:#
                    break#
            if "[value]" in tempButton[6] and tempButton[6]["[value]"][0]!="":
                tempData=tempButton[6]["[value]"]
                for y in xrange(len(tempData)):
                    value=self.matchString(tempEvent,tempData[y][0])
                    if value!=False:
                        if tempData[y][1]!="":
                            value2=self.matchString(tempPayload,tempData[y][1])
                            if value2!=False:
                                if "{value}" in tempData[y][1]:
                                    self.plugin.valueSave(id,value2)
                                elif "{value}" in tempData[y][0]:
                                    self.plugin.valueSave(id,value)
                        elif "{value}" in tempData[y][0]:
                            self.plugin.valueSave(id,value)
            #if stateForThisButtonChanged:
            #    thisButtonStatesPre=self.plugin.buttonStatesPre[id]
            #    for k1 in tempButton[6]:
            #        thisButtonStatesPre[k1]=[]
            #        for k in tempButton[6][k1]:
            #            thisButtonStatesPre[k1].append(False)
        for id in self.plugin.actionEventCategories[catID1][catID2]:
            actionEvent = self.plugin.actionEvents[id]
            for j in actionEvent[1]:
                #print tempEvent+" <> "+j[0]
                #if (fnmatch(tempEvent,re.sub(r'[\[\]]',r'[\g<0>]',j[0]))) and (j[1]=="" or fnmatch(tempPayload,re.sub(r'[\[\]]',r'[\g<0>]',j[1]))):
                value=self.matchString(tempEvent,j[0])
                if value!=False:
                    if j[1]!="":
                        value2=self.matchString(tempPayload,j[1])
                        if value2!=False:
                            value=value2
                        else:
                            continue
                    #print actionEvent[0]
                    #sceneName=actionEvent[0].split("'")[1]
                    #print "The value for "+sceneName+" is: '"+value+"'"
                    #self.plugin.actionValues[sceneName]=value
                    exec actionEvent[0]
                    break
                    
                    
    def matchString(self, string1, string2):
        #if string2==string1:
        #    return ""
        #elif "*" in string2 or "?" in string2 or "{value}" in string2:
        #string2=string2.replace("°","*")
        i2=0
        start=0
        end=0
        wildcard=0
        string2len=len(string2)
        for i1 in xrange(len(string1)):
            if i2==string2len:
                return False
            elif string2[i2]=="*":
                wildcard=1
                i2+=1
                if string2len==i2:
                    break
            elif string2len>(i2+6) and string2[i2:(i2+7)]=="{value}":
                wildcard=2
                i2+=7
                start=i1
                if string2len==i2:
                    end=len(string1)
                    break
            elif string1[i1]==string2[i2] or string2[i2]=="?":
                if wildcard==1:
                    wildcard=3
                elif wildcard==2:
                    end=i1
                    wildcard=4
                i2+=1
            else:
                if wildcard==0:
                    return False
                elif wildcard==3:
                    wildcard=1
                    i2-=1
                elif wildcard==4:
                    wildcard=2
                    i2-=1
        if i2==string2len:
            return string1[start:end]
        return False
#===============================================================================
# EventListner End
#===============================================================================
# EventActions Start
#===============================================================================
#--------------------------------ServerOnlyStart-------------------------------#
    class emptyEvent():
        prefix=""
        suffix=""
        payload=[]
        
        def __init__(self, suffix, payload=None, prefix="O-MEGA"):
            self.prefix=prefix
            self.suffix=suffix
            self.payload=payload

    
    def integratedMacro(self, event):
        data=event.payload
        id=data["target"]
        targetState=data["targetState"]
        if "targetValue" in data:
            targetValue=data["targetValue"]
        else:
            targetValue=[]
        buttonData=self.plugin.buttons[self.plugin.buttonsIDArray[id]]
        if "data" in data:
            currpos=data["data"]
        else:
            currpos=0
        data3=buttonData[5][targetState]
        i=currpos
        while i < len(data3):
            if data3[i][0]=="[wait]":
                try:
                    eg.scheduler.CancelTask(self.plugin.macroWait[id])
                except:
                    #print "Task "+id+" does not exist yet!"
                    pass
                tempEvent=self.emptyEvent(prefix=event.prefix, suffix=event.suffix, payload={"target":id,"targetState":targetState,"data":(i+1)})
                self.plugin.macroWait[id]=eg.scheduler.AddTask(float(data3[i][1]), self.integratedMacro, tempEvent)
                break
            else:
                buttonID=data3[i][0]
                targetState2=data3[i][1]
                targetValue2=[]
                j=0
                while j<len(targetValue):
                    targetValue2.append(targetValue[j])
                    j+=1
                tempEvent=self.emptyEvent(prefix="O-MEGA", suffix="CMD.buttons", payload={"target":buttonID,"targetState":targetState2,"targetValue":targetValue2})
                self.LogEvent(tempEvent,True)
            i+=1
                
                
    def sceneStart(self, event):
        data=event.payload.split(" ")
        id=int(data[0])
        behave=self.plugin.sceneNames[self.plugin.sceneNamesIds[id]][5]
        self.plugin.sceneAction(id,0,False,behave)
        
      
    def sceneOnOff(self, id, mode):
        id=int(id)
        if mode=="[off]":
            eg.plugins.SchedulGhost.DisableSchedule(u'scene'+unicode(id))
            eg.plugins.SchedulGhost.DataToXML()
            self.plugin.hashs["sceneData"]+=1
        elif mode=="[on]":
            eg.plugins.SchedulGhost.EnableSchedule(u'scene'+unicode(id))
            eg.plugins.SchedulGhost.DataToXML()
            self.plugin.hashs["sceneData"]+=1
        elif mode=="[activate]":
            eg.plugins.SchedulGhost.ForceScheduleImmediately(u'scene'+unicode(id),True)
        elif mode=="[stop]":
            oldState=self.plugin.sceneNames[self.plugin.sceneNamesIds[id]][2]
            if oldState!="[none]":
                self.plugin.removeActionEventsFor2('eg.plugins.OMEGA.plugin.sceneAction('+str(id)+',*,True)')
                try:
                    eg.scheduler.CancelTask(self.plugin.sceneWait[id])
                except:
                    print "O-MEGA: Task "+unicode(id)+" does not exist yet!"
                self.plugin.sceneNames[self.plugin.sceneNamesIds[id]][2]="[none]"
                self.plugin.hashs["scene"]+=1
                eg.TriggerEvent(prefix="O-EVT", suffix="Scene.State."+str(id)+".[none]",payload={"id":id,"new":"[none]","old":oldState,"name":self.plugin.sceneNames[self.plugin.sceneNamesIds[id]][1],"source":"interrupt"})

#--------------------------------ServerOnlyEnd---------------------------------#
#--------------------------------ClientOnlyStart-------------------------------#
    def registerThisClient(self,event):
        self.plugin.serverIP=event.payload[0]
        self.plugin.thisPc=event.payload[1]
        self.plugin.saveToReg("serverIP",self.plugin.serverIP)
        self.plugin.saveToReg("thisPc",self.plugin.thisPc)
        self.plugin.updateClient(event.payload[2])
        eg.TriggerEvent(prefix="System",suffix="Resume")
            
#--------------------------------ClientOnlyEnd---------------------------------#

    def winPcPower(self, event):
        if self.plugin.pluginServer:
            self.plugin.saveStates()
        if eg.document.isDirty:
            eg.document.Save()
        data=event.payload
        id=data["target"]
        if id=="test":
            oldstate=id
        else:
            targetState=data["targetState"]
            oldstate=data["oldState"]
        if targetState=="[off]":
            print "O-MEGA: PC will shut down now!"
            if oldstate=="#"+targetState:
                wx.CallAfter(eg.plugins.System.PowerDown,True)
            else:
                eg.scheduler.AddTask(1.0,eg.plugins.System.PowerDown,False)
                #wx.CallAfter(eg.plugins.System.PowerDown,False)
        elif targetState=="[restart]":
            print "O-MEGA: PC will restart now!"
            if oldstate=="#"+targetState:
                wx.CallAfter(eg.plugins.System.Reboot,True)
            else:
                eg.scheduler.AddTask(1.0,eg.plugins.System.Reboot,False)
                #wx.CallAfter(eg.plugins.System.Reboot,False)
        elif targetState=="[standby]":
            print "O-MEGA: PC will go to standby now!"
            eg.plugins.System.Standby(False)
        elif targetState=="[hibernate]":
            print "O-MEGA: PC will go to hibernate now!"
            #wx.CallAfter(eg.plugins.System.Hibernate,False)
            eg.plugins.System.Hibernate(False)
        elif targetState=="[on]":
            eg.TriggerEvent(prefix="System",suffix="Resume")
        else:
            eg.PrintError("O-MEGA: State "+targetState+" is unknown for PC power!")
            
            
    def winPcPyCommand(self, event):
        data=event.payload
        id=data["target"]
        data3=data["data"]
        command=u""
        for i in ["p1","p2","p3","p4","p5","p6","p7","p8","p9"]:
            if i in data3:
                command+=unicode(data3[i])
        exec unicode(command)
    
    
    def winPcVolume(self, event):
        mode=event.payload["targetState"]
        if mode=="[up]":
            eg.plugins.System.ChangeMasterVolumeBy(1.0, u'Primary Sound Driver')
        elif mode=="[down]":
            eg.plugins.System.ChangeMasterVolumeBy(-1.0, u'Primary Sound Driver')
        elif mode=="[value]":
            eg.plugins.System.SetMasterVolume(float(event.payload["targetValue"][0]), u'Primary Sound Driver')
    
    
    def winPcMute(self, event):
        mode=event.payload["targetState"]
        if mode=="[on]":
            eg.plugins.System.MuteOn(u'Primary Sound Driver')
        elif mode=="[off]":
            eg.plugins.System.MuteOff(u'Primary Sound Driver')

            
    def mouseButton(self, event):
        data=event.payload
        button=data["targetValue"][0]
        what=data["targetState"]
        coordinates=data["data"]
        eg.plugins.Mouse.MoveAbsolute(coordinates[0], coordinates[1], None, False, True)
        if button==1 and what=="[click]":
            eg.plugins.Mouse.LeftButton()
        elif button==2 and (what=="[click]" or what=="[up]"):
            eg.plugins.Mouse.RightButton()
        elif button==1 and what=="[up]":
            eg.plugins.Mouse.ToggleLeftButton(1)
        elif button==1 and what=="[down]":
            eg.plugins.Mouse.ToggleLeftButton(2)
    
    
    def keyboardType(self, event):
        data=event.payload["data"]
        self.plugin.sendKeys(event.payload["target"],data[0],data[1],data[2])#targetPC, data, hotKey=True, mode

            
    def programPower(self, event):
        data=event.payload
        id2=data["target"]
        targetState=data["targetState"]
        programData=self.plugin.programs[self.plugin.programsIDArray[id2]]
        if "filePath" in programData[2]:
            tempCommand=unicode(programData[2]["filePath"])
            if targetState=="[on]":
                tempParameter=""
                if "runParameter" in programData[2]:
                    tempParameter=programData[2]["runParameter"]
                if "runAsAdmin" in programData[2] and programData[2]["runAsAdmin"]=="1" or not self.plugin.runsAsAdmin:
                    print "O-MEGA: Executing: "+tempCommand
                    eg.plugins.System.Execute(tempCommand, tempParameter, 0, False, 2, u'', False, False, u'', True, True, False)
                else:
                    try:
                        eg.plugins.System.Execute(u'cmd.exe', u'/C SCHTASKS /Create /TN "\\EventGhost\\O-MEGAProg-'+id2+'" /XML "'+self.plugin.info.path+'\\progschedtemplate.xml" /F', 3, True, 2, u'', False, False, u'', True, True, False)
                        eg.plugins.System.Execute(u'cmd.exe', u'/C SCHTASKS /Change /TN "\\EventGhost\\O-MEGAProg-'+id2+'" /TR \'"'+tempCommand+'"'+tempParameter+'\'', 3, True, 2, u'', False, False, u'', True, True, False)
                        eg.plugins.System.Execute(u'cmd.exe', u'/C SCHTASKS /Run /I /TN "\\EventGhost\\O-MEGAProg-'+id2+'"', 3, False, 2, u'', False, False, u'', True, True, False)
                        print "O-MEGA: Running task: O-MEGAProg-"+id2
                    except:
                        print "O-MEGA: Executing: "+tempCommand
                        eg.plugins.System.Execute(tempCommand, tempParameter, 0, False, 2, u'', False, False, u'', True, True, False)
            elif targetState=="[off]":
                exe=tempCommand.split("\\")
                print "O-MEGA: Killing task: "+exe[-1]
                eg.plugins.System.Execute(u'cmd.exe', u'/C TASKKILL /F /IM "'+exe[-1]+'"', 3, False, 2, u'', False, False, u'', True, True, False)
            else:
                eg.PrintError("O-MEGA: State "+targetState+" is unknown for program power!")
            
            
    def resVolume(self, event):
        self.plugin.ServerExecute(u'self.States["devices"]["'+self.plugin.thisPc+'"]["volume"]="'+event.payload+'"')
          
    def resMute(self, event):
        self.plugin.ServerExecute(u'self.States["devices"]["'+self.plugin.thisPc+'"]["mute"]="[on]"')
        self.plugin.ServerExecute(u'self.States["devices"]["'+self.plugin.thisPc+'"]["volume"]="'+event.payload+'"')
        
    def resUnMute(self, event):
        self.plugin.ServerExecute(u'self.States["devices"]["'+self.plugin.thisPc+'"]["mute"]="'+event.payload+'"')
    
#---------------------------------browserStart---------------------------------#
    
    def browserRename(self, event):
        data=event.payload["data"]
        path=data["location"]
        newName=self.plugin.replaceTimeVars(data["name"])
        #print path+" to "+newName
        eg.plugins.System.Execute(u'cmd.exe', u'/C ren "'+path+'" "'+newName+'"', 3, True, 2, u'', False, False, u'', True, True, False)
        
        
    def browserNewFolder(self, event):
        data=event.payload["data"]
        path=data["location"]
        newName=self.plugin.replaceTimeVars(data["name"])
        newFolder=path+u"\\"+newName
        #print newFolder
        eg.plugins.System.Execute(u'cmd.exe', u'/C mkdir "'+newFolder+'"', 3, True, 2, u'', False, False, u'', True, True, False)
        
        
    def browserRun(self, event):
        data=event.payload["data"]
        #print data
        os.startfile(data,"open")
        
    
    def browserDelete(self, event):
        data=event.payload["data"]["targets"]
        for i in data:
            if i[1]=="folder":
                eg.plugins.System.Execute(u'cmd.exe', u'/C rmdir /S /Q "'+i[0]+'"', 3, True, 2, u'', False, False, u'', True, True, False)
            else:
                eg.plugins.System.Execute(u'cmd.exe', u'/C del /F /Q "'+i[0]+'"', 3, True, 2, u'', False, False, u'', True, True, False)
                
                
    def browserOpenWith(self, event):
        what=event.payload["data"][0]
        id=event.payload["data"][1]
        data=event.payload["data"][2]
        for i in data:
            eg.TriggerEvent(prefix="O-CMD",suffix=what,payload={"target":id,"data":i})
    
    
    browserRobocopyData=[]        
    def browserPaste(self, event):
        data=event.payload["data"]
        newLocation=self.plugin.replaceTimeVars(data["location"])
        options=data["parameters"]
        wait=False
        scene=""
        scenePos=""
        targets=data["targets"]
        process=False
        if len(self.browserRobocopyData)==0:
            process=True
        for i in range(len(targets)):
            tempArr=targets[i][0].split("\\")
            system=False
            if i==len(targets)-1 and data["wait"] and "scene" in data:
                wait=True
                scene=data["scene"]
                scenePos=data["scenePos"]
            if targets[i][1]=="folder":
                self.browserRobocopyData.append([u'"'+targets[i][0]+'" "'+newLocation+u'\\'+tempArr[-1]+u'" * /E'+options, newLocation+u'\\'+tempArr[-1], system, wait, [scene, scenePos]])
            else:
                tempArr2=tempArr[:-1]
                stringliste = u"\\".join(tempArr2)
                if len(tempArr2)==1:
                    stringliste+=u"\\\\"
                    system=True
                #print u'"'+stringliste+u'" "'+newLocation+u'" "'+tempArr[-1]+u'"'+options
                self.browserRobocopyData.append([u'"'+stringliste+u'" "'+newLocation+u'" "'+tempArr[-1]+u'"'+options, newLocation, system, wait, [scene, scenePos]])
        if process:
            eg.plugins.System.Execute(u'robocopy.exe', self.browserRobocopyData[0][0], 3, False, 1, u'', True, False, u'browserCopy', True, True, True)
            
            
    def browserPaste2(self, event):
        try:
            if self.browserRobocopyData[0][3]:
                self.plugin.ServerExecute(u'self.sceneAction('+str(self.browserRobocopyData[0][4][0])+','+str(self.browserRobocopyData[0][4][1])+',True)')
        except:
            self.browserRobocopyData=[0]
        try:
            if self.browserRobocopyData[0][2]:
                eg.plugins.System.Execute(u'attrib.exe', u'-s -h /S /D "'+self.browserRobocopyData[0][1]+u'"', 3, True, 2, u'', False, False, u'', True, True, False)
        except:
            pass
        self.browserRobocopyData.pop(0)
        if len(self.browserRobocopyData)>0:
            eg.plugins.System.Execute(u'robocopy.exe', self.browserRobocopyData[0][0], 3, False, 1, u'', True, False, u'browserCopy', True, True, True)
            
            
    def browserNewLink(self, event):
        data=event.payload["data"]
        newLocation=data["location"]
        data=data["targets"]
        for i in data:
            tempArr=i[0].split("\\")
            #eg.plugins.System.Execute(u'cmd.exe', u'/C mklink "'+newLocation+'\\Link to '+tempArr[-1]+'" "'+i[0]+'"', 3, False, 3, u'', False, False, u'', True, True, False)
            self.plugin.createShortcut(newLocation+'\\Link to '+tempArr[-1]+'.lnk', i[0], newLocation, i[0])
#---------------------------------browserEnd-----------------------------------#
#===============================================================================
# EventActions End
#===============================================================================
# TCP Start
#===============================================================================
class RequestData(eg.ActionBase):
    name = "Request Data from a remote host"
    
    def __call__(self,destIP, destPort ,passwd , data):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.settimeout(5.0)
        
        sock.connect((destIP, destPort))
        sock.settimeout(180.0)
        # First wake up the server, for security reasons it does not
        # respond by it self it needs this string, why this odd word ?
        # well if someone is scanning ports "connect" would be very 
        # obvious this one you'd never guess :-) 

        sock.sendall("omegaismegacool\n\r")

        # The server now returns a cookie, the protocol works like the
        # APOP protocol. The server gives you a cookie you add :<password>
        # calculate the md5 digest out of this and send it back
        # if the digests match you are in.
        # We do this so that no one can listen in on our password exchange
        # much safer then plain text.

        cookie = sock.recv(128)		

        # Trim all enters and whitespaces off
        cookie = cookie.strip()

        # Combine the token <cookie>:<password>
        token = cookie + ":" + passwd

        # Calculate the digest
        digest = md5(token).hexdigest()

        # add the enters
        digest = digest + "\n"
                
        # Send it to the server		
        sock.sendall(digest)

        # Get the answer
        answer = sock.recv(512)

        # If the password was correct and you are allowed to connect
        # to the server, you'll get "accept"
        if (answer.strip() != "accept"):
            sock.close()
            return False
        elif (answer.strip("\n") == " accept"):
            sock.sendall("dataRequest %s\n" % json.dumps(data))
            count=0
            answer=""
            try :
                close=False
                while (answer.find("close\n")==-1) and count<1024:
                    tmp=sock.recv(512)
                    #print str(count)+tmp
                    answer+=tmp
                    count+=1
                close=(answer.find("close\n")>-1)
                answer=answer[:answer.find("\n")]
            except:
                pass
            try:
                if not close:sock.sendall("close\n")
            finally:
                sock.close()
            answer=answer.strip()
            if answer[:7]=="result ":
                try:
                    result=json.loads(answer[7:])
                except:
                    eg.PrintError("O-MEGA: Can not parse json object in the response from the server: " +answer+"; Returning False")
                    result=False
            else:
                eg.PrintError("O-MEGA: The server didn't send back a response. It might not be able to evaluate the request (" + data +"==>" + answer + ")")
                result=False
        else:
            eg.PrintError("O-MEGA: Received incompatible TCP data!")
            result=False
        return result
            

class TCPServerHandler(asynchat.async_chat):
    """Telnet engine class. Implements command line user interface."""
    
    def __init__(self, sock, addr, hex_md5, cookie, plugin):
        self.plugin = plugin
        
        # Call constructor of the parent class
        asynchat.async_chat.__init__(self, sock)

        # Set up input line terminator
        self.set_terminator('\n')

        # Initialize input data buffer
        self.data = ''
        self.state = self.state1
        self.ip = addr[0]
        self.payload = []
        self.hex_md5 = hex_md5
        self.cookie = cookie
                  
                
    def handle_close(self):
        #self.plugin.EndLastEvent()
        asynchat.async_chat.handle_close(self)
    
    
    def collect_incoming_data(self, data):
        """Put data read from socket to a buffer
        """
        # Collect data in input buffer
        self.data += data
    
    
    def found_terminator(self):
        """
        This method is called by asynchronous engine when it finds
        command terminator in the input stream
        """   
        # Take the complete line
        line = self.data

        # Reset input buffer
        self.data = ''

        #call state handler
        self.state(line)


    def initiate_close(self):
        try:
            self.push("close\n")
            self.close_when_done()
        except:
            eg.PrintError("O-MEGA: Error in TCPServerHandler.initiate_close (push/close_when_done)")
        #asynchat.async_chat.handle_close(self)
        #self.plugin.EndLastEvent()
        self.state = self.state1
        #try:
        #    print "close"
        #    self.close()
        #except:
        #    eg.PrintError("O-MEGA: Error in TCPServerHandler.initiate_close (close)")    
 

    def state1(self, line):
        """
        get keyword "omegaismegacool\n" and send cookie
        """
        if line == "omegaismegacool":
            self.state = self.state2
            self.push(self.cookie + "\n")
        else:
            self.initiate_close()
                
                
    def state2(self, line):
        """get md5 digest
        """
        line=line.strip()
        digest = line.strip()[-32:]
        if digest == "":
            pass
        elif digest.upper() == self.hex_md5:
            self.push(" accept\n")
            self.state = self.state3
        else:
            eg.PrintError("O-MEGA: TCP error, wrong password?")
            self.initiate_close()
            
            
    def state3(self, line):
        line = line.decode(eg.systemEncoding)
        if line == "close":
            self.initiate_close()
        elif line[:12]=="dataRequest " :
            dataRequest = line[12:]
            try:
                result=self.plugin.ExecuteString(json.loads(dataRequest))
                self.push("result ")
                try:
                    result=json.dumps(result)
                    count=0
                    while len(result)>count:
                        count2=count+512
                        if count2>len(result):
                            count2=len(result)
                        self.push(result[count:count2])
                        #print result[count:count2]
                        count=count2
                    self.push("\n")
                except:
                    self.push(json.dumps(None))
                    self.push("\n")
            except:
                result = None
            self.initiate_close()
            

class TCPServer(asyncore.dispatcher):
    
    def __init__ (self, port, password, plugin):
        self.plugin = plugin
        try:
            self.cookie = hex(random.randrange(65536))
            self.cookie = self.cookie[len(self.cookie) - 4:]
            self.hex_md5 = md5(self.cookie + ":" + password).hexdigest().upper()

            # Call parent class constructor explicitly
            asyncore.dispatcher.__init__(self)
        
            # Create socket of requested type
            self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        
            # restart the asyncore loop, so it notices the new socket
            eg.RestartAsyncore()
        
            # Set it to re-use address
            # self.set_reuse_addr()
            # self.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
            # Bind to all interfaces of this host at specified port
            self.bind(('', port))
            
            # Start listening for incoming requests
            #self.listen (1024)
            self.listen(5)
        except:
            eg.PrintError("O-MEGA: Error in TCP Server")

            
    def handle_accept (self):
        """Called by asyncore engine when new connection arrives"""
        # Accept new connection
        try:
            (sock, addr) = self.accept()
            TCPServerHandler(
                sock, 
                addr, 
                self.hex_md5, 
                self.cookie,
                self.plugin,
            )
        except:
            eg.PrintError("O-MEGA: Error in TCP handle accept")

#===============================================================================
# TCP End
#===============================================================================
# Explorer Main start
#===============================================================================
FO_DELETE = 3
FOF_ALLOWUNDO = 64
FOF_NOCONFIRMATION = 16
ERROR_ACCESS_DENIED  = 5
ERROR_NO_ASSOCIATION = 1155
FILE_ATTRIBUTE_READONLY = 1
FILE_ATTRIBUTE_HIDDEN = 2
FILE_ATTRIBUTE_SYSTEM = 4
BUFSIZE = 8192
folder_ID   = u"?dir?"
shortcut_ID = u"?lnk?"


def CaseInsensitiveSort(list):
    tmp = [(item[0].upper(), item) for item in list] # Schwartzian transform
    tmp.sort()
    return [item[1] for item in tmp]


def GetFolderItems(folder, patterns, hide=False):
    shortcut = pythoncom.CoCreateInstance (
      shell.CLSID_ShellLink,
      None,
      pythoncom.CLSCTX_INPROC_SERVER,
      shell.IID_IShellLink
    )
    persist_file = shortcut.QueryInterface (pythoncom.IID_IPersistFile)
    patterns = patterns.split(",")
    if folder != MY_COMPUTER:
        ds = []
        fs = []
        try:
            items = os.listdir(folder)
        except:
            return fs
        for f in items:
            path1 = os.path.join(folder, f)
            if os.path.isdir(path1):
                if hide:
                    attr = GetFileAttributesW(path1)
                    if attr & (FILE_ATTRIBUTE_HIDDEN | FILE_ATTRIBUTE_SYSTEM):
                        continue
                ds.append(("%s%s" % (folder_ID,f),""))
            elif os.path.isfile(path1):
                if os.path.splitext(f)[1].lower() == ".lnk":
                    persist_file.Load (path1)
                    path = shortcut.GetPath(shell.SLGP_RAWPATH)[0]
                    f = os.path.split(path1)[1][:-4]
                    if hide:
                        attr = GetFileAttributesW(path)
                        if attr & (FILE_ATTRIBUTE_HIDDEN | FILE_ATTRIBUTE_SYSTEM):
                            continue
                    if os.path.isdir(path):
                        if not "%s%s" % (folder_ID,f) in ds:
                            ds.append(("%s%s%s" % (shortcut_ID,folder_ID,f),path))
                            continue
                    elif os.path.isfile(path):
                        for p in patterns:
                            if fnmatch(os.path.split(path)[1],p.strip()):
                                if not shortcut_ID+f in fs:
                                    fs.append((shortcut_ID+f,path))
                                break
                else:
                    if hide:
                        attr = GetFileAttributesW(os.path.join(folder,f))
                        if attr & (FILE_ATTRIBUTE_HIDDEN | FILE_ATTRIBUTE_SYSTEM):
                            continue
                    for p in patterns:
                        if fnmatch(f,p.strip()):
                            if not f in fs:
                                fs.append((f,""))
                            break
        ds = CaseInsensitiveSort(ds)
        fs = CaseInsensitiveSort(fs)
        ds.extend(fs)
        return ds
    else: #pseudo-folder "My computer"
        #drives = GetLogicalDriveStrings().split('\000')[:-1]
        drives = []
        mask = 1
        ordA = ord('A')
        drivebits = GetLogicalDrives()
        for c in range(26):
            if drivebits & mask:
                drv = '%c:\\' % chr(ordA+c)
                if os.path.isdir(drv):
                    try:
                        name = GetVolumeInformation(drv)[0]
                        drives.append(("%s%s (%s)" % (
                            folder_ID,
                            name,
                            drv[:2]),
                            ""
                        ))
                    except:
                        pass
            mask = mask << 1
        return drives
        
        
class Menu():

    oldStart = ""
    watchThread = None

    def __init__(
        self,
        flag,
        plugin,
        prefix,
        start,
        patterns,
        hide,
        inst,
        scan
        ):

        self.plugin  = plugin
        self.plugin.menuDlg[inst] = self
        self.goBackList = []

        self.flag     = flag
        self.patterns = patterns
        self.hide     = hide
        self.inst     = inst
        self.scan     = scan

        self.ShowMenu(prefix, start, False, False)


    def ShowMenu(
        self,
        prefix,
        start,
        goBack,
        isReload=False,
    ):
        
        if goBack:
            self.goBackList.pop()
            start = self.goBackList.pop()
        self.prefix = prefix
        self.start = start
        try:
            items  = GetFolderItems(start, self.patterns, self.hide)
        except:
            pythoncom.CoInitialize()
            items  = GetFolderItems(self.start, self.patterns, self.hide)
            pythoncom.CoUninitialize()
        if not isReload:
            self.goBackList.append(self.start)
            if len(self.goBackList) >= 4:
                if self.goBackList[-2:] == self.goBackList[-4:-2]:
                    self.goBackList.pop()
                    self.goBackList.pop()
        self.choices = [item[0] for item in items]
        self.shortcuts = [item[1] for item in items]

        head, tail = os.path.split(self.oldStart)
        if start != MY_COMPUTER:
            items = self.choices
            if self.scan:
                self.watchIt(start)
            itm = folder_ID + tail if head == start else "#"
        else:
            items = [itm[-3:-1] for itm in self.choices]
            itm = self.oldStart[:2]
        itm = items.index(itm) if itm in items else 0
        self.oldStart = start
        self.selectedRow = 0
        
        
    def GetInfo(self,sel):
        sel = self.GoToPos(sel)
        fp = unicode(self.shortcuts[sel].decode(eg.systemEncoding))
        if not fp:
            fp = os.path.join(self.start,self.choices[sel])
        return fp, self.prefix


    def GetItemsFolder(self, fp):
        return GetFolderItems(fp, self.patterns, self.hide)


    def GoToPos(self, sel):
        if len(self.choices) <= sel:
            sel=0
        return sel
            
            
    def GoToParent(self):
        if self.start != MY_COMPUTER:
            strt = MY_COMPUTER if len(self.start) == 3 else os.path.split(self.start)[0]
            self.ShowMenu(
                self.prefix,
                strt,
                False,
                False,
            )
            return True


    def GoBack(self):
        if len(self.goBackList) >= 1:
            self.ShowMenu(
                self.prefix,
                None,
                True,
                False,
            )
            return True


    def GetFilePath(self,sel):
        sel = self.GoToPos(sel)
        filePath = unicode(self.shortcuts[sel].decode(eg.systemEncoding))
        if not filePath:
            filePath = os.path.join(self.start,self.choices[sel])
            filePath = filePath.replace(folder_ID,"")
            if filePath[-2] == ":": #root of drive
                filePath = filePath[-3:-1]+"\\"
            if filePath[-3:] == r"\..":
                if len(filePath) == 5:
                    filePath = MY_COMPUTER
                else:
                    filePath = os.path.split(filePath[:-3])[0]
        return sel, filePath
        
        
    def GetPath(self):
        filePath = os.path.join(self.start)
        filePath = filePath.replace(folder_ID,"")
        if filePath[-2] == ":": #root of drive
            filePath = filePath[-3:-1]+"\\"
        if filePath[-3:] == r"\..":
            if len(filePath) == 5:
                filePath = MY_COMPUTER
            else:
                filePath = os.path.split(filePath[:-3])[0]
        return filePath
        

    def GetValue(self, target):
        if isinstance(target, int):
            sel, filePath = self.GetFilePath(target)
            choosen = self.choices[sel]
        else:
            filePath = target
            choosen = filePath.split("\\")[-1]
        return [choosen, filePath]
        
        
    def GetProperties(self, target, what):
        if isinstance(target, int):
            sel, filePath = self.GetFilePath(target)
        else:
            filePath = target
        statinfo=os.stat(filePath)
        if what==0:
            if os.path.isfile(filePath):
                return [statinfo.st_size,1,0]
            else:
                inst = None
                x=0
                while x < len(self.plugin.instances):
                    if self.plugin.instances[x] == False:
                        self.plugin.instances[x] = True
                        inst=x
                        x=len(self.plugin.instances)
                    x+=1
                if inst == None:
                    inst=len(self.plugin.instances)
                    self.plugin.instances.append(True)
                Menu(
                    False,
                    self.plugin,
                    self.prefix,
                    filePath,
                    '*',
                    False,
                    inst,
                    False
                )
                size, filesCount, folderCount = self.plugin.menuDlg[inst].GetFolderSize()
                self.plugin.menuDlg[inst] = None
                self.plugin.instances[inst] = False
                return [size,filesCount,folderCount]
        elif what==1:
            return time.strftime("%d;%m;%Y;%H;%M;%S", time.localtime(statinfo.st_ctime)).split(";")
        elif what==2:
            return time.strftime("%d;%m;%Y;%H;%M;%S", time.localtime(statinfo.st_mtime)).split(";")
        elif what==3:
            return time.strftime("%d;%m;%Y;%H;%M;%S", time.localtime(statinfo.st_atime)).split(";")
        else:
            return GetFileAttributesW(filePath)
        
        
    def GetFolderSize(self):
        size=0
        filesCount=0
        folderCount=0
        filePathArr=[]
        i=0
        while i < len(self.choices):
            fp = self.GetFilePath(i)[1]
            if self.choices[i].find(shortcut_ID)==-1:
                filePathArr.append(fp)
            else:
                filesCount += 1
            i+=1
        for tmpPath in filePathArr:
            if os.path.isfile(tmpPath):
                filesCount += 1
                size += os.lstat(tmpPath).st_size
            else:
                folderCount += 1
                for dirpath, dirnames, filenames in os.walk(tmpPath):
                    for f in filenames:
                        filesCount+=1
                        fp = os.path.join(dirpath, f)
                        size += os.lstat(fp).st_size
                    for d in dirnames:
                        folderCount+=1
        return [size, filesCount, folderCount]
        
        
    def watchIt(self, path):
        self.watchStop()
        self.stopWatchEvent = CreateEvent(None, 1, 0, None)
        self.stopWatchThreadEvent = Event()
        self.watchThread = Thread(
            target=self.watch,
            args=(self.stopWatchThreadEvent,path, )
        )
        self.watchThread.start()


    def watchStop(self):
        if self.watchThread is not None:
            self.stopWatchThreadEvent.set()
            PulseEvent(self.stopWatchEvent)


    def watch(self, stopWatchThreadEvent, path):
        hDir = CreateFile(
            path,
            FILE_LIST_DIRECTORY,
            FILE_SHARE_READ|FILE_SHARE_WRITE,
            None,
            OPEN_EXISTING,
            FILE_FLAG_BACKUP_SEMANTICS|FILE_FLAG_OVERLAPPED,
            0
        )
        if hDir == INVALID_HANDLE_VALUE:
            self.stopWatchThreadEvent.set()
            return
        overlapped = OVERLAPPED()
        overlapped.hEvent = CreateEvent(None, 1, 0, None)
        buffer = (c_byte * BUFSIZE )()
        events = (HANDLE * 2)(overlapped.hEvent, self.stopWatchEvent)
        flags = (
            FILE_NOTIFY_CHANGE_FILE_NAME |
            FILE_NOTIFY_CHANGE_DIR_NAME
        )
        includeSubdirs = False
        bytesReturned = DWORD()
        noneCallback = cast(None, LPOVERLAPPED_COMPLETION_ROUTINE)
        
        while not stopWatchThreadEvent.isSet():
            ReadDirectoryChangesW(
                hDir,
                buffer,
                BUFSIZE,
                includeSubdirs,
                flags,
                byref(bytesReturned),
                byref(overlapped),
                noneCallback
            )
            rc = MsgWaitForMultipleObjects(
                2, events, 0, INFINITE, QS_ALLINPUT
            )
            if rc == WAIT_OBJECT_0:
                self.plugin.updateBrowserDataState(self.plugin.thisPc,self.inst+1,"newData",1)
            elif rc == WAIT_OBJECT_0+1:
                break
        CloseHandle(hDir)

#===============================================================================
# Explorer Main end
#===============================================================================
# Explorer Actions Start
#===============================================================================

class StartMenu(eg.ActionBase):

    def __call__(
        self,
        prefix = "O-MEGA", #Event prefix
        start = "", #Folder
        patterns = "*.*", #Here you can enter the patterns of required files, separated by commas. For example, *.mp3, *.ogg, *.flac or e*.ppt, g*.ppt and the like.
        hide = True, #Do not display system and hidden files and folders
        inst = None, #Target instance ID
        newInst = False, #If an instance is specified and this is true, the instance will be replaced, otherwise the instance will just be used
        scan = True, #If a new instance is created, and this is false, the actual folder will not be monitored for changes in this instance
    ):
        if not start:
            start = MY_COMPUTER
        if start != MY_COMPUTER:
            while not os.path.isdir(start):
                if len(start) == 3:
                    start = MY_COMPUTER
                    break
                start = os.path.split(start)[0]
        if inst == None:
            x=0
            while x < len(self.plugin.instances):
                if self.plugin.instances[x] == False:
                    self.plugin.instances[x] = True
                    inst=x
                    break
                x+=1
            if inst == None:
                inst=x
                self.plugin.instances.append(True)
            Menu(
                False,
                self.plugin,
                prefix,
                start,
                patterns,
                hide,
                inst,
                scan
            )
            inst+=1
            #eg.TriggerEvent(prefix = prefix, suffix ="New browser instance created:" , payload = inst)
            return inst
        else:
            inst-=1
            if newInst:
                self.plugin.menuDlg[inst].watchStop()
                Menu(
                    False,
                    self.plugin,
                    prefix,
                    start,
                    patterns,
                    hide,
                    inst,
                    scan
                )
            else:
                self.plugin.menuDlg[inst].ShowMenu(
                    prefix,
                    start,
                    False,
                    False,
                )
            return True
        
#===============================================================================

class Cancel(eg.ActionBase):
    
    class text:
        inst = "Instance Number:"
        
        
    def __call__(self, inst = 1):
        inst-=1
        if self.plugin.menuDlg[inst]:
            prefix = self.plugin.menuDlg[inst].prefix
            self.plugin.menuDlg[inst].watchStop()
            self.plugin.menuDlg[inst] = None
            self.plugin.instances[inst] = False
            #eg.TriggerEvent(prefix = prefix, suffix ="Browser instance destroid:" , payload = (inst+1))
            return True
            
#===============================================================================

class GoToParent(Cancel):
        
    def __call__(self, inst = 1):
        inst-=1
        if self.plugin.menuDlg[inst]:
            return self.plugin.menuDlg[inst].GoToParent()
#===============================================================================

class GoBack(Cancel):

    def __call__(self, inst = 1):
        inst-=1
        if self.plugin.menuDlg[inst]:
            return self.plugin.menuDlg[inst].GoBack()
#===============================================================================

class GetValue(eg.ActionBase):

    def __call__(self, val = 3, inst = 1, target = 0, rel = False):
        inst-=1
        if self.plugin.menuDlg[inst]:
            if rel==True:
              prefix= self.plugin.menuDlg[inst].prefix
              filePath= self.plugin.menuDlg[inst].GetPath()
              self.plugin.menuDlg[inst].ShowMenu(
                  prefix,
                  filePath,
                  False,
                  rel,
              )
            if val < 2:#0:Item string,1:Absolute path
                return self.plugin.menuDlg[inst].GetValue(target)[val]
            elif val==2:#2:[Item string, Absolute path]
                return self.plugin.menuDlg[inst].GetValue(target)
            elif val==3:#3:[All item strings in this folder]
                return self.plugin.menuDlg[inst].choices
            elif val==4:#4:Absolute path (without the selected item)
                return self.plugin.menuDlg[inst].GetPath()
            elif val==5:#5:Size in byte
                return self.plugin.menuDlg[inst].GetProperties(target,0)[0]
            elif val==6:#6:[Number of files, Number of folders]
                return self.plugin.menuDlg[inst].GetProperties(target,0)[1:]
            elif val==7:#7:[Size in byte, Number of files, Number of folders]
                return self.plugin.menuDlg[inst].GetProperties(target,0)
            elif val==8:#8:[Creation date and time]
                return self.plugin.menuDlg[inst].GetProperties(target,1)
            elif val==9:#9:[Modification date and time]
                return self.plugin.menuDlg[inst].GetProperties(target,2)
            elif val==10:#10:[Access date and time]
                return self.plugin.menuDlg[inst].GetProperties(target,3)
            elif val==11:#11:File attributes
                return self.plugin.menuDlg[inst].GetProperties(target,4)
            else:#12:Absolute path(don't follow links)
                path = self.plugin.menuDlg[inst].GetPath()
                name = self.plugin.menuDlg[inst].choices[target]
                name = name.replace(folder_ID,"")
                if name.find(shortcut_ID)!=-1:
                    name = name.replace(shortcut_ID,"")
                    name += ".lnk"
                return os.path.join(path, name)

#===============================================================================

class Execute(eg.ActionBase):

    def __call__(self, val = 22, fileSuff = "", folderSuff = "", inst = 1, target = 0):
        inst-=1
        if self.plugin.menuDlg[inst]:
            filePath, prefix = self.plugin.menuDlg[inst].GetInfo(target)
            filePath = filePath.replace(folder_ID,"")
            if filePath[-2] == ":": #root of drive
                filePath = filePath[-3:-1]+"\\"
            if os.path.isfile(filePath):
                if val&1: #trigger event
                    if fileSuff:
                        suffix = fileSuff
                    else:
                        suffix = "file"
                    eg.TriggerEvent(prefix = prefix, suffix = suffix, payload = filePath)
                if val&2: #open in associated
                    try:
                        os.startfile(filePath)
                    except WindowsError, e:
                        if e.winerror == ERROR_NO_ASSOCIATION:
                            eg.PrintError(self.plugin.text.noAssoc % os.path.splitext(filePath)[1])
                        else:
                            raise
                if val&256: #delete file
                    if GetFileAttributesW(filePath) & FILE_ATTRIBUTE_READONLY:
                        eg.PrintError(self.plugin.text.accDeni % filePath)
                    else:
                        try:
                            shell.SHFileOperation((0, FO_DELETE, filePath, None,
                            FOF_ALLOWUNDO|FOF_NOCONFIRMATION))
                        except WindowsError, e:
                            if e.winerror == ERROR_ACCESS_DENIED:
                                eg.PrintError(self.plugin.text.accDeni % filePath)
                            else:
                                raise
                if val&4: #return
                    return filePath
            elif os.path.isdir(filePath):
                if filePath[-3:] == r"\..":
                    if len(filePath) == 5:
                        filePath = MY_COMPUTER
                    else:
                        filePath = os.path.split(filePath[:-3])[0]
                if val&(64+128):
                    items = self.plugin.menuDlg[inst].GetItemsFolder(filePath)
                    fpList = []
                    for sel in xrange(len(items)):
                        fp = unicode(items[sel][1].decode(eg.systemEncoding))
                        if not fp:
                            fp = items[sel][0]

                            fp = fp.replace(folder_ID,"")
                            fp = os.path.join(filePath, fp)
                            if fp[-2] == ":": #root of drive
                                fp = fp[-3:-1]+"\\"
                        if os.path.isfile(fp):
                            fpList.append(fp)
                if folderSuff:
                    suffix = folderSuff
                else:
                    suffix = "folder"
                if val&8: #trigger event
                    eg.TriggerEvent(prefix = prefix, suffix = suffix, payload = filePath)
                if val&64:
                    eg.TriggerEvent(prefix = prefix, suffix = suffix, payload = fpList)
                if val&512: #delete file
                    if GetFileAttributesW(filePath) & FILE_ATTRIBUTE_READONLY:
                        eg.PrintError(self.plugin.text.accDeni % filePath)
                    else:
                        try:
                            shell.SHFileOperation((0, FO_DELETE, filePath, None,
                            FOF_ALLOWUNDO|FOF_NOCONFIRMATION))
                        except WindowsError, e:
                            if e.winerror == ERROR_ACCESS_DENIED:
                                eg.PrintError(self.plugin.text.accDeni % filePath)
                            else:
                                raise
                if val&16: #go to the folder
                    self.plugin.menuDlg[inst].ShowMenu(
                        prefix,
                        filePath,
                        False,
                        False,
                    )
                else:
                    self.plugin.menuDlg[inst] = None
                res = None
                if val&32: #return
                    res = filePath
                elif val&128: #return
                    res = fpList
                if res:
                    return res
        elif val&(4+32+128):
            eg.programCounter = None

#===============================================================================
# Explorer Actions End
#===============================================================================
#===============================================================================
# Webserver Start
#===============================================================================
class FileLoader(BaseLoader):
    """Loads templates from the file system."""

    def get_source(self, environment, filename):
        try:
            sourceFile = open(filename, "rb")
        except IOError:
            raise TemplateNotFound(filename)
        try:
            contents = sourceFile.read().decode("utf-8")
        finally:
            sourceFile.close()

        mtime = os.path.getmtime(filename)
        def uptodate():
            try:
                return os.path.getmtime(filename) == mtime
            except OSError:
                return False
        return contents, filename, uptodate


class MyServer(ThreadingMixIn, HTTPServer):
    address_family = getattr(socket, 'AF_INET6', None)

    def __init__(self, requestHandler, port, certfile, keyfile):
        self.httpdThread = None
        self.abort = False
        for res in socket.getaddrinfo(None, port, socket.AF_UNSPEC,
                              socket.SOCK_STREAM, 0, socket.AI_PASSIVE):
            self.address_family = res[0]
            self.socket_type = res[1]
            address = res[4]
            break

        HTTPServer.__init__(self, address, requestHandler)
        if os.path.isfile(certfile) and os.path.isfile(keyfile):
            self.socket = wrap_socket(
                self.socket,
                certfile = certfile,
                keyfile = keyfile,
                server_side = True
            )


    def server_bind(self):
        """Called by constructor to bind the socket."""
        if socket.has_ipv6 and eg.WindowsVersion >= 'Vista':
            # make it a dual-stack socket if OS is Vista/Win7
            IPPROTO_IPV6 = 41
            self.socket.setsockopt(IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
        HTTPServer.server_bind(self)


    def Start(self):
        """Starts the HTTP server thread"""
        self.httpdThread = Thread(name="WebserverThread", target = self.Run)
        self.httpdThread.start()


    def Run(self):
        try:
            # Handle one request at a time until stopped
            while not self.abort:
                self.handle_request()
        finally:
            self.httpdThread = None


    def Stop(self):
        """Stops the HTTP server thread"""
        if self.httpdThread:
            self.abort = True
            # closing the socket will awake the underlying select.select() call
            # so the handle_request() loop will notice the abort flag
            # immediately
            self.socket.close()
            self.RequestHandlerClass.repeatTimer.Stop()
#===============================================================================

class MyHTTPRequestHandler(SimpleHTTPRequestHandler):
    extensions_map = SimpleHTTPRequestHandler.extensions_map.copy()
    extensions_map['.ico'] = 'image/x-icon'
    extensions_map['.svg'] = 'image/svg+xml'
    extensions_map['.manifest'] = 'text/cache-manifest'
    clAddr = None
    magic = '258EAFA5-E914-47DA-95CA-C5AB0DC85B11'
    # these class attributes will be set by the plugin:
    authString = None
    authRealm = None
    basepath = None
    repeatTimer = None
    environment = None
    plugin = None
    
    def getClientAddress(self):
        ip = self.client_address
        return (ip[0].replace('::ffff:', ''), ip[1])


    def send_close(self):
        msg = bytearray()
        msg.append(0x88)
        msg.append(0x00)
        try:
            self.request.send(msg)
        except:
            pass


    """def handle_one_request(self):
        try:
            SimpleHTTPRequestHandler.handle_one_request(self)
        except Exception, exc:
            eg.PrintError(
                "Webserver: Exception on handle_one_request:",
                unicode(exc)
            )"""


    def version_string(self):
        """Return the server software version string."""
        return "EventGhost/" + eg.Version.string


    def Authenticate(self):
        # only authenticate, if set
        if self.authString is None:
            return True

        # do Basic HTTP-Authentication
        authHeader = self.headers.get('authorization')
        if authHeader is not None:
            authType, authString = authHeader.split(' ', 2)
            if authType.lower() == 'basic' and authString == self.authString:
                return True

        self.send_response(401)
        self.send_header('WWW-Authenticate','Basic realm="%s"' % self.authRealm)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        return False


    def SendContent(self, path):
        fsPath = self.translate_path(path)
        if os.path.isdir(fsPath):
            if not path.endswith('/'):
                # redirect browser - doing basically what apache does
                self.send_response(301)
                self.send_header("Location", path + "/")
                self.end_headers()
                return None
            for index in ("index.html", "index.htm"):
                index = os.path.join(fsPath, index)
                if os.path.exists(index):
                    fsPath = index
                    break
            else:
                return self.list_directory(path)
        #extension = splitext(fsPath)[1].lower()
        #if extension not in (".htm", ".html"):
        f = self.send_head()
        if f:
            self.wfile.write(f.read())
            f.close()
        return
        #try:
        #    template = self.environment.get_template(fsPath)
        #except TemplateNotFound:
        #    self.send_error(404, "File not found")
        #    return
        #content = template.render({})
        #self.end_request(content)


    def end_request(self, content, case = 'text/html'):
        content=content.encode("UTF-8")
        self.send_response(200)
        self.send_header("Content-type", case)
        self.send_header("Content-Length", len(content))
        self.end_headers()
        self.wfile.write(content)
        #self.wfile.close()


    def do_POST(self):
        """Serve a POST request."""
        # First do Basic HTTP-Authentication, if set
        if not self.Authenticate():
            return
        self.clAddr = self.getClientAddress()
        contentLength = int(self.headers.get('content-length'))
        content = self.rfile.read(contentLength)
        plugin = self.plugin
        try:
            data = json.loads(content)
        except:
            if content=="request":
                self.SendContent(self.path)
            else:
                data=content.split("&")
                eg.TriggerEvent(prefix="O-HTTP",suffix=data[0],payload=data[1:])
        else:
            methodName = data["method"]
            args = data.get("args", [])
            kwargs = data.get("kwargs", {})
            targetpc = data.get("targetpc", "")
            result = self.plugin.ProcessTheArguments(
                self,
                methodName,
                args,
                kwargs,
                targetpc
            )
            content = json.dumps(result)
            self.end_request(content, 'application/json; charset=UTF-8')


    def do_GET(self):
        """Serve a GET request."""
        self.clAddr = self.getClientAddress()
        # First do Basic HTTP-Authentication, if set
        if not self.Authenticate():
            return
        path, dummy, remaining = self.path.partition("?")
        if remaining:
            queries = remaining.split("#", 1)[0].split("&")
            queries = [unquote_plus(part).decode("utf-8") for part in queries]
            if len(queries) > 0:
                event = queries.pop(0).strip()
                if "withoutRelease" in queries:
                    queries.remove("withoutRelease")
                    event = self.plugin.TriggerEnduringEvent(event, queries)
                    while not event.isEnded:
                        time.sleep(0.05)
                elif event == "ButtonReleased":
                    self.plugin.EndLastEvent()
                else:
                    event = eg.TriggerEvent(prefix="O-HTTP", suffix=event, payload=queries)
                    while not event.isEnded:
                        time.sleep(0.05)
        try:
            self.SendContent(path)
        except Exception, exc:
            self.plugin.EndLastEvent()
            eg.PrintError("Webserver error", self.path)
            eg.PrintError("Exception", unicode(exc))
            if exc.args[0] == 10053: # Software caused connection abort
                pass
            elif exc.args[0] == 10054: # Connection reset by peer
                pass
            else:
                raise


    def log_message(self, format, *args):
        pass


    def copyfile(self, src, dst):
        dst.write(src.read())


    def translate_path(self, path):
        """Translate a /-separated PATH to the local filename syntax.

        Components that mean special things to the local file system
        (e.g. drive or directory names) are ignored.  (XXX They should
        probably be diagnosed.)

        """
        # stolen from SimpleHTTPServer.SimpleHTTPRequestHandler
        # but changed to handle files from a defined basepath instead
        # of os.getcwd()
        path = path.split('?', 1)[0]
        path = path.split('#', 1)[0]
        path = normpath(unquote(path))
        words = [word for word in path.split('/') if word]
        path = self.basepath
        for word in words:
            drive, word = os.path.splitdrive(word)
            head, word = os.path.split(word)
            if word in (os.curdir, os.pardir):
                continue
            path = os.path.join(path, word)
        return path
        
        
class SendEventExt(eg.ActionBase):

    class text:
        url = "URL:"
        event = "Event:"
        username = "Username:"
        password = "Password:"
        msg1 = "This page isn't protected by basic authentication."
        msg2 = 'But we failed for another reason.'
        msg3 = 'A 401 error without an authentication response header - very weird.'
        msg4 = 'The authentication line is badly formed.'
        msg5 = 'SendEventExt only works with BASIC authentication.'
        msg6 = "url, username or password is wrong."

    def __call__(self, event="", host="", user="", password=""):
        text = self.text
        if event!="":
            req = urlRequest(host, event)
        else:
            req = urlRequest(host)
        try:
            handle = urlopen(req, timeout=60)
        except IOError, e:
            # If we fail then the page could be protected
            if not hasattr(e, 'code') or e.code != 401:
                # we got an error - but not a 401 error
                #print text.msg1
                #print text.msg2
                eg.PrintError("Webserver: Error " + str(e.code if hasattr(e, "code") else e))
                return None
            authline = e.headers.get('www-authenticate', '')
            # this gets the www-authenticat line from the headers - which has the authentication scheme and realm in it
            if not authline:
                eg.PrintError("Webserver: " + text.msg3)
                return None
            authobj = re.compile(r'''(?:\s*www-authenticate\s*:)?\s*(\w*)\s+realm=['"](\w+)['"]''', re.IGNORECASE)
            # this regular expression is used to extract scheme and realm
            matchobj = authobj.match(authline)
            if not matchobj:
                # if the authline isn't matched by the regular expression then something is wrong
                eg.PrintError("Webserver: " + text.msg4)
                #authheader=b'Basic ' + b64encode(user + b':' + password)
                return None
            scheme = matchobj.group(1)
            realm = matchobj.group(2)
            if scheme.lower() != 'basic':
                eg.PrintError("Webserver: " + text.msg5)
                return None
            base64string = b64_encStr('%s:%s' % (user, password))[:-1]
            authheader =  "Basic %s" % base64string
            req.add_header("Authorization", authheader)
            try:
                handle = urlopen(req, timeout=60)
            except IOError, e:
                eg.PrintError("Webserver: Error " + str(e.code if hasattr(e, "code") else e) + ": " + text.msg6)
                return None
        thepage = unquote(handle.read()) # handle.read()
        return thepage


    def Configure(self, event="", host="http://127.0.0.1:80", user="", password=""):
        text = self.text
        panel = eg.ConfigPanel(self)
        eventCtrl = panel.TextCtrl(event)
        hostCtrl = panel.TextCtrl(host)
        userCtrl = panel.TextCtrl(user)
        passwordCtrl = panel.TextCtrl(password)
        fl = wx.EXPAND|wx.TOP
        box=wx.GridBagSizer(2, 5)
        box.Add(panel.StaticText(text.event), (0, 0), flag = wx.TOP, border=12)
        box.Add(eventCtrl, (0, 1), flag = fl, border=9)
        box.Add(panel.StaticText(text.url), (2, 0), flag = wx.TOP, border=12)
        box.Add(hostCtrl, (2, 1), flag = fl, border=9)
        box.Add(panel.StaticText(text.username), (4, 0), flag=wx.TOP, border=12)
        box.Add(userCtrl, (4, 1), flag = fl, border=9)
        box.Add(panel.StaticText(text.password), (5, 0), flag=wx.TOP, border=12)
        box.Add(passwordCtrl, (5, 1), flag = fl, border=9)
        box.AddGrowableCol(1)
        panel.sizer.Add(box, 0, wx.EXPAND|wx.LEFT|wx.RIGHT, 10)
        while panel.Affirmed():
            panel.SetResult(
                eventCtrl.GetValue(),
                hostCtrl.GetValue(),
                userCtrl.GetValue(),
                passwordCtrl.GetValue(),
            )
            
            
class RegisterWebFunction(eg.ActionBase):

    class text:
        function = "Function:"
        alias = "Alias:"

    def __call__(self, function="", alias=""):
        if isinstance(function, basestring):
            function=eg.ParseString(function)
            function=eval(function)
        return self.plugin.RegisterWebFunction(function,alias)


    def Configure(self, function="", alias=""):
        text = self.text
        panel = eg.ConfigPanel(self)
        functionCtrl = panel.TextCtrl(function)
        aliasCtrl = panel.TextCtrl(alias)
        fl = wx.EXPAND|wx.TOP
        box=wx.GridBagSizer(2, 2)
        box.Add(panel.StaticText(text.function), (0, 0), flag = wx.TOP, border=12)
        box.Add(functionCtrl, (0, 1), flag = fl, border=9)
        box.Add(panel.StaticText(text.alias), (1, 0), flag = wx.TOP, border=12)
        box.Add(aliasCtrl, (1, 1), flag = fl, border=9)
        box.AddGrowableCol(1)
        panel.sizer.Add(box, 0, wx.EXPAND|wx.LEFT|wx.RIGHT, 10)
        while panel.Affirmed():
            panel.SetResult(
                functionCtrl.GetValue(),
                aliasCtrl.GetValue(),
            )
            
            
class UnregisterWebFunction(eg.ActionBase):

    class text:
        alias = "Alias:"

    def __call__(self, alias=""):
        return self.plugin.UnregisterWebFunction(alias)


    def Configure(self, alias=""):
        text = self.text
        panel = eg.ConfigPanel(self)
        aliasCtrl = panel.TextCtrl(alias)
        fl = wx.EXPAND|wx.TOP
        box=wx.GridBagSizer(2, 1)
        box.Add(panel.StaticText(text.alias), (0, 0), flag = wx.TOP, border=12)
        box.Add(aliasCtrl, (0, 1), flag = fl, border=9)
        box.AddGrowableCol(1)
        panel.sizer.Add(box, 0, wx.EXPAND|wx.LEFT|wx.RIGHT, 10)
        while panel.Affirmed():
            panel.SetResult(
                aliasCtrl.GetValue(),
            )
#===============================================================================
# Webserver End
#===============================================================================