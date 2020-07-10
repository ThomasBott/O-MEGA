# -*- coding: cp1252 -*-
import os
import zipfile
import xml.etree.ElementTree as ET
import _winreg
import wx
import datetime
import shutil
import json
import tempfile
import psutil
from time import sleep

#lib
LIB_VERSION=1.16

SYSTEM_TEMPLATES=["winpc","winpcbrowser","winpcbrowser2","winpcmousekeyboard","default1","default2","defaultMenu1","defaultMenu2","changeUser","guiSettings","executeCommand","configuration"]
SYSTEM_EXTENSIONS=["PC_WIN","Ping","Generic_Prog","Pseudo_Device"]
REG_PATH = r'Software\EventGhost\O-MEGA'

class Template():
    def __init__(self, name, version, parent, json, extension, html):
        self.name = name
        self.version = version
        self.parent = parent
        self.json = json
        self.extension = extension
        self.html = html
    def __str__(self):
        return self.name+" - "+self.version

class Extension():
    def __init__(self, name, version, json):
        self.name = name
        self.version = version
        self.json = json
    def __str__(self):
        return self.name+" - "+self.version


def msgBox(title,text,mode="normal"):
    if mode=="error":
      dlg = wx.MessageDialog(None, text, title, wx.ICON_ERROR)
    else:
      dlg = wx.MessageDialog(None, text, title, wx.OK)
    dlg.ShowModal()
    dlg.Destroy()


def askYesNo(title, question):
    dlg = wx.MessageDialog(None, question, title, wx.YES_NO)
    ret = dlg.ShowModal()
    dlg.Destroy()
    if ret == 5103:
        return True
    else:
        return False

		
def searchForXmlRecursive(name, root):
    for folder in root.findall("Folder"):
        #print folder.get("Name")
        if folder.get("Name") == name:
            return folder
        else:
            result = searchForXmlRecursive(name, folder)
            if result:
                return result
    return None
    
    
def saveToReg(name, val):
    try:
        key = _winreg.OpenKey(_winreg.HKEY_CURRENT_USER, REG_PATH, 0, _winreg.KEY_ALL_ACCESS)
    except:
        key = _winreg.CreateKey(_winreg.HKEY_CURRENT_USER, REG_PATH)
    _winreg.SetValueEx(key, name, 0, _winreg.REG_SZ, val)
    _winreg.CloseKey(key)
    return True


def readFromReg(name):
    try:
        key = _winreg.OpenKey(_winreg.HKEY_CURRENT_USER, REG_PATH, 0, _winreg.KEY_ALL_ACCESS)
        try:
            val = _winreg.QueryValueEx(key, name)[0]
        except:
            val = ""
        _winreg.CloseKey(key)
        return val
    except:
        return ""


def getOmegaHome():
    return readFromReg("configDir")

def getSchedulghostXml():
    return readFromReg("SchedulGhostXMLPath")

def getEventghostXml():
    return readFromReg("xmlpath")


def zipdir(path, zip):
    for root, dirs, files in os.walk(path):
        for file in files:
            zipentry = os.path.join(root.replace(unicode(path), u"").strip("\\"), file)
            #print zipentry
            zip.write(os.path.join(root, file), zipentry)
    #print "END DEBUG"
	
def makeBackup():
    #get time
    timestamp = datetime.datetime.now()
    timestring = datetime.datetime.strftime(timestamp,"%Y-%m-%d_%H-%M-%S")
    #backup omega web folder
    backupfile = getOmegaHome() + "\\backups\\O-Backup_"+timestring+".zip"
    backupdir = getOmegaHome() + "\\backups"
    backupsrc = getOmegaHome() + "\\web"
    if os.path.exists(backupsrc):
        #backup eventghost xml
        shutil.copyfile(getEventghostXml(), backupsrc+"\\EG.xml")
        #backup schedulghost xml
        shutil.copyfile(getSchedulghostXml(), backupsrc+"\\SG.xml")
        try:
            os.makedirs(backupdir)
        except OSError:
            pass
        if os.path.exists(backupfile):
            os.remove(backupfile)
        zipf = zipfile.ZipFile(backupfile, 'w')
        zipdir(backupsrc, zipf)
        zipf.close()
        #remove eg.xml in web
        try:
            os.remove(backupsrc+"\\EG.xml")
        except OSError:
            msgBox("ERROR","Could not delete "+backupsrc+"\\EG.xml!","error")
        #remove sg.xml in web
        try:
            os.remove(backupsrc+"\\SG.xml")
        except OSError:
            msgBox("ERROR","Could not delete "+backupsrc+"\\SG.xml!","error")
    else:
        msgBox("ERROR","Could not create a backup! No sources found.","error")
        return False
    return True
            
def cleanBackup(maxAgeInDays):
    timestamp = datetime.datetime.now()
    backupdir = getOmegaHome() + "\\backups"
    oldBackups = os.listdir(backupdir)
    deleted = []
    for file in oldBackups:
        filePath = os.path.join(backupdir,file)
        fileParts = file.split("_")
        if os.path.isfile(filePath) and len(fileParts)==3:
            oldTimeData=fileParts[1]
            oldTimestamp=datetime.datetime.strptime(oldTimeData,"%Y-%m-%d")
            delta=timestamp-oldTimestamp
            if delta.days>maxAgeInDays:
                try:
                    os.remove(filePath)
                    deleted.append("Deleted "+file)
                except OSError:
                    deleted.append("ERROR Could not delete "+file)
    return deleted
		
def getInstalledTemplates():
    omegaLocation = getOmegaHome()
    templatesCfgFile = file(omegaLocation+"\\web\\config\\templatesCfg.json")
    jsonObj = json.load(templatesCfgFile)
    templateList = []
    for entry in jsonObj:
        templateList.append(Template(entry[0], entry[1], entry[2], entry, entry[3], entry[4]))
    return templateList

def getInstalledExtensions():
    omegaLocation = getOmegaHome()
    extensionsCfgFile = file(omegaLocation+"\\web\\config\\extensionsCfg.json")
    jsonObj = json.load(extensionsCfgFile)
    extensionList = []
    for entry in jsonObj:
        extensionList.append(Extension(entry[0], entry[1], entry))
    return extensionList

def getInstalledExtensionsWithoutSystemExtensions():
    extensionList = getInstalledExtensions()
    filteredList = []
    filteredList[:] = [x for x in extensionList if  x.name not in SYSTEM_EXTENSIONS]
    return filteredList
    
def getInstalledTemplatesWithoutParent():
    templateList = getInstalledTemplates()
    filteredList = []
    filteredList[:] = [x for x in templateList if  x.parent == "-"]
    return filteredList
    
def getInstalledTemplatesWithoutParentAndSystemTemplates():
    templateList = getInstalledTemplatesWithoutParent()
    filteredList = []
    filteredList[:] = [x for x in templateList if  x.name not in SYSTEM_TEMPLATES]
    return filteredList

def getChildTemplates(name):
    templateList = getInstalledTemplates()
    filteredList = []
    filteredList[:] = [x for x in templateList if  x.parent == name]
    return filteredList


def isTemplateConflicting(filename):
    zf = zipfile.ZipFile(filename)
    data = zf.read("config/templatesCfg.json")
    jsonObj = json.loads(data)
    omegaLocation = getOmegaHome()
    if not omegaLocation:
        #print "Could not read Omega Configuration Directory!"
        return False
    templatesCfgFile = open(omegaLocation+"\\web\\config\\templatesCfg.json", "r")
    jsonTemplateCfgFile = json.load(templatesCfgFile)
    templatesCfgFile.close()
    templateNameList = []
    conflicts = []
    for i in range(len(jsonObj)):
        templateNameList.append(jsonObj[i][0])
        found = False
        for j in range(len(jsonTemplateCfgFile)):
            if jsonObj[i][0] == jsonTemplateCfgFile[j][0]:
                #print "Template "+jsonObj[i][0]+" already exists as Version "+jsonTemplateCfgFile[j][1]+" do you want to replace it with Version "+jsonObj[i][1]+"?"
                conflicts.append([jsonObj[i][0], jsonObj[i][1], jsonTemplateCfgFile[j][1]])
                found=True
                break
    return conflicts

def getExtensionForTemplate(template):
    omegaLocation = getOmegaHome()
    extensionsCfgFile = open(omegaLocation+"\\web\\config\\extensionsCfg.json", "r")
    jsonExtensionsCfgFile = json.load(extensionsCfgFile)
    extensionsCfgFile.close()
    for entry in jsonExtensionsCfgFile:
        if entry[0] == template.json[3]:
            return Extension(entry[0], entry[1], entry)
    return None

def getDictForTemplates(templates):
    omegaLocation = getOmegaHome()
    dictFile = open(omegaLocation+"\\web\\config\\dictionary.json", "r")
    jsonDictFile = json.load(dictFile)
    dictFile.close()
    dictionary = {}
    dictionary["templatesCfg.json"] = {}
    for template in templates:
        if "templatesCfg.json" in jsonDictFile:
            if template.name in jsonDictFile["templatesCfg.json"]:
                dictionary["templatesCfg.json"][template.name] = jsonDictFile["templatesCfg.json"][template.name]
        if "templatesCfg.json"+template.name in jsonDictFile:
                dictionary["templatesCfg.json"+template.name] = jsonDictFile["templatesCfg.json"+template.name]
        if "templatesCfg.json"+template.name+"names" in jsonDictFile:
                dictionary["templatesCfg.json"+template.name+"names"] = jsonDictFile["templatesCfg.json"+template.name+"names"]
    return dictionary



def installPackage(filename):
    #get infos
    extensionBlackList = []
    omegaLocation = getOmegaHome()
    if not omegaLocation:
        msgBox("ERROR","Could not read O-MEGA Configuration Directory!","error")
        return False
    zf = zipfile.ZipFile(filename)
    #import EG XML
    egFileTree = ET.parse(getEventghostXml())
    egFileRoot = egFileTree.getroot()
    egAutostart = egFileRoot.findall("Autostart")[0]
    loadedPlugins=['EventGhost','System','Window','Mouse']
    for plugin in egAutostart.findall("Plugin"):
        loadedPlugins.append(plugin.get("Identifier"))
    #import set to extensionsCfg.json
    if "config/extensionsCfg.json" in zf.namelist():
        data = zf.read("config/extensionsCfg.json")
        jsonObj = json.loads(data)
        extensionsCfgFile = open(omegaLocation + "\\web\\config\\extensionsCfg.json", "r")
        jsonExtensionsCfgFile = json.load(extensionsCfgFile)
        extensionsCfgFile.close()
        missingPlugins=[]
        for extension in jsonObj:
            if extension[3]!="":
                for plugin in extension[3]:
                    if plugin and plugin not in loadedPlugins:
                        missingPlugins.append(plugin)
        if len(missingPlugins)>0:
            msgBox("ERROR","The following required plugins are missing in your configuration, they need to be added before the importer can import the desired Extension(s): "+(", ".join(missingPlugins)),"error")
            return False
        for i in range(len(jsonObj)):
            found = False
            for j in range(len(jsonExtensionsCfgFile)):
                if jsonObj[i][0] == jsonExtensionsCfgFile[j][0]:
                    #print "Extension " + jsonObj[i][0] + " already exists! will replace it.."
                    if askYesNo("Extension conflict detected!", "The extension "+jsonObj[i][0]+" - "+jsonObj[i][1]+" already exists as version "+jsonExtensionsCfgFile[j][1]+". Do you want to overwrite?"):
                        jsonExtensionsCfgFile[j] = jsonObj[i]
                    else:
                        extensionBlackList.append(jsonObj[i][0])
                    found = True
                    break
            if found == False:
                jsonExtensionsCfgFile.append(jsonObj[i])
                #print "Extension" + jsonObj[i][0] + " was appended."
        extensionsCfgFile = open(omegaLocation + "\\web\\config\\extensionsCfg.json", "w")
        json.dump(jsonExtensionsCfgFile, extensionsCfgFile)
        extensionsCfgFile.close()
    #copy html files
    tempFolder = tempfile.mkdtemp()
    if "config/templatesCfg.json" in zf.namelist():
        data = zf.read("config/templatesCfg.json")
        jsonObj = json.loads(data)
        processedDirs=[]
        for name in zf.namelist():
            if name.startswith("html/"):
                name = name.replace("html/", "")
                name.replace("/", "\\")
                tempDir=os.path.dirname(name)
                zf.extract("html/" + name, tempFolder)
                if tempDir not in processedDirs:
                    processedDirs.append(tempDir)
        for tempDir in processedDirs:
            htmlPath = omegaLocation + "\\web\\templates\\" + tempDir
            if os.path.exists(htmlPath):
                shutil.rmtree(htmlPath)
                sleep(3)
            shutil.copytree(os.path.join(tempFolder, "html\\"+tempDir), htmlPath)
        shutil.rmtree(tempFolder)
        #import set to templatesCfg.json
        templatesCfgFile = open(omegaLocation + "\\web\\config\\templatesCfg.json", "r")
        jsonTemplateCfgFile = json.load(templatesCfgFile)
        templatesCfgFile.close()
        templateNameList = []
        for i in range(len(jsonObj)):
            templateNameList.append(jsonObj[i][0])
            found = False
            for j in range(len(jsonTemplateCfgFile)):
                if jsonObj[i][0] == jsonTemplateCfgFile[j][0]:
                    #print "Template " + jsonObj[i][0] + " already exists! will replace it.. (Version: " + jsonObj[i][1] + ")"
                    jsonTemplateCfgFile[j] = jsonObj[i]
                    found = True
                    break
            if found == False:
                jsonTemplateCfgFile.append(jsonObj[i])
                #print "Template " + jsonObj[i][0] + " (Version: " + jsonObj[i][1] + ") was appended."
        templatesCfgFile = open(omegaLocation + "\\web\\config\\templatesCfg.json", "w")
        json.dump(jsonTemplateCfgFile, templatesCfgFile)
        templatesCfgFile.close()
    #import set to dictionary.json
    data = zf.read("config/dictionary.json")
    jsonObj = json.loads(data)
    dictionaryFile = open(omegaLocation + "\\web\\config\\dictionary.json", "r")
    jsonDictionaryFile = json.load(dictionaryFile)
    dictionaryFile.close()
    for i in jsonObj.keys():
        #print "Processing entry " + i
        if i in jsonDictionaryFile:
            #print "Found " + i
            for j in jsonObj[i].keys():
                #print "Itering entry " + j
                jsonDictionaryFile[i][j] = jsonObj[i][j]
        else:
            jsonDictionaryFile[i] = jsonObj[i]
    #print jsonDictionaryFile
    dictionaryFile = open(omegaLocation + "\\web\\config\\dictionary.json", "w")
    json.dump(jsonDictionaryFile, dictionaryFile)
    dictionaryFile.close()
    #print "imported dictionary"
    #create O-MEGA_Extensions folder if not exist
    templateFolder = None
    for folder in egFileRoot.findall("Folder"):
        if folder.get("Name") == "O-MEGA_Extensions":
            templateFolder = folder
    if (templateFolder is None):
        #print "O-MEGA_Extensions Folder not found! Will create it!"
        templateFolder = ET.Element("Folder")
        templateFolder.set("Expanded", "False")
        templateFolder.set("Name", "O-MEGA_Extensions")
        egFileRoot.append(templateFolder)
    #import new template folder
    data = zf.read("eventghost/egimport.xml")
    importRoot = ET.fromstring(data)
    #print "blacklist: " + str(extensionBlackList)
    for folder in importRoot.findall("Folder"):
        #print "importing Folder ", folder.get("Name"), " to EG.xml"
        found = False
        for existingFolder in templateFolder.findall("Folder"):
            if existingFolder.get("Name") == folder.get("Name"):
                #msgBox("bla","Allready existing..")
                found = True
                if existingFolder.get("Name") not in extensionBlackList:
                    #msgBox("bla","Will overwrite it!")
                    templateFolder.remove(existingFolder)
                    templateFolder.append(folder)
                    #existingFolder = folder
                break
        if found == False:
            templateFolder.append(folder)
    #write XML file
    egFileTree.write(getEventghostXml())
    return True
	

def exportTemplate(filename, templates, extensions):
    tempFolder = tempfile.mkdtemp()
    tempConfigFolder = tempFolder+"\\config"
    tempEventghostFolder = tempFolder+"\\eventghost"
    tempHtmlFolder = tempFolder+"\\html"
    os.mkdir(tempConfigFolder)
    os.mkdir(tempEventghostFolder)
    os.mkdir(tempHtmlFolder)
    #print tempFolder
    #get templatesCfg.json content
    tempTemplatesCfgJsonFileName = tempConfigFolder+"\\templatesCfg.json"
    templatesJsonList = []
    for entry in templates:
        templatesJsonList.append(entry.json)
    tempTemplatesCfgJsonFile = open(tempTemplatesCfgJsonFileName, "w")
    json.dump(templatesJsonList, tempTemplatesCfgJsonFile)
    tempTemplatesCfgJsonFile.close()
    #export extensions
    extensionJsonList = []
    for extension in extensions:
        extensionJsonList.append(extension.json)
    tempExtensionsCfgJsonFileName = tempConfigFolder+"\\extensionsCfg.json"
    tempExtensionsCfgJsonFile = open(tempExtensionsCfgJsonFileName, "w")
    json.dump(extensionJsonList, tempExtensionsCfgJsonFile)
    tempExtensionsCfgJsonFile.close()
    #export dict for templates
    tempDictJsonFileName = tempConfigFolder+"\\dictionary.json"
    tempDictJsonFile = open(tempDictJsonFileName, "w")
    json.dump(getDictForTemplates(templates), tempDictJsonFile)
    tempDictJsonFile.close()
    #export eg-xml
    egFileTree = ET.parse(getEventghostXml())
    egFileRoot = egFileTree.getroot()
    #find template folder
    templateFolder = searchForXmlRecursive("O-MEGA_Extensions", egFileRoot)
    #if (templateFolder is None):
        #print "O-MEGA_Extensions Folder not found!!"
    #generate empty XML structure
    root = ET.Element("EventGhost")
    root.set("Version", "1669")
    for template in templates:
        extension = getExtensionForTemplate(template)
        if extension:
            folder = searchForXmlRecursive(extension.name, templateFolder)
            if folder is not None:
                #print "adding XML for Extension "+extension.name
                root.append(folder)
    for extension in extensions:
        for folder in templateFolder.findall("Folder"):
            if folder.get("Name") == extension.name:
                #print "adding XML for Extension "+extension.name
                root.append(folder)
    #write XML file
    tempEGImportXml = tempEventghostFolder+"\\egimport.xml"
    temEGImportXmlFile = open(tempEGImportXml, "w")
    tree = ET.ElementTree(root)
    tree.write(temEGImportXmlFile)
    temEGImportXmlFile.close()
    #get HTML files
    for template in templates:
        if template.html and template.html[0] == "/":
            htmlSrcFolder = os.path.dirname(getOmegaHome()+"\\web"+template.html.replace("/", "\\"))
            targetFolder = os.path.join(tempHtmlFolder, os.path.basename(htmlSrcFolder))
            #os.mkdir(targetFolder)
            if os.path.exists(targetFolder):
                shutil.rmtree(targetFolder)
                sleep(3)
            shutil.copytree(htmlSrcFolder, targetFolder)
    #create zip
    zipf = zipfile.ZipFile(filename, 'w')
    zipdir(tempFolder, zipf)
    zipf.close()
    shutil.rmtree(tempFolder)
    return True
 
 
def checkIfEventGhostIsClosed():
    retry=True
    while retry:
        retry=False
        for p in psutil.process_iter():
            if p.name().lower()=="eventghost.exe":
                if not askYesNo("EventGhost is running!","You need to close EventGhost in order to continue. Please close EventGhost."):
                    return False
                else:
                    retry=True
    return True

EG_PATH=readFromReg("EventGhostPath")