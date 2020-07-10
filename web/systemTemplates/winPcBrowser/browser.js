var secoundBrowser=false;
var copyArray= [];
var cutActiv=false;
var cutFolderPath;
var folderData= [];
var externalRequest=false;
if (self.name == "browserframe2"){
  secoundBrowser=true;
  folderData= parent.folderData;
  omega.pageID=parent.omega.pageID+"2";
  omega.deviceID=parent.omega.deviceID;
}
var actionString2;
var secoundBrowserActive=false;
var advSearch=false;
var folderPath;
var folderPath2;
var isBack=0;
var activeMode="none";
var dataOld="";
var autoBackOK=1;
var myInstanceNr;
var rowsArray= [];
var rowsArrayLength;
var visRowsArray=[];
var selArray = [];
var targetArr= [];//
var firstRow;
var deleteOkV;
var newNameAdd;
var newNameData;
var newName;
var newNameRow;
var functions = ['delete','newFolder','rename','paste','pasteSpecial','createLinks'];
var searchTargetLength = -1;
var openWithOptions = [];
var pasteSpecialOptions = ["/XC","/XN","/XO","/XL","/IS","/IT","/COPYALL","/NOCOPY","/PURGE"];
var pasteSpecialActive = [false,false,false,false,false,false,false,false,false];
var pasteSpecialActiveWait = true;
var pasteSpecialSw = [0,1,2,3,4,5,7,6,8];
var propertiesFolderPath;
var hideHiddenFiles="True";
var buttonConf= [];
var MYEfolder_ID="?dir?";
var MYElink_ID="?lnk?";

omega.useNiceScroll=false;

function bla(force) {
  force=force||false;
  if (advSearch==false && typeof myInstanceNr!="undefined"){
    omega.Request({'method':'getBrowserValue','args':[myInstanceNr,4,1,force],'callback':function(data){
      if (!data){
        delete top.browserInstanceNr[omega.pageID];
        browserStart();
      }
      else if (data!=dataOld || force){
        dataOld=data;
        browserLoad(data);
      }
    }});
  }
}

function bla2(force,ext) {
  ext=ext||false;
  force=force||false;
  isBack=2;
  if (secoundBrowser && ext==false){
    parent.bla2(force,true);
  }
  else if (secoundBrowserActive && ext==false){
    window.frames['browserframe2'].bla2(force,true);
  }
  if (advSearch){
    searchRecus();
  }
  else{
    bla(force);
  }
}
omega.bla2=bla2;


var historie;

function browserStart(){
  if (top.States["devices"][omega.deviceID]["power"]==="[on]"){
    if (typeof top.browserInstanceNr[omega.pageID]=="undefined"){
      
      omega.Request({'method':'startBrowserMenu','args':[top.States["devices"][omega.deviceID]["browser"]["root"], "*", hideHiddenFiles],'callback':function(data){
        myInstanceNr=data;
        top.browserInstanceNr[omega.pageID]=myInstanceNr;
        top.browserInstanceNrs.push([omega.deviceID,myInstanceNr]);
        historie=[["","browser_0"]];
        bla();
      }});
    }
    else{
      myInstanceNr=top.browserInstanceNr[omega.pageID];
      bla();
    }
  }
}

function goToPos(target){
  //console.log("pos: "+target);
  if (advSearch==false){
    if (target==-1){
      if (document.getElementById('textBoxTwo').value!=""){
        searchReset();
      }
      else{
        if (historie.length>1){
          isBack=1;
          omega.Request({'method':'browserGoBack','args':[myInstanceNr],'callback':function(data2){
            if (data2==true){
              historie.pop();
              bla();
            }
            else{
              console.log("Go back from normal failed!! "+historie[historie.length-2][0]);
            }
          }});
        }
      }
    }
    else if (target==-3){
      isBack=0;
      omega.Request({'method':'browserGoToParent','args':[myInstanceNr],'callback':function(data2){
        if (data2==true){
          historie.push(["","browser_0"]);
          bla();
        }
        else{
          console.log("Open parent from normal failed!!");
        }
      }});
    }
    else if (target==-2){
      isBack=0;
      openLocation(top.States["devices"][omega.deviceID]["browser"]["root"]);
    }
    else{
      isBack=0;
      if (fileFolderArray[target]==2||fileFolderArray[target]==4){
        loadTimer=setTimeout("loading();",500);
      }
      omega.Request({'method':'browserExecute','args':[20, "", "", myInstanceNr, target],'callback':function(data2){
        //console.log("go "+data2);
        if (fileFolderArray[target]==2||fileFolderArray[target]==4){
          clearTimeout(loadTimer);
          historie[historie.length-1][1]="browser_"+target;
          historie.push(["","browser_0"]);
          bla();
        }
        else{
          omega.TriggerEvent({command:'browserRun',data:JSON.parse(data2)});
        }
      }});
    }
  }
  else{
    if (target==-1 || target==-3){
      searchRecusReset();
    }
    else if (target==-2){
      isBack=0;
      openLocation(top.States["devices"][omega.deviceID]["browser"]["root"]);
    }
    else{
      if (fileFolderArray[target]==2||fileFolderArray[target]==4){
        isBack=0;
        loadTimer=setTimeout("loading();",500);
        omega.Request({"method":"browserOpenLocation","args":[myInstanceNr,rowsArray[target*2+1]],"callback":function(data2){
          clearTimeout(loadTimer);
          if (data2){
            advSearch=false;
            searchTargetLength=-1;
            historie.push(["","browser_0"]);
            bla();
          }
          else{
            console.log("Open location from advanced search failed!! "+rowsArray[target*2+1]);
          }
        }});
      }
      else{
        omega.TriggerEvent({command:'browserRun',data:rowsArray[target*2+1]});
      }
    }
  }
}

function openLocation(path){
  loadTimer=setTimeout("loading();",500);
  omega.Request({'method':'browserOpenLocation','args':[myInstanceNr,path],'callback':function(data2){
    clearTimeout(loadTimer);
    if (data2==true){
      advSearch=false;
      searchTargetLength=-1;
      historie.push(["","browser_0"]);
      bla();
    }
    else{
      console.log("Open location failed!!");
    }
  }});
}

//----------------------DeleteStart-------------------------//
function deleteF(targets){
  targetArr=[];
  for (var i=0; i<targets.length; i++){
    targetArr[i]=[targets[i],fileFolderArray[targets[i]]];
  }
  deleteOkV=false;
  var content = '<table class="stdtable" border="0" cellpadding="0" cellspacing="0" align="center" style="width:1px"><tr><td colspan="2" style="text-align:center">'+top.getText('deleteElement',0)+targetArr.length+top.getText('deleteElement',1)+'</td></tr><tr><td><button class="p1 w2 default" onClick="deleteOk();">'+top.getText('yes',0)+'</button></td><td class="last"><button class="p1 w2 default" onClick="TINY.box.hide();">'+top.getText('no',0)+'</button></td></tr></table>';
  if (secoundBrowser){
    parent.TINY.box.show({html:content,boxid:'deletebox',width:160,height:100,maskid:'whitemask',opacity:30,animate:true,close:false,closejs:function(){deleteCancel();}});
    parent.externalRequest=true;
  }
  else{
    TINY.box.show({html:content,boxid:'deletebox',width:160,height:100,maskid:'whitemask',opacity:30,animate:true,close:false,closejs:function(){deleteCancel();}});
    externalRequest=false;
  }
}

function deleteOk(){
  if (externalRequest){
    window.frames['browserframe2'].deleteOkV=true;
  }
  else{
    deleteOkV=true;
  }
  TINY.box.hide();
}

function deleteCancel(){
  if (deleteOkV==false){
    buttonPrint('delete',0);
  }
  else{
    if (advSearch){
      var tempArray=[];
      for (var i=0; i<targetArr.length; i++){
        var tempFileFolder="file";
        if (targetArr[i][1]=="2"){
          tempFileFolder="folder";
        }
        tempArray.push([rowsArray[targetArr[i][0]*2+1],tempFileFolder]);
      }
      searchTargetLength=rowsArrayLength-targetArr.length;
      omega.TriggerEvent({command:"browserDelete",data:{"targets":tempArray}});
      browserLoad(dataOld);
    }
    else{
      var tempTargetIds=[];
      for (var i=0; i<targetArr.length; i++){
        tempTargetIds.push(targetArr[i][0]);
      }
      omega.Request({'method':'getBrowserValues','args':[myInstanceNr,12,tempTargetIds],'callback':function(data2){
        var dataTempArr=JSON.parse(data2);
        var tempArray=[];
        for (var i=0;i<dataTempArr.length;i++){
          var tempFileFolder="file";
          if (targetArr[i][1]=="2"){
            tempFileFolder="folder";
          }
          tempArray.push([dataTempArr[i],tempFileFolder]);
        }
        folderData[folderPath]['browsertargetlength']=folderData[folderPath]['browserlength']-dataTempArr.length;
        omega.TriggerEvent({command:"browserDelete",data:{"targets":tempArray}});
        browserLoad(dataOld);
      }});
    }
  }
}
//----------------------DeleteEnd-------------------------//
//----------------------ReName&NewFolderStart-------------------------//
function renameF(row){
  newName="";
  newNameAdd="";
  if (row==-1){
    newNameData=top.getText('newFolder',1);
  }
  else{
    if (advSearch==false){
      newNameData=rowsArray[row];
    }
    else{
      newNameData=rowsArray[row*2];
    }
    newNameData=newNameData.replace(MYEfolder_ID,"");
    if (newNameData.indexOf(MYElink_ID)!=-1){
      newNameData=newNameData.replace(MYElink_ID,"");
      newNameAdd=".lnk";
    }
  }
  newNameRow=row;
  if (secoundBrowser){
    parent.TINY.box.show({html:'<div id="reNameContent"></div>',boxid:'renamebox',width:300,height:160,fixed:true,maskid:'whitemask',opacity:30,animate:true,close:false,openjs:function(){parent.reNameLoad(newNameData);},closejs:function(){reNameCancel();}});
    parent.externalRequest=true;
  }
  else{
    TINY.box.show({html:'<div id="reNameContent"></div>',boxid:'renamebox',width:300,height:160,fixed:true,maskid:'whitemask',opacity:30,animate:true,close:false,openjs:function(){reNameLoad(newNameData);},closejs:function(){reNameCancel();}});
    externalRequest=false;
  }
}

function reNameLoad(data){
  document.getElementById('reNameContent').innerHTML='<center><table class="stdtable" border="0" cellpadding="0" cellspacing="0"><tr><td colspan="2"><input name="reNameBox" type="text" id="textBox" class="w4"></td></tr><tr><td><button class="p1 w2 default" onClick="reNameOk();">'+top.getText('ok',0)+'</button></td><td><button class="p1 w2 default" onClick="TINY.box.hide();" >'+top.getText('cancel',0)+'</button></td></tr></table><br><small>'+top.getText('browserMessages','defineName')+'</small></center>';
  document.getElementById('textBox').value=data;
  //document.getElementById('textBox').focus();
  document.getElementById('textBox').select();
  document.getElementById('textBox').onkeyup = reNameKeyEnterHandler;
}

function reNameKeyEnterHandler(event)
{
    switch(event.which)
    {
        case  13:reNameOk(); break;
        default: break;
//        default:  alert(event.which); break;
    }
    return false;
}

function reNameOk(){
  //newName=encodeURIComponent(document.getElementById('textBox').value);
  newName=document.getElementById('textBox').value;
  if (externalRequest){
    window.frames['browserframe2'].reNameOk2(newName);
  }
  else{
    reNameOk2(newName);
  }
  TINY.box.hide();
}

function reNameOk2(newName){
  var itsNew=true;
  for (var j=0; j<rowsArrayLength; j++){
    if (rowsArray[j]==newName){
      itsNew=false;
    }
  }
  if (newNameRow==-1){
    var tempData=[folderPath,newName];
    if (itsNew==true){
      folderData[folderPath]['browsertargetlength']=folderData[folderPath]['browserlength']+1;
      omega.TriggerEvent({command:'browserNewFolder',data:{"location":folderPath,"name":newName}});
    }
    else{
      top.alertBox(top.getText('itemNameExists',0),function(o){buttonPrint('newFolder',0);});
    }
  }
  else if (newName!=newNameData&&newName!=""){
    if (advSearch==false){
      if (itsNew==true){
        omega.TriggerEvent({command:'browserRename',data:{"location":(folderPath+"\\"+newNameData+newNameAdd),"name":(newName+newNameAdd)}});
      }
      else{
        top.alertBox(top.getText('itemNameExists',0),function(o){buttonPrint('rename',0);});
      }
    }
    else{
      omega.TriggerEvent({command:'browserRename',data:{"location":(rowsArray[newNameRow*2+1]+newNameAdd),"name":(newName+newNameAdd)}});
    }
  }
}

function reNameCancel(){
  buttonPrint('newFolder',0);
  buttonPrint('rename',0);
}
//----------------------ReName&NewFolderEnd-------------------------//
//-------------------------CopyCutStart--------------------------------//
function copyF(type,targets){
  targetArr=[];
  if (secoundBrowser){
    parent.copyArray=[];
    copyArray=parent.copyArray;
    if (type=="cut"){
      parent.cutActiv=true;
      parent.cutFolderPath=folderPath;
    }
    else{
      parent.cutActiv=false;
    }
  }
  else{
    copyArray=[];
    if (type=="cut"){
      cutActiv=true;
      cutFolderPath=folderPath;
    }
    else{
      cutActiv=false;
    }
  }
  if (advSearch){
    for (var i=0; i<targets.length; i++){
      copyArray[i]=[];
      targetArr[i]=[targets[i],fileFolderArray[targets[i]]];
      copyArray[i].push(rowsArray[targetArr[i][0]*2+1]);
      copyArray[i].push(targetArr[i][1]);
      copyArray[i].push(targetArr[i][2]);
    }
  }
  else{
    var tempTargetIds=[];
    for (var i=0; i<targets.length; i++){
      targetArr[i]=[targets[i],fileFolderArray[targets[i]]];
      targetArr[i].push(rowsArray[targetArr[i][0]]);
      tempTargetIds.push(targetArr[i][0]);
    }
    omega.Request({'method':'getBrowserValues','args':[myInstanceNr,12,tempTargetIds],'callback':function(data2){
      var dataTempArr=JSON.parse(data2);
      for (var i=0;i<dataTempArr.length;i++){
        copyArray[i]=[];
        copyArray[i].push(dataTempArr[i]);
        var tempFileFolder="file";
        if (targetArr[i][1]=="2"){
          tempFileFolder="folder";
        }
        copyArray[i].push(tempFileFolder);
        copyArray[i].push(targetArr[i][2]);
      }
    }});
  }
}
//--------------------------CopyCutEnd---------------------------------//
//-------------------------PasteStart---------------------------------//
function pasteF(options,wait){
  var y=0;
  if (secoundBrowser){
    copyArray=parent.copyArray;
    cutActiv=parent.cutActiv;
    cutFolderPath=parent.cutFolderPath;
  }
  for (var i=0; i<copyArray.length; i++){
    y++;
    for (var j=0; j<rowsArrayLength; j++){
      if (rowsArray[j]==copyArray[i][2]){
        y--;
        break;
      }
    }
    copyArray[i].splice(2,1);
  }
  folderData[folderPath]['browsertargetlength']=folderData[folderPath]['browserlength']+y;
  var parameters=[copyArray,folderPath,options];
  if (options=="link"){
    omega.TriggerEvent({command:"browserLink",data:{"targets":copyArray,"location":folderPath}});
  }
  else{
    if (cutActiv){
      folderData[cutFolderPath]['browsertargetlength']=folderData[cutFolderPath]['browserlength']-y;
      options+=" /MOVE";
    }
    omega.TriggerEvent({command:"browserCopy",data:{"targets":copyArray,"location":folderPath,"parameters":options,"wait":wait}});
    if (cutActiv){
      if (secoundBrowser==false){
        copyArray=[];
        cutActiv=false;
      }
      else{
        parent.copyArray=[];
        parent.cutActiv=false;
      }
    }
    browserLoad(dataOld);
  }
}
//--------------------------PasteEnd----------------------------------//
//--------------------------openWithStart-----------------------------//
function openWithF(targets){
  targetArr=[];
  var actionArray=[];
  if (advSearch){
    for (var i=0;i<targets.length;i++){
      targetArr[i]=[targets[i],fileFolderArray[targets[i]]];
      actionArray.push(rowsArray[targetArr[i][0]*2+1]);
    }
    //actionString2=encodeURIComponent(JSON.stringify(actionArray));
    actionString2=actionArray;
  }
  else{
    var tempTargetIds=[];
    for (var i=0; i<targets.length; i++){
      targetArr[i]=[targets[i],fileFolderArray[targets[i]]];
      targetArr[i].push(rowsArray[targetArr[i][0]]);
      tempTargetIds.push(targetArr[i][0]);
    }
    omega.Request({'method':'getBrowserValues','args':[myInstanceNr,1,tempTargetIds],'callback':function(data2){
      actionString2=JSON.parse(data2);
    }});
  }
  if (secoundBrowser){
    data = parent.openWithLoad();
    choosen = data[0];
    content = data[1];
    if (!choosen){
      top.alertBox(top.getText("browserMessages","noOpenWithOptionsFound"),function(){openWithCancel();});
    }
    else{
      parent.TINY.box.show({html:content,boxid:'openWithBox',width:300,height:80,maskid:'whitemask',opacity:30,animate:true,close:false,openjs:function(){parent.openWithOption(choosen);},closejs:function(){openWithCancel();}});
      parent.externalRequest=true;
    }
  }
  else{
    data = openWithLoad();
    choosen = data[0];
    content = data[1];
    if (!choosen){
      top.alertBox(top.getText("browserMessages","noOpenWithOptionsFound"),function(){openWithCancel();});
    }
    else{
      TINY.box.show({html:content,boxid:'openWithBox',width:300,height:80,maskid:'whitemask',opacity:30,animate:true,close:false,openjs:function(){openWithOption(choosen);},closejs:function(){openWithCancel();}});
      externalRequest=false;
    }
  }
}

function openWithLoad(){
  var choosen="";
  openWithOptions=[];
  var content='<table border="0" cellpadding="0" cellspacing="0" align="center"><tr><td><table class="stdtable" border="0" cellpadding="0" cellspacing="0"><tr>';
  var typ="programs";
  for (var i=0; i<top.programs.length; i++){
    if (top.programs[i][3]==omega.deviceID){
      var id=top.programs[i][0];
      var type=top.programs[i][1];
      var temptype=top.extensions[top.extensionsIDArray[type]];
      if (temptype[4]["browserOpenSuffix"] || temptype[4]["browserAddSuffix"] || temptype[4]["browserPlaySuffix"]){
        var commands={};
        if (temptype[4]["browserOpenSuffix"]){
          commands["browserOpenSuffix"]=temptype[4]["browserOpenSuffix"];
        }
        if (temptype[4]["browserPlaySuffix"]){
          commands["browserPlaySuffix"]=temptype[4]["browserPlaySuffix"];
        }
        if (temptype[4]["browserAddSuffix"]){
          commands["browserAddSuffix"]=temptype[4]["browserAddSuffix"];
        }
        openWithOptions.push([typ,type,id,commands]);
        content+='<td id="openWith'+typ+id+'B"></td>';
        if (choosen==""){
          choosen=typ+id;
        }
      }
    }
  }
  content+='</tr></table></td></tr><tr><td><div id="openWithOptionsContent"></div></td></tr></table>';
  return [choosen, content];
}

function openWithOption(target){
  var selectedIndex=0;
  for (var i=0; i<openWithOptions.length; i++){
    var tempTarget=openWithOptions[i][0]+openWithOptions[i][2];
    var tempName="?";
    if (typeof top.text[openWithOptions[i][0]+'.jsonnames'][openWithOptions[i][2]]!="undefined"){
      tempName=top.text[openWithOptions[i][0]+'.jsonnames'][openWithOptions[i][2]];
    }
    else {
      tempName=openWithOptions[i][2];
    }
    var targetDeviceId=openWithOptions[i][0]+"/"+openWithOptions[i][2];
    var tempTargetPageIDs=top.filesTargetArray[targetDeviceId];
    if (tempTargetPageIDs){
      for (var y=0; y<tempTargetPageIDs.length; y++){
        if (top.files[top.filesIDArray[top.files[tempTargetPageIDs[y]][1]]][2]!=targetDeviceId){
          tempName=top.getText('files.json',top.files[tempTargetPageIDs[y]][0]);
          break;
        }
      }
    }
    if (tempTarget==target){
      selectedIndex=i;
      document.getElementById("openWith"+tempTarget+"B").innerHTML='<button class="p1 w2 green">'+tempName+'</button>';
    }
    else{
      document.getElementById("openWith"+tempTarget+"B").innerHTML='<button class="p1 w2 default" onClick="openWithOption(\''+tempTarget+'\');">'+tempName+'</button>';
    }
  }
  var tempStr='<table class="stdtable" border="0" cellpadding="0" cellspacing="0"><tr>';
  if(openWithOptions[selectedIndex][3]["browserOpenSuffix"]){
    tempStr+='<td><button class="p1 w2 default" onClick="openWithOk(\''+openWithOptions[selectedIndex][0]+'.'+openWithOptions[selectedIndex][1]+'\',\''+openWithOptions[selectedIndex][2]+'\',\''+openWithOptions[selectedIndex][3]["browserOpenSuffix"]+'\');">'+top.getText('open',0)+'</button></td>';
  }
  if(openWithOptions[selectedIndex][3]["browserPlaySuffix"]){
    tempStr+='<td><button class="p1 w2 default" onClick="openWithOk(\''+openWithOptions[selectedIndex][0]+'.'+openWithOptions[selectedIndex][1]+'\',\''+openWithOptions[selectedIndex][2]+'\',\''+openWithOptions[selectedIndex][3]["browserPlaySuffix"]+'\');">'+top.getText('play',0)+'</button></td>';
  }
  if(openWithOptions[selectedIndex][3]["browserAddSuffix"]){
    tempStr+='<td><button class="p1 w2 default" onClick="openWithOk(\''+openWithOptions[selectedIndex][0]+'.'+openWithOptions[selectedIndex][1]+'\',\''+openWithOptions[selectedIndex][2]+'\',\''+openWithOptions[selectedIndex][3]["browserAddSuffix"]+'\');">'+top.getText('add',0)+'</button></td>';
  }
  tempStr+='</tr></table>';
  document.getElementById("openWithOptionsContent").innerHTML=tempStr;
}

function openWithOk(what,id,how){
  if(externalRequest){
    window.frames['browserframe2'].openWithGo(what,id,how);
    window.frames['browserframe2'].selResetAll();
  }
  else{
    openWithGo(what,id,how);
    selResetAll();
  }
  TINY.box.hide();
}

function openWithGo(what,id,how){
  omega.TriggerEvent({command:'openWith',data:[what+'.'+how,id,actionString2]});
}

function openWithCancel(){
  buttonPrint('openWith',0);
}

//--------------------------openWithEnd-------------------------------//
//--------------------------pasteSpecialStart-----------------------------//
function pasteSpecialF(){
  var content='<table border="0" cellpadding="0" cellspacing="0" align="center"><tr><td><table class="stdtable" border="0" cellpadding="0" cellspacing="0"><tr>';
  var buttonCount=pasteSpecialOptions.length;
  if (top.recording){
    buttonCount++;
  }
  for (var i=0; i<buttonCount; i++){
    content+='<td><div id="pasteSpecial'+i+'B"></div></td>';
  }
  if (secoundBrowser){
    content+='</tr></table></td></tr><tr><td><table class="stdtable" border="0" cellpadding="0" cellspacing="0" align="center"><tr><td><button class="p1 w2 default" onClick="window.frames[\'browserframe2\'].pasteSpecialOk();">'+top.getText('ok',0)+'</button></td><td><button class="p1 w2 default" onClick="TINY.box.hide();" >'+top.getText('cancel',0)+'</button></td></tr></table></td></tr></table>';
  parent.TINY.box.show({html:content,boxid:'pasteSpecialBox',width:buttonCount*82,height:72,maskid:'whitemask',opacity:30,animate:true,close:false,openjs:function(){parent.pasteSpecialLoad(content);},closejs:function(){pasteSpecialCancel();}});
  }
  else{
    content+='</tr></table></td></tr><tr><td><table class="stdtable" border="0" cellpadding="0" cellspacing="0" align="center"><tr><td><button class="p1 w2 default" onClick="pasteSpecialOk();">'+top.getText('ok',0)+'</button></td><td><button class="p1 w2 default" onClick="TINY.box.hide();" >'+top.getText('cancel',0)+'</button></td></tr></table></td></tr></table>';
    TINY.box.show({html:content,boxid:'pasteSpecialBox',width:buttonCount*82,height:72,maskid:'whitemask',opacity:30,animate:true,close:false,openjs:function(){pasteSpecialLoad(content);},closejs:function(){pasteSpecialCancel();}});
  }
}

function pasteSpecialLoad(content){
  //document.getElementById("pasteSpecialContent").innerHTML=content;
  for (var i=0; i<pasteSpecialOptions.length; i++){
    pasteSpecialOption(i,"none");
  }
  if (top.recording){
    pasteSpecialWait(pasteSpecialOptions.length,"none");
  }
}

function pasteSpecialOption(option, newVal){
  if (newVal!="none"){
    pasteSpecialActive[option]=newVal;
  }
  if (pasteSpecialActive[option]==true){
    if (pasteSpecialSw[option]!=option && pasteSpecialActive[pasteSpecialSw[option]]==true){
      pasteSpecialOption(pasteSpecialSw[option],false);
    }
    document.getElementById("pasteSpecial"+option+"B").innerHTML='<button class="p1 w2 green" onClick="pasteSpecialOption('+option+',false);" class="green">'+top.getText('pasteSpecial',pasteSpecialOptions[option])+'</button>';
  }
  else{
    document.getElementById("pasteSpecial"+option+"B").innerHTML='<button class="p1 w2 default" onClick="pasteSpecialOption('+option+',true);">'+top.getText('pasteSpecial',pasteSpecialOptions[option])+'</button>';
  }
}

function pasteSpecialWait(option,newVal){
  if (newVal!="none"){
    pasteSpecialActiveWait=newVal;
  }
  if (pasteSpecialActiveWait==true){
    document.getElementById("pasteSpecial"+option+"B").innerHTML='<button class="p1 w2 green" onClick="pasteSpecialWait('+option+',false);" class="green">'+top.getText('pasteSpecial','wait')+'</button>';
  }
  else{
    document.getElementById("pasteSpecial"+option+"B").innerHTML='<button class="p1 w2 default" onClick="pasteSpecialWait('+option+',true);">'+top.getText('pasteSpecial','wait')+'</button>';
  }
}

function pasteSpecialOk(){
  var actionString="";
  var wait=false;
  if (secoundBrowser){
    pasteSpecialActive=parent.pasteSpecialActive;
    pasteSpecialActiveWait=parent.pasteSpecialActiveWait;
  }
  for (var i=0; i<pasteSpecialActive.length; i++){
    if (pasteSpecialActive[i]==true){
      actionString+=" "+pasteSpecialOptions[i];
    }
  }
  pasteF(actionString,pasteSpecialActiveWait);
  if (secoundBrowser){
    parent.TINY.box.hide();
  }
  else{
    TINY.box.hide();
  }
}

function pasteSpecialCancel(){
  buttonPrint('pasteSpecial',0);
}

//--------------------------pasteSpecialEnd-------------------------------//
//--------------------------propertiesStart-----------------------------//
function propertiesF(targets){
  var target2=[];
  var mode=-1;
  if (targets.length==0){
    target2=[folderPath];
  }
  else{
    mode=0;
    if (advSearch){
      for (var i=0;i<targets.length;i++){
        target2.push(parseInt(rowsArray[targets[i]*2+1],10));
      }
    }
    else{
      for (var i=0;i<targets.length;i++){
        target2.push(parseInt(targets[i],10));
      }
    }
  }
  propertiesFolderPath=folderPath;
  omega.Request({'method':'getProperties','args':[myInstanceNr,target2, mode],'callback':function(data){
    data=JSON.parse(data);
    var content='<center><table class="stdtable" border="0" cellpadding="0" cellspacing="0">';
    if (data[0]!="False"){
      content+='<tr><td style="text-align:right"><b>'+top.getText('path',0)+':</b></td><td class="selectable">'+data[0]+'</td></tr>';
    }
    if (data[1]!="False"){
      var size=data[1][0];
      if (targets.length>1){
        content+='<tr><td style="text-align:right" class="selectable"><b>'+top.getText('items',0)+':</b></td><td class="selectable">'+targets.length+'</td></tr>';
      }
      content+='<tr><td style="text-align:right"><b>'+top.getText('size',0)+':</b></td><td class="selectable">'+top.calculateFilesize(size)+'</td></tr>';
      content+='<tr><td style="text-align:right"><b>'+top.getText('files',0)+':</b></td><td class="selectable">'+data[1][1]+'</td></tr>';
      content+='<tr><td style="text-align:right"><b>'+top.getText('folders',0)+':</b></td><td class="selectable">'+data[1][2]+'</td></tr>';
    }
    else{
      content+='<tr><td style="text-align:right"><b>'+top.getText('items',0)+':</b></td><td class="selectable">'+folderData[folderPath]['browserlength']+'</td></tr>';
    }
    for (var i=2;i<=3;i++){
      if (data[i]!="False"){
        var dateTime=data[i];
        var dateTime2=top.dateTransform(dateTime[0],dateTime[1],dateTime[2]);
        dateTime2+=" - "+dateTime[3]+":"+dateTime[4]+":"+dateTime[5];
        switch(i){
          case  2:dateTime=top.getText('created',0); break;
          case  3:dateTime=top.getText('modified',0); break;
          case  4:dateTime=top.getText('lastAccess',0); break;
          default:dateTime="undefined"; break;
        }
        content+='<tr><td style="text-align:right"><b>'+dateTime+':</b></td><td class="selectable">'+dateTime2+'</td></tr>';
      }
    }
    if (data[5]!="False"){
      var start=262144;
      var value=parseInt(data[5]);
      values="";
      while (start>=1){
        if (value/start>=1){
          values+=", "+top.getText('attributes',start);
          value-=start;
        }
        start=start/2;
      }
      if (values!=""){
        values=values.substring(2);
      }
      content+='<tr><td style="text-align:right"><b>'+top.getText('attributes',0)+':</b></td><td>'+values+'</td></tr>';
    }
    content+='</table><br><button class="p1 w2 default" onClick="propertiesOk('+mode+');">'+top.getText('ok',0)+'</button></center>';
    if (secoundBrowser){
      parent.TINY.box.show({html:content,boxid:'propertiesBox',maskid:'whitemask',opacity:30,animate:true,close:false,closejs:function(){propertiesCancel();}});
      parent.externalRequest=true;
    }
    else{
      TINY.box.show({html:content,boxid:'propertiesBox',maskid:'whitemask',opacity:30,animate:true,close:false,closejs:function(){propertiesCancel();}});
      externalRequest=false;
    }
  }});
}

function propertiesOk(mode){
  if (mode!=-1){
    if (externalRequest){
      if (window.frames['browserframe2'].propertiesFolderPath==window.frames['browserframe2'].folderPath){
        window.frames['browserframe2'].selResetAll();
      }
    }
    else if (propertiesFolderPath==folderPath){
      selResetAll();
    }
  }
  TINY.box.hide();
}

function propertiesCancel(){
  buttonPrint('properties',0);
}

//--------------------------propertiesEnd-------------------------------//
//------------------------configureHomeStart----------------------------//
function changeHomeDirF(oldPath){
  var content ='<center><table class="stdtable" border="0" cellpadding="0" cellspacing="0">';
  content += '<tr><td>'+top.getText('path',0)+':</td><td colspan="2" align="center" class="last"><input name="pathBox" type="text" id="pathBox" class="w4"></td></tr>';
  content += '<tr><td></td><td><button class="p1 w2 default" onClick="changeHomeDirOk();">'+top.getText('ok',0)+'</button></td><td class="last"><button class="p1 w2 default" onClick="TINY.box.hide();">'+top.getText('cancel',0)+'</button></td></tr></table></center>';
  if (secoundBrowser){
    parent.TINY.box.show({html:content,boxid:'changeHomeDorbox',maskid:'whitemask',opacity:30,animate:true,close:false,openjs:function(){parent.changeHomeDirOpen(oldPath);},closejs:function(){changeHomeDirCancel();}});
  }
  else{
    TINY.box.show({html:content,boxid:'changeHomeDorbox',maskid:'whitemask',opacity:30,animate:true,close:false,openjs:function(){changeHomeDirOpen(oldPath);},closejs:function(){changeHomeDirCancel();}});
  }
}

function changeHomeDirOk(){
  omega.SetUserSetting({name:"homeFolder",value:document.getElementById("pathBox").value});
  TINY.box.hide();
}

function changeHomeDirOpen(data){
  document.getElementById("pathBox").value=data;
}

function changeHomeDirCancel(){
  if (advSearch || folderPath!=omega.GetUserSetting({name:"homeFolder"})){
    buttonPrint('home',0,'','p1 w2');
  }
}

//------------------------configureHomeEnd------------------------------//

function selected(row){
  var index = selArray.indexOf(row);
  if (index==-1){
    selArray.push(row);
    contentvar='<button class="p1 w1 green"></button>';
  }
  else{
    selArray.splice(index,1);
    contentvar='<button class="p1 w1 default"></button>';
  }
  window.frames['browserContentframe'].contenter('sel'+row, contentvar);
}

function selAll(){
  for (var i=0; i<visRowsArray.length; i++){
    if (selArray.indexOf(visRowsArray[i])==-1){
      selected(visRowsArray[i]);
    }
  }
}

function selInv(){
  for (var i=0; i<visRowsArray.length; i++){
    selected(visRowsArray[i]);
  }
}

function selResetAll(){
  selAll();
  selInv();
  selArray=[];
}

function browserLoad(data,ext){
  ext=ext||false;
  selArray = [];
  for (var i=0; i<functions.length; i++){
    buttonPrint(functions[i],0);
  }
  if (advSearch){
    if (data==""){
      //rowsArray=[];
      rowsArrayLength=0;
    }
    else{
      rowsArray=JSON.parse(data);
      rowsArrayLength=rowsArray.length/2;
    }
    if (searchTargetLength!=-1 && rowsArrayLength>searchTargetLength){
      buttonPrint('delete',1,rowsArrayLength-searchTargetLength);
    }
    contentPrinter(2,1,rowsArrayLength);
  }
  else{
    data2=JSON.parse(data);
    if (data2[1]==""){
      rowsArray=[];
    }
    else{
      rowsArray=data2[1];
    }
    rowsArrayLength=rowsArray.length;
    if (data2[0].length>3 && data2[0].substr(-1)=="\\"){
      data2[0]=data2[0].substring(0,data2[0].length-1);
    }
    folderPath=data2[0];
    historie[historie.length-1][0]=folderPath;
    if (typeof folderData[folderPath] == "undefined"){
      folderData[folderPath]=[];
      folderData[folderPath]['browserlength']=rowsArray.length;
      folderData[folderPath]['browsertargetlength']=-1;
    }
    else{
      folderData[folderPath]['browserlength']=rowsArray.length;
      //console.log(folderData[folderPath]['browserlength']+" <> "+folderData[folderPath]['browsertargetlength']);
      if (folderData[folderPath]['browserlength']!=folderData[folderPath]['browsertargetlength'] && folderData[folderPath]['browsertargetlength']!=-1){
        if (folderData[folderPath]['browserlength']<folderData[folderPath]['browsertargetlength']){
          buttonPrint('paste',1,folderData[folderPath]['browsertargetlength']-folderData[folderPath]['browserlength']);
        }
        else{
          buttonPrint('delete',1,folderData[folderPath]['browserlength']-folderData[folderPath]['browsertargetlength']);
        }
      }
      else{
        folderData[folderPath]['browsertargetlength']=-1;
      }
    }
    if (folderPath==top.States["devices"][omega.deviceID]["browser"]["root"]){
      folderPath2=top.getText('root',0);
      buttonPrint('root',1,'','p1 w2');
    }
    else{
      folderPath2=folderPath;
      buttonPrint('root',0,'','p1 w2');
    }
    if (advSearch==false && folderPath==omega.GetUserSetting({name:"homeFolder"})){
      buttonPrint('home',1,'','p1 w2');
    }
    else{
      buttonPrint('home',0,'','p1 w2');
    }
    document.getElementById('pathShow').innerHTML=top.getText('path',0)+": "+folderPath2;
    document.getElementById('textBoxTwo').value="";
    autoBackOK=1;
    contentPrinter(1,0,folderData[folderPath]['browserlength']);
    if (isBack==1){
      lastBrowserPos(historie[historie.length-1][1]);
    }
    else if(isBack==0){
      lastBrowserPos("browser_"+firstRow);
    }
  }
}

setToLoading=false;
function loading(){
  setToLoading=true;
  window.frames['browserContentframe'].contenter('content', '<center><table style="height:100%;" cellpadding="0" cellspacing="0"><tr><td><img src="/img/loading-black.gif" /></tr></td></table></center>');
}

function contentPrinter(factor,addition,end,searchStr){
    var searchStr=searchStr||"";
    if (searchStr==""){
      selArray=[];
    }
    visRowsArray=[];
    firstRow=-1;
    fileFolderArray={};
    var contentvar='<table class="stdtable2" border="0" style="width:100%;" align="center" cellpadding="0" cellspacing="0">';
    if (end==0){
      contentvar+='<tr><td class="transparent1NH text">'+top.getText("empty",0)+'</td></tr>'
    }
    else{
      for (var i=0; i<end; i++){
        if (rowsArray[i*factor].indexOf(MYEfolder_ID)!=-1){
        //folder
          fileFolderArray[i]=2;
        }
        else {
        //file
          fileFolderArray[i]=1;
        }
        if (rowsArray[i*factor].indexOf(MYElink_ID)!=-1){
        //link
          fileFolderArray[i]+=2;
        }
        if (searchStr=="" || rowsArray[i*factor+addition].match(new RegExp(searchStr, "i"))){
          contentvar+=contentRowPrinter(i,i*factor+addition);
        }
      }
    }
    contentvar+='</table>';
    window.frames['browserContentframe'].contenter('content', contentvar);
    setToLoading=false;
}

function contentRowPrinter(i,y){
    var contentvar='<tr id="browser_'+i+'"><td id="sel'+i+'" class="shrink" onClick="parent.selected('+i+');">';
    if (selArray.indexOf(i)!=-1){
      contentvar+='<button class="p1 w1 green"></button>';
    }
    else{
      contentvar+='<button class="p1 w1 default"></button>';
    }
    contentvar+='</td>';
    //contentvar+='<td class="shrink"><button class="p1 w1 default" onClick="parent.renameF('+i+');"><img src="/img/pen.gif" /></button></td>';
    if (firstRow==-1){
      firstRow=i;
    }
    visRowsArray.push(i);
    if (fileFolderArray[i]==2||fileFolderArray[i]==4){
    //folder
      realName=rowsArray[y].replace(MYEfolder_ID,"");
      if (fileFolderArray[i]==4){
        realName=realName.replace(MYElink_ID,"");
        contentvar+='<td class="transparent0 text" onClick="parent.goToPos('+i+');"><img src="/img/folder.gif" /><img src="/img/lnk.gif" />&nbsp;'+realName+'</td></tr>';
      }
      else{
        contentvar+='<td class="transparent0 text" onClick="parent.goToPos('+i+');"><img src="/img/folder.gif" />&nbsp;'+realName+'</td></tr>';
      }
    }
    else {
    //file
      if (fileFolderArray[i]==3){
        realName=rowsArray[y].replace(MYElink_ID,"");
        contentvar+='<td class="transparent1 text" onClick="parent.goToPos('+i+');"><img src="/img/lnk.gif" />&nbsp;'+realName+'</td></tr>';
      }
      else{
        contentvar+='<td class="transparent1 text" onClick="parent.goToPos('+i+');">'+rowsArray[y]+'</td></tr>';
      }
    }
    return contentvar;
}

function lastBrowserPos(anker){
  window.frames['browserContentframe'].location.href="browserContentframe.html#"+anker;
  //top.document.location.href="/index.html#top";
  //alert(anker);
}

function buttonPrint(what,onOff,data,cssButtonId){
  data=data||"";
  if (cssButtonId){
    buttonConf[what]=cssButtonId;
  }
  else{
    cssButtonId=buttonConf[what];
  }
  if (onOff==1){
    content='<button name="'+what+'B" class="'+cssButtonId+' green" onClick="actionF(\''+what+'\',1);">';
  }
  else{
    content='<button name="'+what+'B" class="'+cssButtonId+' default" onClick="actionF(\''+what+'\',0);">';
  }
  if (data!=""){
    content+=data+'</button>';
  }
  else{
    content+=top.getText("browser",what)+'</button>';
  }
  document.getElementById(what+'B').innerHTML=content;
}

function actionF(SelValue,SelButtonState){
  buttonPrint(SelValue,1);
  if (secoundBrowser==true){
    copyArray=parent.copyArray;
    cutActiv=parent.cutActiv;
    cutFolderPath=parent.cutFolderPath;
  }
  if (SelValue=="paste" || SelValue=="pasteSpecial" || SelValue=="createLinks" || SelValue=="newFolder"){
    if (advSearch){
      top.alertBox(top.getText("browserMessages","notInAdvancedSearch"),function(o){buttonPrint(SelValue,0);});
    }
    else{
      if (SelValue=="newFolder"){
        renameF(-1);
      }
      else if (copyArray.length==0){
        top.alertBox(top.getText("browserMessages","copyItems"),function(o){buttonPrint(SelValue,0);});
      }
      else{
        if (SelValue=="paste" || SelValue=="pasteSpecial"){
          if (cutActiv){
            buttonPrint('cut',0);
            if (secoundBrowser){
              parent.buttonPrint('cut',0);
            }
            else if (secoundBrowserActive){
              window.frames['browserframe2'].buttonPrint('cut',0);
            }
          }
          if (SelValue=="paste"){
            var pasteWait=false;
            if (top.recording){
              pasteWait=true;
            }
            pasteF("",pasteWait);
          }
          else{
            pasteSpecialF();
          }
        }
        else if (SelValue=="createLinks"){
          if (cutActiv){
            top.alertBox(top.getText("browserMessages","noCut"),function(o){buttonPrint(SelValue,0);});
          }
          else{
            pasteF("link",false);
          }
        }
      }
    }
  }
  else if(SelValue=="home"){
    if (omega.GetUserSetting({name:"homeFolder"})=="-"){
      changeHomeDirF(folderPath);
    }
    else{
      if (SelButtonState==1){
        changeHomeDirF(omega.GetUserSetting({name:"homeFolder"}));
      }
      else{
        openLocation(omega.GetUserSetting({name:"homeFolder"}));
      }
    }
  }
  else if (SelValue=="root"){
    goToPos(-2);
  }
  else{
    if (selArray.length>0){
      if (SelValue=="copy"){
        buttonPrint('cut',0);
        if (secoundBrowser==true){
          parent.buttonPrint('cut',0);
          parent.buttonPrint('copy',0);
        }
        else if (secoundBrowserActive==true){
          window.frames['browserframe2'].buttonPrint('cut',0);
          window.frames['browserframe2'].buttonPrint('copy',0);
        }
        copyF('copy',selArray);
      }
      else if (SelValue=="cut"){
        buttonPrint('copy',0);
        if (secoundBrowser==true){
          parent.buttonPrint('cut',0);
          parent.buttonPrint('copy',0);
        }
        else if (secoundBrowserActive==true){
          window.frames['browserframe2'].buttonPrint('cut',0);
          window.frames['browserframe2'].buttonPrint('copy',0);
        }
        copyF('cut',selArray);
      }
      else if (SelValue=="rename"){
        if (selArray.length>1){
          top.alertBox(top.getText("browserMessages","selectOnlyOne"),function(o){buttonPrint('rename',0);});
        }
        else{
          renameF(selArray[0]);
        }
      }
      else if (SelValue=="delete"){
        deleteF(selArray);
      }
      else if (SelValue=="openWith"){
        openWithF(selArray);
      }
      else if (SelValue=="properties"){
        propertiesF(selArray);
      }
      else{
        alert('"'+SelValue+'" is not defined!');
      }
    }
    else if (SelValue=="properties" && advSearch==false){
      if (folderPath==top.States["devices"][omega.deviceID]["browser"]["root"]){
        top.alertBox(top.getText('propertiesOf',0)+folderPath2+top.getText('propertiesOf',1),function(o){buttonPrint('properties',0);});
      }
      else{
        propertiesF([]);
      }
    }
    else {
      top.alertBox(top.getText("browserMessages","selectItems"),function(o){buttonPrint(SelValue,0);});
    }
  }
}

function openSecoundBrowser(){
  if (window.frames['browserframe2'].location.href!=document.location.href){
    window.frames['browserframe2'].location.href="browserframe.html";
  }
  $("#browserframe2C").show(omega.GetUserSetting({name:"effectTimePage",global:true}));
  document.getElementById('secoundBrowserB').innerHTML='<button class="p1 w1 default" onClick="closeSecoundBrowser();"><b>-</b></button>';
  secoundBrowserActive=true;
}

function closeSecoundBrowser(){
  $("#browserframe2C").hide(omega.GetUserSetting({name:"effectTimePage",global:true}));
  document.getElementById('secoundBrowserB').innerHTML='<button class="p1 w1 default" onClick="openSecoundBrowser();"><b>+</b></button>';
  secoundBrowserActive=false;
  window.frames['browserframe2'].buttonPrint('cut',0);
  window.frames['browserframe2'].buttonPrint('copy',0);
}

//-------------------------------------hideZeugStart-------------------------------------------------//

function menu(mode,hide){
  if (hide==0 && activeMode!=mode && activeMode!="none"){
    document.getElementById(activeMode+'B').innerHTML='<button class="p1 w2 default" onClick="menu(\''+activeMode+'\',0);">'+top.getText(activeMode,0)+'</button>';
    document.getElementById(activeMode).style.display = 'none';
    document.getElementById(mode+'B').innerHTML='<button class="p1 w2 green" onClick="menu(\''+mode+'\',1);">'+top.getText(mode,0)+'</button>';
    document.getElementById(mode).style.display='inline';
    activeMode=mode;
  }
  else{
    if (hide==0){
      $(document.getElementById(mode)).slideDown(omega.GetUserSetting({name:"effectTimeSlide",global:true}));
      document.getElementById(mode+'B').innerHTML='<button class="p1 w2 green" onClick="menu(\''+mode+'\',1);">'+top.getText(mode,0)+'</button>';
      activeMode=mode;
    }
    else{
      $(document.getElementById(mode)).slideUp(omega.GetUserSetting({name:"effectTimeSlide",global:true}));
      document.getElementById(mode+'B').innerHTML='<button class="p1 w2 default" onClick="menu(\''+mode+'\',0);">'+top.getText(mode,0)+'</button>';
      activeMode="none";
    }
  }
  if (mode=='navigation' && hide==0 && top.touchDevice==false){
    document.getElementById('textBoxTwo').focus();
  }
}

function blurBox(){
  document.getElementById('textBoxTwo').blur();
}

//-------------------------------------hideZeugEnd-------------------------------------------------//
//---------------------------------------searchStart-------------------------------------------//
function search(){
    var searchStr=String(document.getElementById('textBoxTwo').value.trim());
    searchStr=searchStr.replace(/\+/g, "\\+");
    searchStr=searchStr.replace(/\*/g, "\\*");
    if (searchStr==""){
      if(typeof autoBackOKTimeout != "undefined"){
        clearTimeout(autoBackOKTimeout);
      }
      autoBackOKTimeout=setTimeout("autoBackOK=1;",500);
    }
    else{
      autoBackOK=0;
    }
    if (advSearch==false){
      contentPrinter(1,0,folderData[folderPath]['browserlength'],searchStr);
    }
    else{
      contentPrinter(2,1,rowsArrayLength,searchStr);
    }
}

function searchReset(){
  document.getElementById('textBoxTwo').value="";
  search();
  if (advSearch==true){
    searchRecusReset();
  }
}

function KeyEnterHandlerTwo(event){
  switch(event.which){
    case  8: if (autoBackOK==1){goToPos(-1);}else{search();} break;
    case  13: if (visRowsArray.length==0){
                searchRecus();
              }
              else{
                var newTarget=firstRow;
                goToPos(newTarget); 
              } break;
    default: search(); break;
  }
  return false;
}

function searchRecus(){
  var searchStr=document.getElementById('textBoxTwo').value.trim();
  if (searchStr!=""){
    searchStr=searchStr.replace('"',"''");
    omega.Request({'method':'serachSubFolders','args':[myInstanceNr,searchStr],'callback':function(data){
      if (data==true){
        loading();
      }
      else{
        console.log("Error initiating search!");
      }
    }});
  }
}

function searchRecusReset(){
  advSearch=false;
  searchTargetLength=-1;
  bla2(true);
}

//---------------------------------------searchEnd-------------------------------------------//

omega.OnUpdate(function(ext){
  if (ext=="data" && typeof myInstanceNr!="undefined"){
    if (setToLoading && top.States["devices"][omega.deviceID]["browser"][myInstanceNr]["newSearchData"]==1){
      omega.Request({'method':'getBrowerSearchResult','args':[myInstanceNr],'callback':function(data){
        if (!data){
          console.log("Error getting search results!");
        }
        else{
          advSearch=true;
          dataOld=JSON.parse(data);
          browserLoad(dataOld);
        }
      }});
    }
    else if(advSearch==false && top.States["devices"][omega.deviceID]["browser"][myInstanceNr]["newData"]==1){
      //console.log("do reload");
      bla(true);
    }
  }
  if (secoundBrowser==false && secoundBrowserActive){
    window.frames['browserframe2'].omega.update(ext);
  }
});

omega.OnLoad(function(){
    if(typeof omega.GetUserSetting({name:"homeFolder"})=="undefined"){
      omega.SetUserSetting({name:"homeFolder",value:"-"});
    }
    document.getElementById('backB').innerHTML='<button class="p1 w1 default" onClick="goToPos(-1);"><img src="/img/left.gif"></button>';
    document.getElementById('upB').innerHTML='<button class="p1 w1 default" onClick="goToPos(-3);"><img src="/img/up.gif"></button>';
    menu('navigation',1);
    menu('fileOperations',1);
    menu('advanced',1);
    //document.getElementById('rootB').innerHTML='<button class="p1 w2 default" onClick="goToPos(-2);">'+top.getText('root',0)+'</button>';
    //buttonPrint('home',0,'','p1 w2');
    document.getElementById('closeWindowB').innerHTML='<button name="blabidi" class="p1 w2 default" onClick="omega.TriggerEvent({command:\'serverAltF4\'});">'+top.getText('closeWindow',0)+'</button>';
    document.getElementById('selectAllB').innerHTML='<button class="p1 w2 default" onClick="selAll();">'+top.getText('selectAll',0)+'</button>';
    document.getElementById('selectInvertB').innerHTML='<button class="p1 w2 default" onClick="selInv();">'+top.getText('selectInvert',0)+'</button>';
    document.getElementById('searchBox').innerHTML='<input name="searchBox" type="text" id="textBoxTwo" class="w4">';
    document.getElementById('textBoxTwo').onkeyup = KeyEnterHandlerTwo;
    document.getElementById('searchB').innerHTML='<button class="p1 w2 default" onClick="searchRecus();">'+top.getText('search',0)+'</button>';
    //document.getElementById('searchResetB').innerHTML='<button class="p1 w2 default" onClick="searchReset();">'+top.getText('reset',0)+'</button>';
    buttonPrint('newFolder',0,'','p1 w1');
    buttonPrint('copy',0,'','p1 w1');
    buttonPrint('cut',0,'','p1 w1');
    buttonPrint('paste',0,'','p1 w1');
    buttonPrint('delete',0,'','p1 w1 Cred Hred');
    buttonPrint('rename',0,'','p1 w1');
    buttonPrint('openWith',0,'','p1 w2');
    buttonPrint('createLinks',0,'','p1 w2');
    buttonPrint('pasteSpecial',0,'','p1 w2');
    buttonPrint('properties',0,'','p1 w2');
    if (secoundBrowser==false){
      document.getElementById('secoundBrowserB').innerHTML='<button class="p1 w1 default" onClick="openSecoundBrowser();"><b>+</b></button>';
    }
});
