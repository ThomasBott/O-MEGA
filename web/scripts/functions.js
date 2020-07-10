var fullscreenID;
var volumeOld="";
var buttonStates= {};//buttonStates[buttonID]["state"] gibt den status des buttons aus und buttonStates[buttonID]["value"] den wert
var buttonsArray = {};//buttonsArray[buttonID] gibt den button zuruek mit der entspechenden id
var allIndexDataGroupArray= {};//allIndexDataGroupArray[filesID(name)] gibt den status des templates aus
var lastActionTime=0;
var overload=2;
var sceneRecording=-1;
var sceneChoosen=-1;
var loadedFiles= [];//loadedFiles[i] ergaenzt files um dem loaded eintrag
var allFramesArray = [];//allFramesArray[i] beinhaltet die Namen aller frames
var openFramesArray= {};//openFramesArray[framename] gibt aus welche files id (ziffer) in einem bestimmten frame gerade geoeffnet ist
var choosenFramesetPageArray={};//choosenFramesetPageArray[fileID(name)] gibt aus welche files id (ziffer) in einem bestimmten frameset (name) gerade aktiv ist
var nextChoosenFramesetPageArray={};//nextChoosenFramesetPageArray[fileID(name)] gibt aus welche files id (ziffer) in einem bestimmten frameset (name) gerade geoeffnet wird/ als letztes geoefnet wurde.
var browserArray= [];//id (number) of all browser frames
var fullFullscreenEnabled=false;
var fullscreenEnabled=false;
var allFramesetsArray =[];//allFramesetsArray[i] beinhaltet die ids(name) aller Framsetpages
var recording=false;
var conditionMode=false;
var heartbeat;
var hashs={"scene":0,"sceneData":0,"buttons":0,"devices":0,"programs":0,"uniUpdate":0};
var hashmodes=["buttons","devices","programs","sceneData","scene"];
var lastCommandTimerThing;
var sceneRecordCondition;
var sceneRecordLable;
var browserInstanceNrs=[];
var browserInstanceNr= [];
var filesLoading=[];
var States={};
var toOpenFramesArray={};//toOpenFramesArray[framename] beinhaltet die id(ziffer) des neusten files das in einem bestimmten Frame geoeffnet wurde/wird
var dashGoer=false;
var dashEditing=false;
var sysName="CMD.";
var chooseFrameLoaded=false;
var topFrameLoaded=false;
var openPageHistory=[];
var omega={fileID:{"hide":{frames:window.frames},"-":{frames:window.frames}}};
var backHashCount={};
var dashReturnTimeout;

function getIP(){
  var tdata=window.location.href.split("/");
  tdata=tdata[2].split(":");
  return tdata[0];
}
var svIP=getIP();

function is_touch_device() {
  return (('ontouchstart' in window) || (navigator.msMaxTouchPoints > 0));
}

function is_msTouch_device() {
  return window.navigator.msPointerEnabled;
}

var touchDevice = is_touch_device();
var msTouchDevice = false;
if (touchDevice){
  msTouchDevice = is_msTouch_device();
}

var thisIP;
function registerClient(){
  $.post("/empty", JSON.stringify({"method":"RegisterClient"}), function(data){
      thisIP=data;
      console.log("client "+data+" registered!");
  });
}
registerClient();

function dateTransform(day,month,year){
  if (userSettings["language"]==1){
    return day+"."+month+"."+year;
  }
  else{
    return year+"/"+month+"/"+day;
  }
}

function convertActionText(data,dontReplaceBr){
  dontReplaceBr=dontReplaceBr||false;
  //console.log("convert:"+data);
  var parts=data[0];
  var tempText="";
  if (data[2]==2){
    try{
      parts=JSON.parse(parts);
    }
    catch(e){
      console.log("Could not convert:"+parts);
      return parts;
    }
    tempText=getText('else',0)+":";
  }
  else if(data[2]==1){
    try{
      parts=JSON.parse(parts);
    }
    catch(e){
      console.log("Could not convert:"+parts);
      return parts;
    }
    if (data[3]){
      tempText=data[3];
    }
    else{
      tempText=getText('if',0)+createConditionLableFromCode(parts)+":";
    }
  }
  else if(data[2]==0){
    try{
      parts=JSON.parse(parts);
    }
    catch(e){
      console.log("Could not convert:"+parts);
      return parts;
    }
    if (data[3]){
      tempText+=data[3];
    }
    else{
      if (parts["suffix"]==top.sysName+"buttons"){
        var buttonID=parts["payload"]["target"]
        var temp=buttonID.split("/");
        var target=getButtonTarget(buttonID);
        var stateData="";
        if (target[0]=="undefined"){
          stateData=target[1];
        }
        else{
          if (parts["payload"]["targetState"]){
            var tempstate=getText('statesCfg.json',parts["payload"]["targetState"]);
            if (tempstate=="undefined"){
              tempstate=parts["payload"]["targetState"];
            }
            if (typeof tempstate=="string"){
              if (!dontReplaceBr){
                tempstate=tempstate.replace(/<br>/g," ");
              }
              if (tempstate=="{value}"){
                tempstate=getText('statesCfg.json','[set]');
              }
            }
            stateData+=" "+tempstate;
          }
          if (typeof parts["payload"]["targetValue"]!="undefined"){
            for (var i=0; i<parts["payload"]["targetValue"].length; i++){
              if (parts["payload"]["targetValue"][i]){
                var tempstate=getText('statesCfg.json',parts["payload"]["targetValue"][i]);
                if (tempstate=="undefined"){
                  tempstate=parts["payload"]["targetValue"][i];
                }
                if (typeof tempstate=="string"){
                  if (!dontReplaceBr){
                    tempstate=tempstate.replace(/<br>/g," ");
                  }
                  /*if (tempstate.indexOf("{value}")!=-1 && parts["payload"]["targetValue"].length>=i){
                    i++;
                    tempstate=tempstate.replace("{value}",getText('statesCfg.json','[set]')+" "+parts["payload"]["targetValue"][i]);
                  }*/
                }
                stateData+=" "+tempstate;
              }
            }
          }
          if(target[0]!="macro"){
            var targetClassName=tryToResolveText(target[0]+".jsonnames",target[1],target[0]);
            if(targetClassName!="undefined"){
                tempText+=targetClassName+":";
                if (dontReplaceBr){
                  tempText+="<br>";
                }
            }
          }
          tempText+=getText("files.json"+temp[0],temp[1]+"/"+temp[2]);
          if (dontReplaceBr){
            tempText+="<br>";
          }
          else{
            tempText+=" ";
          }
        }
        tempText+=stateData;
      }
      else if (parts["suffix"]=="[wait]"){
        if (parts["payload"][0].length!=0){
          tempText+=getText("timerMode",2)+" "+getText("event",0)+" "+getText("or",0)+" ";
        }
        if (parts["payload"][1]=="0"){
          tempText+=getText("timerMode",parts["payload"][1])+" "+convertTime(parts["payload"][2],"seconds",1,true);
        }
        else{
          tempText+=getText("timerMode",parts["payload"][1])+" "+parts["payload"][2]+":"+parts["payload"][3]+":"+parts["payload"][4]+" "+getText("clock",0);
        }
      }
      else if(parts["suffix"]==top.sysName+"sceneOnOff"){
        if (typeof scenesFind[parts["payload"]["data"]]!="undefined"){
          var tempScenename=scenesIds[scenesFind[parts["payload"]["data"]]][1];
          if(tempScenename==""){
            tempScenename=getText('scene',0)+" "+(parts["payload"]["data"]+1);
          }
          var tempText1=getText('statesCfg.json',parts["payload"]["targetState"]);
          if (!dontReplaceBr && typeof tempstate=="string"){
            tempText1=tempText1.replace(/<br>/g," ");
          }
          tempText+=getText('scene',0)+":"
          if (dontReplaceBr){
            tempText+="<br>";
          }
          tempText+=tempScenename;
          if (dontReplaceBr){
            tempText+="<br>";
          }
          else{
            tempText+=" ";
          }
          tempText+=tempText1;
        }
        else{
          tempText+='<div class="Cred">->'+getText('broken',0)+'!<-</div>';
        }
      }
      else{
        var commandData=parts["suffix"].split(".");
        var targetClass=commandData[1];
        if (commandData[0]=="EXT"){
          targetClass=commandData[2];
        }
        /*if (parts["payload"]["target"]=="test"){
          parts["payload"]["target"]=parts["payload"]["data"];
          parts["payload"]["data"]="";
        }*/
        if(targetClass!="macro"){
            var targetClassName=tryToResolveText(targetClass+".jsonnames",parts["payload"]["target"],parts["payload"]["target"]);
            if(targetClassName!="undefined"){
              tempText+=targetClassName+":";
              if (dontReplaceBr){
                tempText+="<br>";
              }
            }
        }
        var stateData="";
        var tempstate=getText('statesCfg.json',parts["payload"]["targetState"]);
        if (tempstate=="undefined"){
          tempstate=parts["payload"]["targetState"];
        }
        if (typeof tempstate=="string"){
          if (!dontReplaceBr){
            tempstate=tempstate.replace(/<br>/g," ");
          }
          if (tempstate=="{value}"){
            tempstate=getText('statesCfg.json','[set]');
          }
        }
        stateData+=" "+tempstate;
        if (typeof parts["payload"]["targetValue"]!="undefined"){
          for (var i=0; i<parts["payload"]["targetValue"].length; i++){
            var tempstate=getText('statesCfg.json',parts["payload"]["targetValue"][i]);
            if (tempstate=="undefined"){
              tempstate=parts["payload"]["targetValue"][i];
            }
            if (!dontReplaceBr && typeof tempstate=="string"){
              tempstate=tempstate.replace(/<br>/g," ");
            }
            stateData+=" "+tempstate;
          }
        }
        tempText+=commandData[commandData.length-1];
        if (dontReplaceBr){
          tempText+="<br>";
        }
        else{
          tempText+=" ";
        }
        tempText+=stateData;
      }
    }
  }
  else if (data[2]==10){
    if (dontReplaceBr){
      tempText=getText("openPage",0)+":<br>"+top.getText('files.json',parts);
    }
    else{
      tempText=getText("openPage",0)+": "+top.getText('files.json',parts).replace(/<br>/g," ");
    }
  }
  else{
    tempText=data[0];
  }
  return tempText;
}

function tryToResolveText(key,target,onError){
  try{
    var tempVar=text[key][target];
    if (typeof tempVar=="undefined"){
      console.log(key+'/'+target+' is undefined, "'+target+'" will be used!');
      tempVar=target;
    }
    return tempVar;
  }
  catch(e){
    console.log(key+"/"+target+" does not exist!");
    return onError;
  }
}

function getButtonTarget(buttonID){
  var target=["undefined",'<div class="Cred">->'+getText('broken',0)+'!<-</div>'];
  try{
    var thisButton = buttonsArray[buttonID];
    target=thisButton[1].split("/");
    if (target[0]=="frontend"){
      target[0]="undefined";
    }
  }
  catch(e){
    alert(getText("referencedButtonNA",0));
  }
  return target;
}

function createConditionLableFromCode(parts){
  var tempText="";
  for (var j=-1; j<(parts.length-1); j+=4){
    var buttonID = parts[j+1];
    if (j!=-1){
      tempText+=" "+getText(parts[j].toLowerCase(),0);
    }
    if (buttonID=="None" && parts[j+2]=="PYTHON"){
      tempText+=" ("+JSON.parse(parts[j+3])+")";
    }
    else{
      var temp=buttonID.split("/");
      if (parts[j+2]=="PYTHON"){
        var target=getButtonTarget(buttonID);
        var targetClassName=tryToResolveText(target[0]+".jsonnames",target[1],target[0]);
        tempText+=" ";
        if(targetClassName!="macro" && targetClassName!="undefined"){
          tempText+=targetClassName+":";
        }
        tempText+=getText("files.json"+temp[0],temp[1]+"/"+temp[2]);
        tempText+=" ("+JSON.parse(parts[j+3])+")";
      }
      else{
        var status=parts[j+3];
        if (temp.length==3){
          var target=getButtonTarget(buttonID);
          var targetClassName=tryToResolveText(target[0]+".jsonnames",target[1],target[0]);
          tempText+=" ";
          if(targetClassName!="macro" && targetClassName!="undefined"){
            tempText+=targetClassName+":";
          }
          tempText+=getText("files.json"+temp[0],temp[1]+"/"+temp[2]);
          tempText+=getText('conditionNegation',parts[j+2]);
          var tempStatus=getText('statesCfg.json',status.replace(/=/g,"").replace(/#/g,"")).replace(/<br>/g," ");
          if (tempStatus=="undefined"){
            tempStatus=status;
          }
          if (status.substring(0,1)=="="){
            if (status.substring(1,2)=="#"){
              tempText+=' <font class="Cyellow">'+tempStatus+'</font>';
            }
            else{
              tempText+=' <font class="Cgreen">'+tempStatus+'</font>';
            }
          }
          else{
            tempText+=" "+tempStatus;
          }
        }
        else{
          tempText+=" "+buttonID;
          if (parts[j+2]=="IS"){
            tempText+=" ==";
            //tempText+=" "+top.getText('is',0);
          }
          else{
            tempText+=" !=";
            //tempText+=" "+top.getText('not',0);
          }
          tempText+=" "+status;
        }
      }
    }
  }
  return tempText;
}

var globalWindowWidth;
var globalWindowHeight;
function getGlobalWindowSize(){
  globalWindowWidth=parseInt($(window).width(),10);
  globalWindowHeight=parseInt($(window).height(),10);
  if (topFrameLoaded){
    top.frames['topframe'].logo();
  }
}
getGlobalWindowSize(1);

function calculateFilesize(size){
  var level = 0;
  while ((size/1000)>1){
      size=size/1024;
      level++;
  }
  size = Math.ceil(size*100)/100;
  return size+top.getText('fileSizeSuffix',level);
}


function rotgruen(status){
  status=status||"[?]";
  //status=status.toString();
  if (status.indexOf(":")==-1){
    if (typeof statesIDArray[status]=="undefined"){
      if(status.substring(0,1)=="#"){
        status=status.substring(1);
        return "<font class='Cyellow'>"+getText('statesCfg.jsonshort',status)+"</font>";
      }
      else{
        return "<font class='Cred'>!ERR</font>";
      }
    }
    else{
      return "<font style='color:"+states[statesIDArray[status]][1]+"'>"+getText('statesCfg.jsonshort',status)+"</font>";
    }
  }
  return "<font class='Cgreen'>"+status+"</font>";
}
//----------------------replaceUMLstart------------------------------//
function replaceuml(text,back) {
    back=back||false;
    var tpos=0;
    var tpos2=text.indexOf("<",tpos);
    var finalText="";
    for (var i=0; tpos2!=-1; i++){
      var tposEnd=text.indexOf(">",tpos2);
      if (tposEnd!=-1){
        if (back){
          finalText+=rereplaceumlTwo(text.substring(tpos,tpos2));
        }
        else{
          finalText+=replaceumlTwo(text.substring(tpos,tpos2));
        }
        finalText+=text.substring(tpos2,tposEnd);
        tpos=tposEnd;
      }
      else{
        break;
      }
      tpos2=text.indexOf("<",tpos);
    }
    if (back){
      finalText+=rereplaceumlTwo(text.substring(tpos));
    }
    else{
      finalText+=replaceumlTwo(text.substring(tpos));
    }
    return finalText;
}
    
function replaceumlTwo(text) {
    return text.replace(
      /&/g, "&amp;"
    ).replace(
      /Ä/g, "&Auml;"
    ).replace(
      /ä/g, "&auml;"
    ).replace(
      /Ö/g, "&Ouml;"
    ).replace(
      /ö/g, "&ouml;"
    ).replace(
      /Ü/g, "&Uuml;"
    ).replace(
      /ü/g, "&uuml;"
    ).replace(
      /ß/g, "&szlig;"
    ).replace(
      /é/g, "&eacute;"
    ).replace(
      /°/g, "&deg;"
    ).replace(
      / /g, "&nbsp;"
    ).replace(
      / /g, "&nbsp;"
    );
}

function rereplaceumlTwo(text) {
    return text.replace(
      /&amp;/g, "&"
    ).replace(
      /&Auml;/g, "Ä"
    ).replace(
      /&auml;/g, "ä"
    ).replace(
      /&Ouml;/g, "Ö"
    ).replace(
      /&ouml;/g, "ö"
    ).replace(
      /&Uuml;/g, "Ü"
    ).replace(
      /&uuml;/g, "ü"
    ).replace(
      /&szlig;/g, "ß"
    ).replace(
      /&eacute;/g, "é"
    ).replace(
      /&deg;/g, "°"
    ).replace(
      /&nbsp;/g, " "
    );
}
//----------------------replaceUMLend--------------------------------//
//--------------------musicPlayerStart-----------------------------//
var playingData;
var playingTitle;
var playingFileID;
var updateintervals={};

function actuallyPlayingUpdate(ext){
  //if (programStatesLoaded && deviceStatesLoaded){
    var primaryFilesIDs=[];
    for (var y=0; y<files.length; y++){
      var temp=files[y][2].split("/");
      var mode=temp[0];
      var id=temp[1];
      var type=false;
      if (mode=="devices"){
        type = devices[devicesIDArray[id]][1];
        if (id == primHifiID){
          primaryFilesIDs.push(y);
        }
      }
      else if (mode=="programs"){
        type = programs[programsIDArray[id]][1];
      }
      if (type){
        if (supportedAudioPlayer.indexOf(type)!=-1){
          window.clearInterval(updateintervals[id]);
          if ((States[mode][id]["play"]=="[on]" || States[mode][id]["play"]=="#[on]") && !(States[mode][id]["pause"]=="[on]" || States[mode][id]["pause"]=="#[on]")){
            updateintervals[id] = window.setInterval('PlayerUpdate(States["'+mode+'"]["'+id+'"],"'+type+'");',1000);
          }
        }
      }
    } 
    if (States["devices"][primHifiID]["input"]){
      if (hifiFileIDsPerInput[States["devices"][primHifiID]["input"]]){
        identifyActuallyPlaying(hifiFileIDsPerInput[States["devices"][primHifiID]["input"]]);
      }
      else{
        playingFileID=-1;
        top.frames['topframe'].document.getElementById('titleB').innerHTML='<button class="p1 w6 default" onClick="top.openPage(\''+files[filesTargetArray['devices/'+primHifiID][0]][0]+'\',false,top.fullscreenEnabled);">'+getText('actuallyPlaying',0)+':<br><font class="Cred">'+getText('input',0)+': '+States["devices"][primHifiID]["input"].replace(/<br>/g," ")+'</font></button>';
      }
    }
    else{
      identifyActuallyPlaying(primaryFilesIDs);
    }
  //}
}

function identifyActuallyPlaying(filesIDs){
  var parentFileID=-1;
  var tempPlayingFileID=-1;
  for (var i=0; i<filesIDs.length; i++){
    var y=filesIDs[i];
    if (parentFileID==-1 && (files[y][1]=="-" || files[y][1]=="hide")){
      parentFileID=y;
    }
    var temp=files[y][2].split("/");
    var mode=temp[0];
    var id=temp[1];
    var type1=false;
    if (mode=="devices"){
      type1 = devices[devicesIDArray[id]][1];
    }
    else if (mode=="programs"){
      type1 = programs[programsIDArray[id]][1];
    }
    if (type1){
      if (supportedAudioPlayer.indexOf(type1)!=-1){
        if (States[mode][id]["power"]!="[off]" && States[mode][id]["power"]!="#[off]" && (States[mode][id]["play"]=="[on]" || States[mode][id]["play"]=="#[on]") && States[mode][id]["pause"]!="[on]" && States[mode][id]["pause"]!="#[on]"){
          playingData=States[mode][id];
          tempPlayingFileID=y;
          //type=type1;
          break;
        }
      }
    }
  }
  if (tempPlayingFileID!=-1){
    if (tempPlayingFileID!=playingFileID || playingData["title"]!=playingTitle){
      playingFileID=tempPlayingFileID;
      playingTitle=playingData["title"];
      var tempContent='<button class="p1 w6 default" onClick="top.openPage(\''+files[playingFileID][0]+'\',false,top.fullscreenEnabled);">'+getText('actuallyPlaying',0)+':<br>';
      if (playingTitle.length>35){
        tempContent+='<marquee scrollamount="4" scrolldelay="100">'+playingTitle+'</marquee>';
      }
      else{
        tempContent+=playingTitle;
      }
      top.frames['topframe'].document.getElementById('titleB').innerHTML=tempContent+'</button>';
    }
  }
  else if (parentFileID!=-1){
    playingFileID=parentFileID;
    top.frames['topframe'].document.getElementById('titleB').innerHTML='<button class="p1 w6 default" onClick="top.openPage(\''+files[parentFileID][0]+'\',false,top.fullscreenEnabled);">'+getText('actuallyPlaying',0)+':<br><font class="Cred">'+top.getText('files.json',files[parentFileID][0]).replace(/<br>/g," ")+'</font></button>';
  }
}

function actuallyPlayingUpdate2(type){
  top.frames['topframe'].document.getElementById('showtime').innerHTML = '&nbsp;'+convertTime(playingData["over"])+'&nbsp;/&nbsp;'+convertTime(playingData["total"]);
}

function PlayerUpdate(obj,type){
  obj["over"]++;
}

function convertTime(data,mode,multi,text){
  mode=mode||"minutes";
  multi=multi||1;
  text=text||false;
  var result;
  var resulttext;
  if (mode=="seconds" && parseInt(data*multi,10)<60){
    result=parseInt(data*multi,10);
    resulttext=top.getText('timeFormat',0);
  }
  else{
    var tempTimeMin=parseInt(data/(multi * 60),10);
    var tempTimeSec=Math.round(data%(multi * 60)/multi);
    var tempTimeHour=parseInt(tempTimeMin/60,10);
    if (mode=="days" || tempTimeHour>23){
      var tempTimeDays=parseInt(tempTimeHour/24,10)
      tempTimeMin=tempTimeMin%60;
      tempTimeHour=tempTimeHour%24;
      result=tempTimeDays+":"+addZeroToTime(tempTimeHour)+":"+addZeroToTime(tempTimeMin)+":"+addZeroToTime(tempTimeSec);
      resulttext=top.getText('timeFormat',3);
    }
    else if (mode=="hours" || tempTimeMin>59){
      tempTimeHour=parseInt(tempTimeMin/60,10);
      tempTimeMin=tempTimeMin%60;
      result=tempTimeHour+":"+addZeroToTime(tempTimeMin)+":"+addZeroToTime(tempTimeSec);
      resulttext=top.getText('timeFormat',2);
    }
    else{
      result=tempTimeMin+":"+addZeroToTime(tempTimeSec);
      resulttext=top.getText('timeFormat',1);
    }
  }
  if (text){
    return result+" "+resulttext;
  }
  else{
    return result;
  }
}

//--------------------musicPlayerEnd-----------------------------//
//---------------------index2frametopOldstart---------------------//

function vole(ext){
  if (deviceStatesLoaded){
    if (typeof filesTargetArray["devices/"+primHifiID]!="undefined"){
        var hifivol=States["devices"][primHifiID]["volume"];
        var hifimute=States["devices"][primHifiID]["mute"];
        var hifistate=allIndexDataGroupArray[files[filesTargetArray["devices/"+primHifiID][0]][0]];
        if (volumeOld!=hifivol+hifistate+hifimute || ext=="load"){
          volumeOld=hifivol+hifistate+hifimute;
          if (hifimute=="[on]"){
            top.frames['topframe'].document.getElementById('volume').innerHTML =getText('volume',0)+':<br><font class="Cred" class="blinking">'+top.getText('mute',0).toUpperCase()+'</font>';
          }
          else if (hifistate=="[off]"||hifistate=="[error]"){
            top.frames['topframe'].document.getElementById('volume').innerHTML =getText('volume',0)+':<br><font class="Cred">'+top.getText('statesCfg.json',hifistate)+'</font>';
          }
          else{
            top.frames['topframe'].document.getElementById('volume').innerHTML =getText('volume',0)+':<br>'+hifivol;
          }
        }
    }
  }
}

function addZeroToTime(number){
  if (number<10){
    number="0"+number;
  }
  return ""+number;
}


function indexReload(ext){
  if (deviceStatesLoaded){
    top.frames['chooseframe'].omega.update(ext);
    top.frames['topframe'].dashButton();
  }
}

function reloadF(ext){
  ext=ext||"std";
  allBrowserLoad();
  dataUpdate(ext);
  if (ext=="reload"){
    actuallyPlayingUpdate(ext);
    calculatePageStates();
    indexReload(ext);
    vole(ext);
    if (touchDevice && !fullFullscreenEnabled && top.userSettings["useFullscreen"]){
      fullFullscreen(1);
      setTimeout('getGlobalWindowSize();',400);
    }
    top.frames['chooseframe'].timeUpdate();
    resetDashReturnTimeout();
  }
}

function allBrowserLoad(){
  for(var i in browserArray){
    if (loadedFiles[browserArray[i]]){
      omega.fileID[files[browserArray[i]][0]].bla2(true,false);
    }
  }
}


var programStatesLoaded=false;
var deviceStatesLoaded=false;
var uniHashs={}

function dataUpdate(ext){
  clearTimeout(heartbeat);
  heartbeat=setTimeout("dataUpdate('std');",30000);
  if (ext=="reload"){
    hashs={"scene":0,"sceneData":0,"buttons":0,"devices":0,"programs":0,"uniUpdate":0};
  }
  $.ajax({
    type: "POST",
    url: "/empty",
    timeout: 30000,
    cache: false,
    data: JSON.stringify({"method":"dataUpdate","args":[JSON.stringify(hashs),JSON.stringify(uniHashs),thisIP]})
  })
  .fail(function(data) {
    console.log("data update failed (maybe the page has been reloaded)");
  })
  .done(function(data) {
    if (data==false){
      console.log("data update error!");
    }
    else if (data!=null){//null means long polling already started
      data=JSON.parse(data);
      //console.log(data);
      hashData=data[0];
      hashs["uniUpdate"]=hashData["uniUpdate"];
      uniData=data[1];
      for (var y=0; y<uniData.length; y++){
        unidataOld[uniData[y][0]]=uniData[y][1];
        uniHashs[uniData[y][0]]=uniData[y][2];
        for (var i=uniTasks[uniData[y][0]].length-1; i>=0; i--){
          var id=uniTasks[uniData[y][0]][i][0];
          var targetFunction=uniTasks[uniData[y][0]][i][2];
          if (loadedFiles[filesIDArray[id]]){
            uniFinishData(id,targetFunction,uniData[y][1]);
          }
          else{
            uniTasks[uniData[y][0]].splice(i,1)
            if (uniTasks[uniData[y][0]].length==0){
              uniUnregister(uniData[y][0]);
            }
          }
        }
      }
      for (var j=0; j<hashmodes.length; j++){
        var mode=hashmodes[j];
        if (hashData[mode]!=hashs[mode]){
          $.post("/empty",JSON.stringify({"method":"dataUpdate2","args":[mode]}),dataUpdate2(mode));
          hashs[mode]=hashData[mode];
        }
      }
      dataUpdate('std');
    }
  });
}


var scenesFind={};
var scenesFindData={};
var scenesIds=[];
var scenes;

function dataUpdate2(mode){
  return function(data){
    data=JSON.parse(data);
    if (mode=="buttons"){
      buttonStates=data;
      calculatePageStates();
      indexReload('data');
      //vole('std');
    }
    else if(mode=="scene"){
      scenesIds=data;
      scenesFind={};
      for (var i=0; i<scenesIds.length; i++){
        scenesFind[scenesIds[i][0]]=i;
      }
      //if (chooseFrameLoaded){
        top.frames['chooseframe'].sceneLoad('data');
      //}
    }
    else if(mode=="sceneData"){
      scenes=JSON.parse(data[0]);
      scenesFindData={};
      for (var i=0; i<scenes.length; i++){
        if (scenes[i][1].substring(0,5)=="scene"){
          var tempId=scenes[i][1].substr(5);
          scenesFindData[tempId]=i;
        }
      }
      for (var i=0; i<scenesIds.length; i++){
        var tempId=scenesIds[i][0];
        if (typeof scenesFindData[tempId]=="undefined"){
          //sceneRemove(true,tempId); //better clean in backend, here it causes errors
          console.log("scene"+tempId+" is broken!");
          scenesIds.splice(i,1);
          i--;
        }
      }
      scenesNextRunTime=JSON.parse(data[1]);
      //if (chooseFrameLoaded){
        top.frames['chooseframe'].sceneLoad('data');
      //}
    }
    else if(mode=="devices"){
      States["devices"]=data;
      deviceStatesLoaded=true;
      if(programStatesLoaded){ 
        actuallyPlayingUpdate('std');//must be before index load
      }
      indexReload('data');
      vole('std');
    }
    else if(mode=="programs"){
      States["programs"]=data;
      programStatesLoaded=true;
      if(deviceStatesLoaded){
        actuallyPlayingUpdate('std');//must be before index load
      }
      indexReload('data');
    }
  }
}

function calculatePageStates(){
  for (var y=0; y<files.length; y++){
    if (viewChoosen=="-" || files[y][10].indexOf(viewChoosen)!=-1){
      var tempState="[none]";
      var tempLevel=-1;
      var buttons=files[y][5];
      for (var bid in buttons){
        var thisButton=buttons[bid];
        if (viewChoosen=="-" || !buttonViewsForPage[files[y][0]] || typeof thisButton[9]!="undefined" && thisButton[9].indexOf(viewChoosen)!=-1){
          var buttonid=files[y][0]+"/"+thisButton[0];
          var buttonid1=buttonid;
          var copy=false;
          if (thisButton[1]=="macro" && thisButton[2]=="copy" && typeof thisButton[5]["buttonID"]!="undefined"){
            buttonid=thisButton[5]["buttonID"];
            thisButton=buttonsArray[buttonid];
            copy=true;
          }
          if (thisButton[2]=="power" && $.isEmptyObject(thisButton[6]) && typeof buttonStates[thisButton[1]+"/"+thisButton[2]]!="undefined"){
            buttonStates[buttonid]=buttonStates[thisButton[1]+"/"+thisButton[2]];
          }
          if (thisButton[8]==1 && (!$.isEmptyObject(thisButton[6])|| thisButton[2]=="power") && (parseInt(thisButton[3][0],10)==0 || parseInt(thisButton[3][0],10)==-10)){
            var tempState1;
            var tempState2;
            var tempYellow=false;
            if (typeof buttonStates[buttonid]=="undefined"){
              tempState1="[none]";
              tempState2=tempState1;
            }
            else{
              tempState1=buttonStates[buttonid]["state"];
              tempState2=tempState1;
              if (typeof statesIDArray[tempState1]=="undefined"){ 
                if (tempState1.substring(0,1)=="#"){
                  tempState1=tempState1.substring(1);
                  tempYellow=true;
                }
                else{
                  tempState1="[?]";
                }
              }
              if (copy){
                tempState2="[none]";
                var tempButton=buttonsArray[buttonid1];
                for (var j=0; j<tempButton[4].length; j++){
                  if (tempButton[5][tempButton[4][j]][0]==tempState1){
                    tempState1=tempButton[4][j];
                    tempState2=tempState1;
                    if (tempYellow){
                      tempState2="#"+tempState2;
                    }
                    break;
                  }
                }
              }
            }
            if (tempLevel==-1 || tempLevel>statesIDArray[tempState1] || tempLevel==statesIDArray[tempState1] && tempYellow && states[statesIDArray[tempState1]][2]==1){
              tempState=tempState2;
              tempLevel=statesIDArray[tempState1];
              if (tempYellow){
                if(states[statesIDArray[tempState1]][2]==0){
                  tempLevel+=0.5;
                }
                else{
                  tempLevel-=0.5;
                }
              }
            }
          }
        }
      }
      allIndexDataGroupArray[files[y][0]]=tempState;
    }
  }
}

function uniFinishData(id,targetFunction,data){
  //console.log(data);
  targetFunction(JSON.parse(data));
}

function uniUnregister(varInBackend){
  //console.log("unregister "+varInBackend);
  $.ajax({
    type: "POST",
    url: "/empty",
    cache: false,
    data: JSON.stringify({"method":"uniUnregister","args":[top.thisIP,varInBackend]})
  })
  .fail(function(data) {
    console.log("unregister failed");
  })
  delete uniHashs[varInBackend];
}

var unidataOld={};
var uniTasks={};

function uniUpdate(id,varInBackend,targetFunctionName,targetFunction){
  if (typeof uniTasks[varInBackend] == "undefined" ){
    uniTasks[varInBackend]=[[id,targetFunctionName,targetFunction]];
  }
  else if (uniTasks[varInBackend].indexOf([id,targetFunctionName])==-1){
    uniTasks[varInBackend].push([id,targetFunctionName,targetFunction]);
  }
  if (typeof unidataOld[varInBackend] == "undefined"){
    unidataOld[varInBackend]='""';
  }
  else{
    uniFinishData(id,targetFunction,unidataOld[varInBackend]);
  }
  $.ajax({
    type: "POST",
    url: "/empty",
    cache: false,
    data: JSON.stringify({"method":"uniUpdate","args":[top.thisIP,varInBackend]})
  })
  .fail(function(data) {
    console.log("updated failed");
  })
}

function sceneRemove(state,nr){
  if(state){
    if(!user["parameters"]["isSceneEditor"] || scenesIds[nr][7]==1){
      console.log("Cannot delete scene, Access Denied!");
      return false;
    }
    if (files[choosenFramesetPageArray['index']][0]=="scene" && sceneChoosen==nr){
      openPage('dashboard');
    }
    if (recording && sceneRecording==nr){
      sceneRecordEnd(false,false);
    }
    var command=JSON.stringify({"method":"sceneRemove","args":[nr]});
    $.post("/empty",command);
  }
}

function sceneMetadata(i){
    var tempId=scenesFindData[i];
    var tempVarInfo="";
    var tempVarDays="";
    var tempVarWeeks="";
    var tempVarMonths="";
    var tempVarDate="";
    switch (scenes[tempId][2]){
      case 0: //only once or yearly
        var tempArr=scenes[tempId][3][2].split("-");
        if (scenes[tempId][3][3]==1){//yearly
          tempVarInfo='yearly';
          tempVarDate=dateTransform(tempArr[2],tempArr[1]);
        }
        else{ //only once
          tempVarInfo='once';
          tempVarDate=dateTransform(tempArr[2],tempArr[1],tempArr[0]);
        }
        break;
      case 1: //daily
        tempVarInfo='daily';
        break;
      case 2: //weekly
        tempVarInfo='weekly';
        var value=scenes[tempId][3][2].toString(2);
        var tempArr=sceneCalculateDaysMonths(value);
        for (var o=0; o<tempArr.length; o++){
          var o2=Math.pow(2,(tempArr[o]-1));
          tempArr[o]=top.getText("days",o2);
        }
        tempVarDays=tempArr.join();
        break;
      case 3: //monthly-weekday
        tempVarInfo='monthly';
        var value=(scenes[tempId][3][4]+64*scenes[tempId][3][5]).toString(2);
        var tempArr=sceneCalculateDaysMonths(value);
        for (var o=0; o<tempArr.length; o++){
          var o2=Math.pow(2,(tempArr[o]-1));
          tempArr[o]=top.getText("months",o2);
        }
        tempVarMonths=tempArr.join();
        var value=scenes[tempId][3][2].toString(2);
        var tempArr=sceneCalculateDaysMonths(value);
        for (var o=0; o<tempArr.length; o++){
          var o2=Math.pow(2,(tempArr[o]-1));
          tempArr[o]=top.getText("weeks",o2);
        }
        tempVarWeeks=tempArr.join();
        var value=scenes[tempId][3][3].toString(2);
        var tempArr=sceneCalculateDaysMonths(value);
        for (var o=0; o<tempArr.length; o++){
          var o2=Math.pow(2,(tempArr[o]-1));
          tempArr[o]=top.getText("days",o2);
        }
        tempVarDays=tempArr.join();
        break;
      case 4: //monthly-days        
        tempVarInfo='monthly';
        var value=(scenes[tempId][3][6]+64*scenes[tempId][3][7]).toString(2);
        var tempArr=sceneCalculateDaysMonths(value);
        for (var o=0; o<tempArr.length; o++){
          var o2=Math.pow(2,(tempArr[o]-1));
          tempArr[o]=top.getText("months",o2);
        }
        tempVarMonths=tempArr.join();
        var value=(scenes[tempId][3][2]+256*scenes[tempId][3][3]+65536*scenes[tempId][3][4]+16777216*scenes[tempId][3][5]).toString(2);
        tempVarDays=sceneCalculateDaysMonths(value).join();
        break;
      case 5: //periodically
        tempVarInfo=top.getText('every',1)+" "+scenes[tempId][3][3]+" "+top.getText('timeFormat',scenes[tempId][3][4]);
        break;
      default: //time span
        tempVarInfo=top.getText('unknown',0);
    }
    //console.log(new Array(tempVarInfo, tempVarDays, tempVarWeeks, tempVarMonths, tempVarDate));
    return [tempVarInfo, tempVarDays, tempVarWeeks, tempVarMonths, tempVarDate];
}

function sceneCalculateDaysMonths(value){
  var tempArr=[];
  var j=0;
  for (var o=value.length; o>0; o--){
    j++;
    if(value.substring(o-1,o)=="1"){
      tempArr.push(j);
    }
  }
  return tempArr;
}
//---------------------index2frametopOldEnd------------------------//
//---------------------hifiStart---------------------------------//
var hifiUsedInputs=[];
var hifiFileIDsPerInput={};

function hifiInit(){
  //hifiInputsIDArray= [];
  hifiFileIDsPerInput={};
  //for (var i=0; i<hifiInputs.length; i++){
  //  hifiInputsIDArray[hifiInputs[i][1]]=i;
  //}
  hifiUsedInputs=[];
  for (var i=0; i<files.length; i++){
    if (typeof files[i][4][primHifiID]!="undefined"){
      if (typeof files[i][4][primHifiID]!="object" ){
        files[i][4][primHifiID]=files[i][4][primHifiID].split(",");
      }
      for (var j=0;j<files[i][4][primHifiID].length;j++){
        if (files[i][1]=="-"){ 
          hifiUsedInputs.push(files[i][4][primHifiID][j]);
        }
        if (typeof hifiFileIDsPerInput[files[i][4][primHifiID][j]]=="undefined"){
          hifiFileIDsPerInput[files[i][4][primHifiID][j]]=[];
        }
        hifiFileIDsPerInput[files[i][4][primHifiID][j]].push(i);
      }
    }
  }
}
//----------------------hifiEnd-------------------------------//
//---------------------OpenPageStart-------------------------------//
var filesIDArray = {};
var filesTargetArray={};
var openPageRunning=false;
var openPageTimer;
var openPageMainCall=[];
var framesArrayPointer=-1;
var buttonViewsForPage={};

function openPageInit(){
	for (var i=0; i<files.length; i++){
        filesIDArray[files[i][0]]=i;
        if (typeof filesTargetArray[files[i][2]]=="undefined"){
          filesTargetArray[files[i][2]] = [];
        }
        filesTargetArray[files[i][2]].push(i);
        if (files[i][5]==""){
          files[i][5]={};
        }
        else{
          try{
            files[i][5]=JSON.parse(files[i][5]);
            var buttons=files[i][5];
            buttonViewsForPage[files[i][0]]=false;
            for (var j=0; j<buttons.length; j++){
              var thisButton=buttons[j];
              if (!buttonViewsForPage[files[i][0]] && typeof thisButton[9]!="undefined" && thisButton[9][0]!=""){
                buttonViewsForPage[files[i][0]]=true;
              }
              if (thisButton[5]==""){
                thisButton[5]={};
              }
              else{
                try{
                  thisButton[5]=JSON.parse(thisButton[5]);
                }
                catch(e){
                  console.log(e);
                  thisButton[5]={};
                }
              }
              if (thisButton[6]==""){
                thisButton[6]={};
              }
              else{
                try{
                  thisButton[6]=JSON.parse(thisButton[6]);
                }
                catch(e){
                  console.log(e);
                  thisButton[6]={};
                }
              }
              if (thisButton[7]==""){
                thisButton[7]={};
              }
              else{
                try{
                  thisButton[7]=JSON.parse(thisButton[7]);
                }
                catch(e){
                  console.log(e);
                  thisButton[7]={};
                }
              }
              buttonsArray[files[i][0]+"/"+thisButton[0]]=thisButton;
            }
          }
          catch(e){
            console.log(files[i][0]);
            console.log(e);
            files[i][5]={};
          }
        }
        if (files[i][4]==""){
          files[i][4]={}
        }
        else{
          try{
            files[i][4]=JSON.parse(files[i][4]);
          }
          catch(e){
            console.log(e);
            files[i][4]={};
          }
        }
        if(files[i][0].substring(files[i][0].length-7)=="browser"){
          browserArray.push(i);
        }
        if (allFramesArray.indexOf(files[i][6])==-1){
          allFramesArray.push(files[i][6]);
          openFramesArray[files[i][6]]=-1;
        }
        if (files[i][9]===1){
          loadedFiles[i]=true;
          if(files[i][3].substr(0,1)=="/"){
            filesLoading[i]=true;
          }
          else{
            filesLoading[i]=false;
          }
        }
        else{
          loadedFiles[i]=false;
        }
        var indexID;
        if (files[i][1]=="-" || files[i][1]=="hide"){
          indexID="index";
        }
        else{
          indexID=files[i][1];
        }
        if (allFramesetsArray.indexOf(indexID)==-1){
          allFramesetsArray.push(indexID);
          openFramesArray[files[i][6]]=i;
          toOpenFramesArray[files[i][6]]=i;
          choosenFramesetPageArray[indexID]=i;
          nextChoosenFramesetPageArray[indexID]=i;
        }
	}
}

function pageOpened(frameID,pageOmega){
  if (typeof pageOmega!="undefined"){
    omega.fileID[frameID]=pageOmega;
    pageOmega.advancedPageNumber=openPageMainCall[2];
    console.log("loaded: "+frameID);
  }
  else if (files[filesIDArray[frameID]][3].substr(0,1)=="/"){//only internal pages
    omega.fileID[frameID].advancedPageNumber=openPageMainCall[2];
  }
  loadedFiles[filesIDArray[frameID]]=true;
  openFramesArray[files[filesIDArray[frameID]][6]]=filesIDArray[frameID];
  if (files[filesIDArray[frameID]][1]=="-" || files[filesIDArray[frameID]][1]=="hide"){
    indexID="index";
  }
  else{
    indexID=files[filesIDArray[frameID]][1];
  }
  filesLoading[filesIDArray[frameID]]=false;
  if (framesArray.indexOf(filesIDArray[frameID])!=-1){
    choosenFramesetPageArray[indexID]=filesIDArray[frameID];
    nextChoosenFramesetPageArray[indexID]=filesIDArray[frameID];
    framesArrayPointer--;
    if (frameID=="scene" || frameID=="dashboard"){
      top.frames['chooseframe'].sceneLoad('load');
    }
    if (framesArrayPointer>-1){
      overload=0;
      openPage2(framesArray[framesArrayPointer]);
    }
    else{
      if (overload>0){
        console.log("overload: "+overload+":"+frameID);
      }
      overload++;
      if (frameID=="dashboard"){
        //$(document.getElementById(files[choosenFramesetPageArray['index']][6])).show(0,function(){$(document.getElementById("dummyC")).hide(0,function(){openPageRunning=false;});});
        $(document.getElementById(files[choosenFramesetPageArray['index']][6])).show(0,function(){$(document.getElementById("dummyC")).hide(0);});
      }
      else{
        //$(document.getElementById(files[choosenFramesetPageArray['index']][6])).animate({width:"show",opacity:"show"},top.userSettings["effectTimePage"],"swing",function(){$(document.getElementById("dummyC")).hide(0,function(){openPageRunning=false;});});
        $(document.getElementById(files[choosenFramesetPageArray['index']][6])).animate({width:"show",opacity:"show"},top.userSettings["effectTimePage"],"swing",function(){$(document.getElementById("dummyC")).hide(0);});
      }
      clearTimeout(openPageTimer);
      openPageRunning=false;
      indexReload('load');
      resetDashReturnTimeout();
    }
  }
}

function openPage(frameID,donotclear,goFullScreen,record,number,ext){
  //console.log([frameID,donotclear,goFullScreen,record,number]);
  donotclear=donotclear||false;
  goFullScreen=goFullScreen||false;
  ext=ext||"load";
  if (typeof record!="boolean"){
    if (frameID=="back"){
      record=false;
    }
    else{
      record=true;
    }
  }
  if (typeof number!="number"){
    number=-1;
  }
  if (openPageRunning){
    console.log("Another openPage action is running, please wait...");
    setTimeout('openPage("'+frameID+'",'+donotclear+','+goFullScreen+','+record+','+number+',"'+ext+'");',200);
  }
  else{
    //if (dashEditing && dashGoer==false && frameID!="dashboard" && record){
    //  dashAddBox(10,frameID,false,true,number);
    //}
    //else{
      if (frameID=="back"){
        goFullScreen=false;
        var tempInitFrameID;
        if (openPageHistory.length>1){
          if (openPageHistory[0][0]=="fullscreen" || openPageHistory[1][0]=="fullscreen"){
            if (openPageHistory[0][0]=="fullscreen"){
              openPageHistory.shift();
            }
            else{
              openPageHistory.splice(1,1);
            }
            if (fullscreenEnabled){
              fullscreen(0);
              if (number!=-2){
                return true;
              }
              //goFullScreen=false;
            }
            else{
              if (openPageHistory.length>1){
                openPageHistory.shift();
              }
            }
            tempInitFrameID=openPageHistory[0][2];
          }
          else if(openPageHistory[0][0]=="activePage" || openPageHistory[1][0]=="activePage"){
            if (openPageHistory[0][0]=="activePage"){
              tempInitFrameID=openPageHistory[0][2];
              openPageHistory.shift();
            }
            else{
              tempInitFrameID=openPageHistory[1][2];
              openPageHistory.splice(1,1);
            }
            goFullScreen=true;
          }
          else if(openPageHistory[0][0]=="viewChanged" || openPageHistory[1][0]=="viewChanged"){
            if (openPageHistory[0][0]=="viewChanged"){
              top.frames['topframe'].selectView(openPageHistory[0][1],true);
              openPageHistory.shift();
            }
            else{
              top.frames['topframe'].selectView(openPageHistory[1][1],true);
              openPageHistory.splice(1,1);
            }
            if (number!=-2){
              return true;
            }
            tempInitFrameID=openPageHistory[0][2];
          }
          else{
            openPageHistory.shift();
            tempInitFrameID=openPageHistory[0][2];
          }
        }
        console.log(openPageHistory.length + " " + openPageHistory[0]);
        frameID=openPageHistory[0][0];
        number=openPageHistory[0][1];
        //console.log("back to "+frameID);
        openPageMainCall=[filesIDArray[tempInitFrameID],goFullScreen,number,ext];
      }
      else{
        var tempInitFrameID=frameID;
        openPageMainCall=[filesIDArray[frameID],goFullScreen,number,ext];
        while (typeof choosenFramesetPageArray[frameID]!="undefined"){
          frameID=files[choosenFramesetPageArray[frameID]][0];
        }
        if (openPageHistory.length==0 || frameID!=openPageHistory[0][0] || number!=openPageHistory[0][1]){
          openPageHistory.unshift([frameID,number,tempInitFrameID]);
        }
      }
      //window.focus();
      window.blur();
      clearTimeout(openPageTimer);
      openPageRunning=true;
      //console.log(frameID+" "+record+" "+number);
      //console.log(openPageHistory);
      dashGoer=false;
      var i=filesIDArray[frameID];
      //openPageMainCall=[i,goFullScreen,number];
      framesArray = [i];
      framesArray2 = [files[i][6]];
      var x=i;
      while (files[x][1]!='-' && files[x][1]!='hide'){
        var z=filesIDArray[files[x][1]];
        framesArray.push(z);
        framesArray2.push(files[z][6]);
        x=z;
      }
      i=x;
      if (blankSubPages(i,donotclear)){
        openPageTimer=setTimeout("openPageRunning=false;",5000);
        framesArrayPointer=framesArray.length-1;
        //console.log(files[i][0]+":  newframe: "+files[i][6]+" ; parent: "+files[i][1]+" ; choosenframe: "+files[choosenFramesetPageArray['index']][6]+" ; newpage: "+i+" ; choosenPage: "+choosenFramesetPageArray['index']);
        if (files[i][6]=='default'||files[choosenFramesetPageArray['index']][6]!=files[i][6]){
          if (choosenFramesetPageArray['index']!=i){
            $(document.getElementById("dummyC")).show();
            $(document.getElementById("allframeC")).hide();
            $(document.getElementById(files[choosenFramesetPageArray['index']][6])).hide();
            //console.log("frame should be hidden: "+files[choosenFramesetPageArray['index']][6]);
          }
        }
        overload=0;
        openPage2(i);
      }
      else{
        openPageRunning=false;
      }
    //}
  }
}
function openPage2(i){
	//console.log(files[i][0]+" + "+files[i][6]);
  if (files[i][0]=="scene" && openPageMainCall[2]>-1){
    sceneChoosen=parseInt(openPageMainCall[2]);
  }
  var openSkip=false;
  //console.log(openFramesArray[files[i][6]]+" = "+i+" & "+loadedFiles[i]);
  if (openFramesArray[files[i][6]]==i&&(loadedFiles[i]||filesLoading[i])&&files[i][8]===0&&(files[i][3].substr(0,1)=="/"||openPageMainCall[3]!="reload")){
    openSkip=true;
  }
  if ((files[i][1]!="-"&&files[i][1]!="hide")&&(loadedFiles[i]==false||choosenFramesetPageArray[files[i][1]]!=i)){
    //console.log("hide because: loaded:"+loadedFiles[i]+" choosen:"+choosenFramesetPageArray[files[i][1]]+" new:"+i);
    //eval(callStr2+".omega.hideActualFrame();");
    omega.fileID[files[i][1]].hideActualFrame();
  }
  if(openSkip){
    //console.log('no');
    pageOpened(files[i][0]);
  }
  else{
	//console.log('jo');
    if (files[i][3]!=""){
      var tempUrl=files[i][3];
      if (files[i][2]!="-"){
        tempUrl=replaceVariableInText(files[i][3],files[i][2]);
      }
      filesLoading[i]=true;
      if (files[i][1]=="-" || files[i][1]=="hide"){
        nextChoosenFramesetPageArray["index"]=i;
      }
      else{
        nextChoosenFramesetPageArray[files[i][1]]=i;
      }
      backHashCount[files[i][0]]=0;
      //omega.fileID[files[i][1]].frames[files[i][6]].location.href=tempUrl;//for firefox to deactivate the back button
      omega.fileID[files[i][1]].frames[files[i][6]].location.href=tempUrl;
      if (files[i][3].substr(0,1)!="/"){//external pages only
        pageOpened(files[i][0]);
      }
    }
    toOpenFramesArray[files[i][6]]=i;
  }
  if (openPageMainCall[0]==i){
    var goFullScreen = openPageMainCall[1];
    //console.log([files[i][0],goFullScreen]);
    if (goFullScreen){
      fullscreen(2,files[i][0]);
    }
  }
}
function blankSubPages(i,donotclear){
  if (!donotclear){
    for (var k=0;k<allFramesArray.length;k++){
      var fileId=openFramesArray[allFramesArray[k]];
      if (fileId!=-1&&typeof omega.fileID[files[fileId][1]]!="undefined"){
        if (typeof omega.fileID[files[fileId][0]]!="undefined"){
          var functionsToTrigger=omega.fileID[files[fileId][0]].onBeforeUnloadArray;
          for (var n=0; n<functionsToTrigger.length; n++){
            if (functionsToTrigger[n].func()==false){
              return false;
            }
          }
        }
        if (files[fileId][7]===1){
          var closeSkip=false;
          for (var m=0; m<framesArray.length; m++){
            if (files[fileId][6]==files[framesArray[m]][6]){
              closeSkip=true;
              break;
            }
          }
          if (closeSkip==false){
            omega.fileID[files[fileId][1]].frames[files[fileId][6]].location.href='/systemTemplates/system/loading.html';
            blankSubPages2(fileId);
            console.log(files[fileId][0]+" ("+files[fileId][1]+"."+files[fileId][6]+") <-cleared!");
          }
        }
      }
    }
  }
  if (openFramesArray[files[i][6]]!=-1){
    if (files[openFramesArray[files[i][6]]][0]!=files[i][0]){
      blankSubPages2(openFramesArray[files[i][6]]);
    }
  }
  return true;
}
function blankSubPages2(id){
  loadedFiles[id]=false;
  filesLoading[id]=false;
  openFramesArray[files[id][6]]=-1;
  console.log("unloaded: "+files[id][0]);
  if (typeof choosenFramesetPageArray[files[id][0]]!="undefined"){
    blankSubPages2(choosenFramesetPageArray[files[id][0]]);
  }
}

function replaceVariableInText(oldText,target){
  var re = /{([^}]+)}/g, newText;
  while(newText = re.exec(oldText)) {
    var tempResult="{"+newText[1]+"}";
    var tempTargetParts=target.split("/");
    try{
        tempResult=encodeURIComponent(States[tempTargetParts[0]][tempTargetParts[1]][newText[1]]);
    }
    catch(e){
        console.log('Could not find variable "'+newText[1]+'", it will stay '+tempResult);
    }
    if (newText[1]!=tempResult){
        oldText=oldText.replace('{'+newText[1]+'}',tempResult);
    }
  }
  return oldText;
}

function openActivePage(id){
  if (dashEditing && dashGoer==false && files[id][0]!="dashboard"){
    dashAddBox(10,files[id][0],false,false,sceneChoosen,"activePage");
  }
  else{
    fullscreen(2,files[id][0]);
    if (allFramesetsArray.indexOf(files[id][1])!=-1){
      openPageHistory.unshift(["activePage","",files[id][1]]);
    }
  }
}

function fullscreenChanged(){
  var element=document.documentElement;
  if (element.requestFullScreen) {
    fullFullscreenEnabled=document.fullScreen;
  } 
  else if (element.mozRequestFullScreen) {
    fullFullscreenEnabled=document.mozFullScreen;
  }
  else if (element.webkitRequestFullScreen) {
    fullFullscreenEnabled=document.webkitIsFullScreen;
  }
  else if (element.msRequestFullscreen) {
    fullFullscreenEnabled=document.msFullscreenEnabled;
  }
  //console.log("fullFullscreenEnabled: "+fullFullscreenEnabled);
  if (fullFullscreenEnabled){
    $(document.getElementById("backButton")).show();
  }
}

function fullFullscreen(onOff,element) {
  if (top.userSettings["useFullscreen"]){
    element=element||document.documentElement;
    if (typeof onOff=="undefined"){
      if (fullFullscreenEnabled){
        onOff=0;
      }
      else{
        onOff=1;
      }
    }
    if (onOff==1){
      if(element.requestFullscreen) {
        element.requestFullscreen();
      }
      else if(element.mozRequestFullScreen) {
        element.mozRequestFullScreen();
      }
      else if(element.webkitRequestFullscreen) {
        element.webkitRequestFullscreen();
      }
      else if(element.msRequestFullscreen) {
        element.msRequestFullscreen();
      }
      //fullFullscreenEnabled=true;
    }
    else{
      if(element.requestFullscreen) {
        document.exitFullScreen();
      }
      else if(element.mozRequestFullScreen) {
        document.mozCancelFullScreen();
      }
      else if(element.webkitRequestFullscreen) {
        document.webkitCancelFullScreen();
      }
      else if(element.msRequestFullscreen) {
        document.msExitFullscreen();
      }
      //fullFullscreenEnabled=false;
    }
  }
}

function fullscreen(onOff,id){
  id=id||fullscreenID;
  //console.log("going to fullscreen: "+id+" "+onOff);
  if (onOff>0){
    if (fullscreenID!=id || !fullscreenEnabled || onOff==2 && !fullFullscreenEnabled){
      if (fullscreenEnabled){
          while (files[filesIDArray[fullscreenID]][1]!="-"&&files[filesIDArray[fullscreenID]][1]!="hide"){
              var parentId=files[filesIDArray[fullscreenID]][1];
              if (loadedFiles[filesIDArray[parentId]]){
                  omega.fileID[parentId].frameHideAll(0);
              }
              fullscreenID=parentId;
          }
      }
      fullscreenID=id;
      while (files[filesIDArray[id]][1]!="-"&&files[filesIDArray[id]][1]!="hide"){
        var parentId=files[filesIDArray[id]][1];
        omega.fileID[parentId].frameHideAll(1)
        id=parentId;
      }
      if (!fullscreenEnabled){
        openPageHistory.splice(1,0,["fullscreen","",""]);
        hidechooseframeall(1,false);
        fullscreenEnabled=true;
      }
      if (onOff==1){
        $(document.getElementById("topframehide")).hide();
        $(document.getElementById("fullscreenLeaver")).show();
        fullFullscreen(1);
        getGlobalWindowSize();
      }
      else if(onOff==2){
        $(document.getElementById("fullscreenLeaver")).show();
        $(document.getElementById("backButton")).show(top.userSettings["effectTimeSlide"]);
        $(top.frames["topframe"].document.getElementById("fullscreenLeaver")).show();
        fullFullscreen(1);
      }
    }
  }
  else if (fullscreenEnabled){
    if (fullFullscreenEnabled){
      fullFullscreen(0);
    }
    $(document.getElementById("fullscreenLeaver")).hide();
    $(document.getElementById("backButton")).hide(top.userSettings["effectTimeSlide"]);
    $(top.frames["topframe"].document.getElementById("fullscreenLeaver")).hide();
    fullscreenEnabled=false;
    $(document.getElementById("topframehide")).slideDown(top.userSettings["effectTimeSlide"]);
    getGlobalWindowSize();
    hidechooseframeall(0,false);
    while (files[filesIDArray[id]][1]!="-"&&files[filesIDArray[id]][1]!="hide"){
      var parentId=files[filesIDArray[id]][1];
      omega.fileID[parentId].frameHideAll(0);
      id=parentId;
    }
  }
  top.frames['topframe'].dashButton();
}

var pageToLearnEvent;
var elementToLearnEvent;
function openEventLog(oldPageId,tempElement){
  pageToLearnEvent=oldPageId;
  elementToLearnEvent=tempElement;
  openPage("eventLog",true);
}

function closeEventLog(data){
  openPage(pageToLearnEvent);
  if (elementToLearnEvent){
    omega.fileID[pageToLearnEvent].insert(data,"",elementToLearnEvent);
  }
  else{
    omega.fileID[pageToLearnEvent].insertEvent(data);
  }
}

function resetDashReturnTimeout(){
    clearTimeout(dashReturnTimeout);
    if (userSettings["dashReturnTimeout"] && choosenFramesetPageArray['index']!=filesIDArray["dashboard"] && !recording){
        dashReturnTimeout = setTimeout(function(){
            top.openPage("dashboard");
        },parseInt(userSettings["dashReturnTimeout"])*1000);
    }
}
//-----------------------OpenPageEnd-----------------------------//
//-----------------------TinyBoxes_start-----------------------------//
var tempDataCommand;
var tempDataCommand2;

function showAddedCommandBox(command,timeToWait){
  timeToWait=timeToWait||0;
  setTimeout('showBox(\''+getText('command',0)+' "'+convertActionText(command)+'" '+getText('added',0)+'.\')',timeToWait);
}

function showBox(text){
  TINY.box.show({html:text,fixed:false,animate:false,close:false,mask:false,boxid:'success',autohide:2,top:0});
}

function showErrorBox(text){
  TINY.box.show({html:text,fixed:false,animate:false,close:false,mask:false,boxid:'error',autohide:2,top:0});
}

function submitBox(text,callbackFunction,scope){
  text=text||top.getText("areYouSure",0);
  tempDataCommand=false;
  tempDataCommand2=scope||[[getText('yes',0),true],[getText('no',0),false]];
  var tempText='<center>'+text+'<br><br><table class="stdtable" cellpadding="0" cellspacing="0"><tr>';
  for (var i=0; i<tempDataCommand2.length; i++){
    tempText+='<td><button class="p1 w2 default" onClick="submitBoxOk(tempDataCommand2['+i+'][1]);">'+tempDataCommand2[i][0]+'</button></td>';
  }
  TINY.box.show({html:tempText+'</tr></table></center>',maskid:'whitemask',opacity:30,animate:false,close:false,closejs:function(){submitBoxClose(callbackFunction);}});
}

function submitBoxOk(state){
  tempDataCommand=state;
  TINY.box.hide();
}

function submitBoxClose(callbackFunction){
  if (callbackFunction){
    callbackFunction({OK:tempDataCommand});
  }
}

function alertBox(text,callbackFunction){
  text=text||"...";
  tempDataCommand=false;
  TINY.box.show({html:'<center>'+text+'<br><br><table class="stdtable" cellpadding="0" cellspacing="0"><tr><td class="last"><button class="p1 w2 default" onClick="submitBoxOk(true);">'+getText('ok',0)+'</button></td></tr></table></center>',maskid:'whitemask',opacity:30,animate:false,close:false,closejs:function(){submitBoxClose(callbackFunction);}});
}

function boxKeyEnterHandler(event,callback){
    if(event.which==13){
        callback();
    }
}

//----------------dashAddBoxStart------------------//
function dashAddBox(typ,data,lable,doIt,number,source){
  lable=lable||false;
  doIt=doIt||false;
  source=source||"normal";
  if (data!="scene"){
      number=-1;
  }
  tempDataCommand=[data,0,typ,lable,false,0,number];
  if (!lable){
    if (typ==10){
      if (data=="scene" && number>-1){
        lable=scenesIds[scenesFind[number]][1];
        if(lable==""){
          lable=getText('scene',0)+" "+(number+1);
        }
      }
      else{
        lable=top.getText('files.json',data).replace(/<br>/g," ");
      }
    }
    else{
      lable=convertActionText(tempDataCommand);
    }
  }
  var content='<center>'+getText('addBox',0)+'<br><br>"'+lable+'"<br><br><table class="stdtable" cellpadding="0" cellspacing="0"><tr><td><button class="p1 w2 defaultNH Hgreen" onClick="dashAddBoxAdd('+typ+','+doIt+',\''+source+'\'); TINY.box.hide();">'+getText('add',0);
  if (doIt){
    content+='<br>&'+getText('execute',0);
  }
  content+='</button></td><td class="last"><button class="p1 w2 default" onClick="dashAddBoxOpen('+typ+',\''+source+'\'); TINY.box.hide();">'+getText('execute',0)+'</button></td></tr></table></center>';
  TINY.box.show({html:content,maskid:'whitemask',opacity:30,animate:false,close:false});
}

function dashAddBoxAdd(typ,doIt,source){
  var dashData=top.userSettings["dashData"][viewRecording]||[];
  dashData.push(tempDataCommand);
  top.userSettings["dashData"][viewRecording]=dashData;
  top.saveUserSettings(false);
  if (typ==10){
    showAddedCommandBox(tempDataCommand);
    if (files[choosenFramesetPageArray['index']][0]=="dashboard"){
      top.frames[files[choosenFramesetPageArray['index']][6]].omega.update("reload");
    }
  }
  else{
    showAddedCommandBox(tempDataCommand);
  }
  if(doIt){
    dashAddBoxOpen(typ,source);
  }
}

function dashAddBoxOpen(typ,source){
  dashGoer=true;
  if (typ==10){
    if (source=="activePage"){
      fullscreen(2,tempDataCommand[0]);
    }
    else{
      openPage(tempDataCommand[0],false,false,true,tempDataCommand[6]);
    }
  }
  else{
    Request(JSON.stringify({'method':'TriggerEvent','kwargs':JSON.parse(tempDataCommand[0])}));
  }
}
//------------------dashAddBoxEnd-------------------//
//----------------dashEditBoxStart------------------//
function dashEditBox(i,callbackFunction){
  tempDataCommand=top.userSettings["dashData"][viewChoosen]||[];
  var boxHeight=225;
  var content='<table border="0" cellpadding="0" cellspacing="3" align="right"><tr><td class="w2">'+top.getText('name',0)+':</td><td colspan="2"><input id="textBox" class="w4"></input></td></tr>';
  if (tempDataCommand[i][2]==0){
    content+='<tr><td class="w2">'+top.getText('image',0)+':<br><u>'+top.getText('command',0)+'</u></td><td colspan="2" id="picPathChooser"><input id="picPathBox" class="w4"></input></td></tr>';
    content+='<tr><td colspan="3"><textarea id="textField" class="w6"></textarea></td></tr>';
    content+='<tr><td class="w2">'+top.getText('dashEditTileMode','tileMode')+':</td><td colspan="2" id="tileModeChooser"><select id="tileModeBox" class="default p1 w4"><option value=0>'+top.getText('dashEditTileMode',0)+'</option><option value=1>'+top.getText('dashEditTileMode',1)+'</option><option value=2>'+top.getText('dashEditTileMode',2)+'</option></select></td></tr>';
    content+='<tr><td></td><td style="width:1px;"><button class="p1 w2 default" onClick="dashEditBoxTestF();">'+top.getText('test',0)+'</button></td>';
  }
  else{
    content+='<tr><td class="w2">'+top.getText('image',0)+':</td><td colspan=2" id="picPathChooser"><input id="picPathBox" class="w4"></input></td></tr>';
    content+='<tr><td></td><td style="width:1px;"></td>';
    boxHeight=120;
  }
  content+='<td style="width:1px;" align="right" ><button align="right" class="p1 w2 default" onClick="dashEditBoxOpenOK('+i+');">'+top.getText('ok',0)+'</button></td></tr></table>';
  TINY.box.show({html:content,height: boxHeight,mask:true,maskid:'whitemask',opacity:30,animate:true,close:false,openjs:function(){dashEditBoxOpen(i);},closejs:function(){callbackFunction(i);}});
}

function dashEditBoxOpen(i){
  //$(document.getElementById("p"+i)).addClass("yellow");
  if (tempDataCommand[i][2]==0){
    document.getElementById("textField").value=tempDataCommand[i][0];
    $(document.getElementById('textField')).on("keyup", function(event){boxKeyEnterHandler(event,function(){dashEditBoxOpenOK(i);})});
    if (tempDataCommand[i][5]){
      document.getElementById("tileModeBox").value=tempDataCommand[i][5];
    }
  }
  if (tempDataCommand[i][3]){
    document.getElementById("textBox").value=replaceuml(tempDataCommand[i][3],true);
  }
  if (tempDataCommand[i][4]){
    document.getElementById("picPathBox").value=tempDataCommand[i][4];
  }
  picPathChooserValuePrint(tempDataCommand[i][4]);
  $(document.getElementById('textBox')).on("keyup", function(event){boxKeyEnterHandler(event,function(){insert("<br>","",event.target);})});
}

function picPathChooserValuePrint(newVal){
  var command=JSON.stringify({"method":"getFilesForDropdown","args":['dashboard']});
  $.post("/empty",command, function(data){
      data=JSON.parse(data);
      data.splice(0,0,"");
      var contentStr='<select class="default p1 w4" id="picPathBox">';
      for (var i=0; i<data.length; i++){
        if (data[i]==newVal){
          contentStr+='<option value="'+data[i]+'" selected="selected">'+data[i]+'</option>';
        }
        else{
          contentStr+='<option value="'+data[i]+'">'+data[i]+'</option>';
        }
      }
      document.getElementById("picPathChooser").innerHTML=contentStr+'</select>';
  });
}

function dashEditBoxTestF(){
  dashGoer=true;
  top.Request(JSON.stringify({'method':'TriggerEvent','kwargs':JSON.parse(document.getElementById("textField").value)}));
}

function dashEditBoxOpenOK(i){
  if (tempDataCommand[i][2]==0){
    tempDataCommand[i][0]=document.getElementById("textField").value;
    tempDataCommand[i][5]=document.getElementById("tileModeBox").value;
  }
  tempDataCommand[i][3]=document.getElementById("textBox").value;
  tempDataCommand[i][4]=document.getElementById("picPathBox").value.replace(/\\/g,"/");
  top.userSettings["dashData"][viewChoosen]=tempDataCommand;
  top.saveUserSettings(false);
  TINY.box.hide();
}
//------------------dashEditBoxEnd-------------------//
//----------------inputBoxStart---------------//
function showInputBox(lable,stext,callbackFunction,preset,parameters){
  stext=stext||"";
  preset=preset||"";
  tempDataCommand=false;
  tempDataCommand2=preset;
  parameters = parameters||{maxlength:100};
  parameters["type"]=parameters["type"]||"text";
  parameters["class"]=parameters["class"]||"w4";
  var content='<center>'+stext+'<br><br><table class="stdtable" border="0" cellpadding="0" cellspacing="0"><tr><td colspan=4 class="p1 last" align="center" id="inputBoxContenter1"></td></tr><tr><td class="border3d"></td><td class="cutLeft shrink"><button class="p1 w2 default" onClick="inputBoxOk();" accesskey="O">'+getText('ok',0)+'</button></td><td class="shrink"><button class="p1 w2 default" onClick="TINY.box.hide();" accesskey="C">'+getText('cancel',0)+'</button></td><td class="border3d"></td></tr></table></center>';
  TINY.box.show({html:content,boxid:'inputbox',maskid:'whitemask',opacity:30,animate:false,close:false,openjs:function(){inputBoxLoad(preset,parameters);},closejs:function(){inputBoxClose(lable,callbackFunction);}});
}

function inputBoxLoad(preset,parameters){
  var tempBox='<input accesskey="T" name="inputBox" id="textBox"';
  for (var parameter in parameters){
    tempBox+=' '+parameter+'="'+parameters[parameter]+'"';
  }
  document.getElementById('inputBoxContenter1').innerHTML=tempBox+'>';
  document.getElementById('textBox').value=preset;
  if (preset==""){
    document.getElementById('textBox').focus();
  }
  else{
    document.getElementById('textBox').select();
  }
  $(document.getElementById('textBox')).on("keyup", function(event){boxKeyEnterHandler(event,inputBoxOk)});
}

function inputBoxOk(){
  tempDataCommand=true;
  tempDataCommand2=document.getElementById('textBox').value;
  TINY.box.hide();
}

function inputBoxClose(lable,callbackFunction){
  callbackFunction({OK:tempDataCommand,data:tempDataCommand2,lable:lable});
}
//----------------inputBoxEnd-----------------//
//----------------sceneConditionBoxStart--------------------//
var choosenSceneConditionButtonId;
var choosenSceneConditionNegation;
var choosenSceneConditionState;
var choosenSceneConditionLable;
var choosenSceneConditionData;

function showSceneConditionBox(fileid,buttonid,choosen){
  //console.log(fileid+"/"+buttonid+"/"+choosen);
  choosenSceneConditionLable=false;
  choosenSceneConditionState=-1;
  choosenSceneConditionButtonId=fileid+"/"+buttonid;
  choosenSceneConditionData=buttonsArray[choosenSceneConditionButtonId][4];
  var options=choosenSceneConditionData.length;
  var options2=options;
  if (options2>5){
    options2=5;
  }
  var content='<div align="center" id="sceneConditionContent"></div><table border="0" cellpadding="0" cellspacing="3" align="center"><tr><td id="sceneConditionValueB"></td><td><button class="p1 w2 default" onClick="sceneConditionConnector(\'AND\');">'+top.getText('and',0).toUpperCase()+'</button></td><td><button class="p1 w2 default" onClick="sceneConditionConnector(\'OR\');">'+top.getText('or',0).toUpperCase()+'</button></td><td><button class="p1 w2 default Hgreen" onClick="sceneAddCondition(true);">'+top.getText('ok',0)+'</button></td></tr></table>';
  TINY.box.show({html:content,boxid:'sceneConditionBox',width:330,height:38*options2+41,maskid:'whitemask',opacity:30,animate:true,close:false,openjs:function(){sceneConditionBoxLoad(fileid,buttonid,choosen,options);}});
}

function sceneConditionBoxLoad(fileid,buttonid,choosen,options){
  sceneConditionPrint("normal",fileid,buttonid,choosen,options);
}

var sceneConditionMode;
function sceneConditionPrint(mode,fileid,buttonid,choosen,options){
  if (mode=="normal"){
    var content='<table border="0" cellpadding="0" cellspacing="0" align="center"><tr><td>'+top.getText('if',0)+' '+top.getText('files.json'+fileid,buttonid).replace(/<br>/g,' ')+top.getText('is',1)+' <div id="notB" style="display:inline"></div></td><td><table border="0" cellpadding="0" cellspacing="3">';
    var cols=Math.ceil(options/5);
    for (var j=0; j<choosenSceneConditionData.length; j++){
      content+='<tr>';
      for (var col=0; col<cols; col++){
        content+='<td><div id="condition'+(j+1)+'B"></div></td>';
        if(col!=(cols-1)){
          j++;
          if (j>=choosenSceneConditionData.length){
            break;
          }
        }
      }
      content+='</tr>';
    }
    content+='</table></td><td id="stateLockIndicator"><img src="/img/transparent2.png"></td></tr></table>';
    document.getElementById("sceneConditionContent").innerHTML=content;
    sceneConditionNegation(false);
    sceneConditionStates(fileid,choosen,0);
    document.getElementById("sceneConditionValueB").innerHTML='<button class="p1 w2 default" onClick="sceneConditionPrint(\'python\',\''+fileid+'\',\''+buttonid+'\',\''+choosen+'\','+options+');">Python</button>';
  }
  else{
    var options2=options;
    if (options2>5){
      options2=5;
    }
    var content='<table style="height:'+(38*options2+3)+'px" border="0" cellpadding="0" cellspacing="0" align="center"><tr><td align="center">'+top.getText("ifPyExpIsTrue",0)+':<br><font style="font-size:10px">'+top.getText("buttonReplace","value")+'<br></font></td></tr><tr><td align="center"><input id="sceneConditionValueBox" class="w6" /></td></tr></table>';
    document.getElementById("sceneConditionContent").innerHTML=content;
    document.getElementById("sceneConditionValueBox").value='{value}==""';
    document.getElementById("sceneConditionValueB").innerHTML='<button class="p1 w2 green" onClick="sceneConditionPrint(\'normal\',\''+fileid+'\',\''+buttonid+'\',\''+choosen+'\','+options+');">Python</button>';
  }
  sceneConditionMode=mode;
}

function sceneConditionStates(fileid,choosen,sceneConditionStateLockMode){
  for (var j=0; j<choosenSceneConditionData.length; j++){
    tempString='<button class="p1 w2';
    if (choosen==choosenSceneConditionData[j]){
      if(sceneConditionStateLockMode==1){
        tempString+=' green" onClick="sceneConditionStates(\''+fileid+'\',\''+choosenSceneConditionData[j]+'\',2);">';
        document.getElementById("stateLockIndicator").innerHTML='<img src="/img/lock.png">';
        choosenSceneConditionState="="+choosenSceneConditionData[j];
      }
      else if(sceneConditionStateLockMode==2){
        tempString+=' yellow" onClick="sceneConditionStates(\''+fileid+'\',\''+choosenSceneConditionData[j]+'\',0);">';
        document.getElementById("stateLockIndicator").innerHTML='<img src="/img/lock.png">';
        choosenSceneConditionState="=#"+choosenSceneConditionData[j];
      }
      else{
        tempString+=' green" onClick="sceneConditionStates(\''+fileid+'\',\''+choosenSceneConditionData[j]+'\',1);">';
        document.getElementById("stateLockIndicator").innerHTML='<img src="/img/transparent2.png">';
        choosenSceneConditionState=choosenSceneConditionData[j];
      }
    }
    else{
      tempString+=' default" onClick="sceneConditionStates(\''+fileid+'\',\''+choosenSceneConditionData[j]+'\','+sceneConditionStateLockMode+');">';
    }
    var rename="";
    if (typeof buttonsArray[choosenSceneConditionButtonId][7][j]!="undefined"){
      rename=buttonsArray[choosenSceneConditionButtonId][7][j]["rename"]||"";
    }
    if (rename!=""){
      tempString+=rename+'</button>';
    }
    else{
      tempString+=top.getText('statesCfg.json',choosenSceneConditionData[j])+'</button>';
    }
    //console.log("condition"+(j+1)+'B');
    document.getElementById("condition"+(j+1)+'B').innerHTML=tempString;
  } 
}

function showSceneConditionBox2(o){//variable,lable,scope,choosenIndex,lables,callback
  choosenSceneConditionLable=false;
  choosenSceneConditionLables={};
  var lables;
  if (o.lable){
    choosenSceneConditionLable=o.lable;
  }
  if (o.scope){
    var choosenIndex=o.choosenIndex||0;
    choosenSceneConditionState=-1;
    choosenSceneConditionData=o.scope;
    var tempText=o.variable;
    if (o.lable){
      tempText=o.lable;
    }
    if (o.lables){
      lables=o.lables;
    }
    else{
      lables={};
      for (var i=0; i<choosenSceneConditionData.length; i++){
        lables[""+choosenSceneConditionData[i]]=""+choosenSceneConditionData[i];
      }
    }
    choosenSceneConditionLables=lables;
    for (var i=choosenSceneConditionData.length-1; i>0; i--){
      if (lables[""+choosenSceneConditionData[i]]=="[toggle]"){
        choosenSceneConditionData.splice(i,1); 
      }
    }
    choosenSceneConditionButtonId=o.variable;
    tempText=tempText.replace(/<br>/g,' ');
    var content='<table border="0" cellpadding="0" cellspacing="0" align="center"><tr><td>'+top.getText('if',0)+' '+tempText+top.getText('is',1)+' <div id="notB" style="display:inline"></div></td><td><table border="0" cellpadding="0" cellspacing="3">';
    var options=0;
    var cols=Math.ceil(choosenSceneConditionData.length/5);
    for (var j=0; j<choosenSceneConditionData.length; j++){
      content+='<tr>';
      for (var col=0; col<cols; col++){
        content+='<td><div id="condition'+(j+1)+'B"></div></td>';
        options++;
        if(col!=(cols-1)){
          j++;
          if (j>=choosenSceneConditionData.length){
            break;
          }
        }
      }
      content+='</tr>';
    }
    var options2=options;
    if (options2>5){
      options2=5;
    }
    content+='</table></td></tr></table><table border="0" cellpadding="0" cellspacing="3" align="center"><tr><td><button class="p1 w2 default" onClick="sceneConditionConnector(\'AND\');">'+top.getText('and',0).toUpperCase()+'</button></td><td><button class="p1 w2 default" onClick="sceneConditionConnector(\'OR\');">'+top.getText('or',0).toUpperCase()+'</button></td><td><button class="p1 w2 default Hgreen" onClick="sceneAddCondition(true);">'+top.getText('ok',0)+'</button></td></tr></table>';
    TINY.box.show({html:content,boxid:'sceneConditionBox',width:500,height:38*options2+41,maskid:'whitemask',opacity:30,animate:true,close:false,openjs:function(){sceneConditionBoxLoad2(choosenIndex);},closejs:function(){sceneConditionBoxClose(o.callback);}});
    sceneConditionMode="normal";
  }
  else{
    o.variable=o.variable||"";
    choosenSceneConditionButtonId="None";
    var content='<div align="center" id="sceneConditionContent"></div><table border="0" cellpadding="0" cellspacing="3" align="center"><tr><td><button class="p1 w2 default" onClick="sceneConditionConnector(\'AND\');">'+top.getText('and',0).toUpperCase()+'</button></td><td><button class="p1 w2 default" onClick="sceneConditionConnector(\'OR\');">'+top.getText('or',0).toUpperCase()+'</button></td><td><button class="p1 w2 default Hgreen" onClick="sceneAddCondition(true);">'+top.getText('ok',0)+'</button></td></tr></table>';
    TINY.box.show({html:content,boxid:'sceneConditionBox',width:300,height:130,maskid:'whitemask',opacity:30,animate:true,close:false,openjs:function(){sceneConditionBoxLoad2(o.variable);},closejs:function(){sceneConditionBoxClose(o.callback);}});
    sceneConditionMode="python";
  }
}

function sceneConditionBoxLoad2(data){
  if(sceneConditionMode=="normal"){
    sceneConditionNegation(false);
    sceneConditionStates2(data);
  }
  else{
    var content='<table border="0" cellpadding="0" cellspacing="0" align="center"><tr><td align="center">'+top.getText("ifPyExpIsTrue",0)+':<br><br></td></tr><tr><td align="center"><input id="sceneConditionValueBox" class="w6" /></td></tr></table><br>';
    document.getElementById("sceneConditionContent").innerHTML=content;
    document.getElementById("sceneConditionValueBox").value=data;
  }
}

function sceneConditionBoxClose(callbackFunction){
  if (callbackFunction){
    callbackFunction({});
  }
}

function sceneConditionStates2(choosenIndex){
  var lables = choosenSceneConditionLables;
  for (var j=0; j<choosenSceneConditionData.length; j++){
    tempString='<button class="p1 w2';
    if (choosenIndex==j){
      tempString+=' green';
      choosenSceneConditionState=choosenSceneConditionData[j];
    }
    else{
      tempString+=' default';
    }
    tempString+='" onClick="sceneConditionStates2('+j+');">';
    var tempState=choosenSceneConditionData[j];
    if (lables && typeof lables[tempState]!="undefined"){
      tempState=lables[tempState];
    }
    if (top.getText('statesCfg.json',tempState)!="undefined"){
      tempString+=top.getText('statesCfg.json',tempState)+'</button>';
    }
    else{
      tempString+=tempState+'</button>';
    }
    document.getElementById("condition"+(j+1)+'B').innerHTML=tempString;
  }
}

function sceneConditionNegation(onOff){
  if (onOff){
    document.getElementById("notB").innerHTML='<button class="p1 w1 green" onClick="sceneConditionNegation(false);">'+top.getText('not',0)+'</button>';
    choosenSceneConditionNegation="NOT";
  }
  else{
    document.getElementById("notB").innerHTML='<button class="p1 w1 defaultHT" onClick="sceneConditionNegation(true);">'+top.getText('not',0)+'</button>';
    choosenSceneConditionNegation="IS";
  }
}

function sceneAddCondition(end){
  if (sceneConditionMode!="normal"){
    choosenSceneConditionNegation="PYTHON";
    choosenSceneConditionState=JSON.stringify(document.getElementById("sceneConditionValueBox").value);
  }
  sceneRecordCondition.push(choosenSceneConditionButtonId);
  sceneRecordCondition.push(choosenSceneConditionNegation);
  sceneRecordCondition.push(choosenSceneConditionState);
  TINY.box.hide();
  if (end){
    recordDataArray.push([JSON.stringify(sceneRecordCondition),sceneSelectedLevel,1,getText('if',0)+sceneRecordLable+createSceneLable()+":"]);
    sceneRecordEnd(true,sceneRecording);
  }
}

function createSceneLable(){
  if (choosenSceneConditionLable){
    var tempState=choosenSceneConditionState;
    if (choosenSceneConditionLables && typeof choosenSceneConditionLables[tempState]!="undefined"){
      tempState=choosenSceneConditionLables[tempState];
    }
    if (top.getText('statesCfg.json',tempState)!="undefined"){
      tempState=top.getText('statesCfg.json',tempState);
    }
    return " "+choosenSceneConditionLable+top.getText("conditionNegation",choosenSceneConditionNegation)+" "+tempState;
  }
  else{
    return createConditionLableFromCode([choosenSceneConditionButtonId,choosenSceneConditionNegation,choosenSceneConditionState]);
  }
}

function sceneConditionConnector(connector){
  sceneAddCondition(false);
  sceneRecordLable+=createSceneLable()+" "+getText(connector.toLowerCase(),0);
  sceneRecordCondition.push(connector);
}

//----------------sceneConditionBoxEnd--------------------//
//---------------------onOffBoxStart-------------------------------//
var onOffBoxData=[];
function showOnOffBox(lable,command,data,possibleStates,statesDict,callbackFunction,target){
  onOffBoxData=0;
  TINY.box.show({html:'<center><table border="0" cellpadding="0" cellspacing="0"><tr><td align="center"><div id="onOffBoxContenter"></div></td></tr></table></center>',boxid:'onOffBox',maskid:'whitemask',width:84,height:38*possibleStates.length,opacity:30,animate:true,close:false,openjs:function(){onOffBoxPrinter(command,data,lable,possibleStates,statesDict);},closejs:function(){onOffBoxClose(lable,command,data,possibleStates,statesDict,callbackFunction,target);}});
}

function onOffBoxPrinter(command,data,lable,scope,lables){
  tempDataCommand=false;
  var tempContent='<table class="stdtable" cellpadding="0" cellspacing="0">';
  for (var i=0; i<scope.length; i++){
    var stateLable=scope[i];
    if (lables && lables[scope[i]]){
      stateLable=lables[scope[i]];
    }
    var temp=top.getText('statesCfg.json',stateLable);
    if (temp!="undefined"){
      stateLable=temp;
    }
    //temp=lable+" "+stateLable;
    tempContent+='<tr><td class="last"><button class="p1 w2 default" onClick="onOffBoxOK('+i+');">'+stateLable+'</button></td></tr>';
  }
  document.getElementById('onOffBoxContenter').innerHTML=tempContent+'</table>';
}

function onOffBoxOK(i){
  tempDataCommand=true;
  onOffBoxData=i;
  TINY.box.hide();
}

function onOffBoxClose(lable,command,data,possibleStates,statesDict,callbackFunction,target){
  var targetState;
  if (tempDataCommand){
    targetState=possibleStates[onOffBoxData];
  }
  var lables=statesDict;
  var stateLable=targetState;
  if (lables && lables[targetState]){
    stateLable=lables[targetState];
  }
  var temp=top.getText('statesCfg.json',stateLable);
  if (temp!="undefined"){
    stateLable=temp;
  }
  if (lable){
    lable+=" "+stateLable;
  }
  callbackFunction({OK:tempDataCommand,multi:false,command:command,targetState:targetState,possibleStates:possibleStates,data:data,lable:lable,target:target});
}
//---------------------onOffBoxEnd-------------------------------//
//---------------------numberBoxStart-------------------------------//
var numberBoxStep;
var numberBoxData;
var numberBoxMin;
var numberBoxMax;
var numberBoxDataArray;
var numberBoxIsMax;

function showNumberBox(lable,callbackFunction,preData,minimum,maximum,step){
  if (isNaN(parseFloat(preData))){
    preData=minimum;
  }
  numberBoxStep=""+step;
  numberBoxData=parseFloat(preData);
  numberBoxMin=parseFloat(minimum);
  numberBoxMax=parseFloat(maximum);
  tempDataCommand=false;
  if (numberBoxMin>numberBoxMax){
    numberBoxData=numberBoxData*-1;
    numberBoxMin=numberBoxMin*-1;
    numberBoxMax=numberBoxMax*-1;
  }
  var temp1=""+numberBoxMin;
  if (temp1.indexOf(".")==-1 && numberBoxStep.indexOf(".")!=-1){
    var temp=numberBoxStep.split(".");
    temp1+="."+temp[1];
  }
  var temp2=""+numberBoxMax;
  if (temp2.indexOf(".")==-1 && numberBoxStep.indexOf(".")!=-1){
    var temp=numberBoxStep.split(".");
    temp2+="."+temp[1];
  }
  numberBoxIsMax=temp2;
  if (temp1.length>temp2.length){
    numberBoxIsMax=temp1;
  }
  var temp1=(""+numberBoxData).split(".");
  var temp2=numberBoxIsMax.split(".");
  var temp3=numberBoxStep.split(".");
  while(temp1[0].length<temp2[0].length){
    temp1[0]=" "+temp1[0];
  }
  if (parseFloat(numberBoxStep)<1){
    if(temp1.length==1){temp1[1]="";}
    while(temp1[1].length<temp3[1].length){
      temp1[1]+="0";
    }
    numberBoxData=temp1.join(".");
  }
  else{
    numberBoxData=temp1[0];
  }
  numberBoxDataArray=numberBoxData.split("");
  numberBoxData=parseFloat(numberBoxData);
  var boxWidth=numberBoxDataArray.length;
  if (numberBoxDataArray.indexOf(".")!=-1){
    boxWidth--;
  }
  boxWidth=boxWidth*38+20;
  if (boxWidth<169){
    boxWidth=169;
  }
  TINY.box.show({html:'<center><table border="0" cellpadding="0" cellspacing="0"><tr><td align="center"><div id="numberBoxChangeContent"></div></td></tr><tr><td align="right"><table class="stdtable" cellpadding="0" cellspacing="0"><tr><td><button class="p1 w2 default" onClick="numberBoxChangeOk();" accesskey="O">'+getText('ok',0)+'</button></td><td><button class="p1 w2 default" onClick="TINY.box.hide();" accesskey="C">'+getText('cancel',0)+'</button></td></tr></table></td></tr></table></center>',boxid:'numberBoxChange',maskid:'whitemask',width:boxWidth,height:153,opacity:30,animate:true,close:false,openjs:function(){numberBoxChangeLoad();},closejs:function(){numberBoxClose(lable,callbackFunction);}});
}

function numberBoxChangeLoad(){
  var pp=numberBoxDataArray.indexOf(".");
  if (pp==-1){pp=numberBoxDataArray.length;}
  var numberBoxChangeContentVar='<table class="stdtable" border="0" cellpadding="0" cellspacing="0"><tr>';
  for (var i=0; i<numberBoxDataArray.length; i++){
    if(i<pp){
      numberBoxChangeContentVar+='<td><button class="p1 w1 default" onClick="numberBoxChange('+Math.pow(10,(pp-i-1))+',1)"><img src="/img/up2.png"></button></td>';
    }
    else if(i>pp){
      numberBoxChangeContentVar+='<td><button class="p1 w1 default" onClick="numberBoxChange(0.';
      for (var y=0; y<(i-pp); y++){
        if (y==(i-pp-1)){
          numberBoxChangeContentVar+='1';
        }
        else{
          numberBoxChangeContentVar+='0';
        }
      }
      numberBoxChangeContentVar+=',1)"><img src="/img/up2.png"></button></td>';
    }
  }
  numberBoxChangeContentVar+='</tr><tr>';
  for (var i=0; i<numberBoxDataArray.length; i++){
    if(i!=pp){
      numberBoxChangeContentVar+='<td><button id="numberBoxChangeShowBox'+i+'" class="p1 w1 defaultNH transparent1NH bigFont"></button></td>';
    }
  }
  numberBoxChangeContentVar+='</tr><tr>';
  for (var i=0; i<numberBoxDataArray.length; i++){
    if(i<pp){
      numberBoxChangeContentVar+='<td><button class="p1 w1 default" onClick="numberBoxChange('+Math.pow(10,(pp-i-1))+',-1)"><img src="/img/down2.png"></button></td>';
    }
    else if(i>pp){
      numberBoxChangeContentVar+='<td><button class="p1 w1 default" onClick="numberBoxChange(0.';
      for (var y=0; y<(i-pp); y++){
        if (y==(i-pp-1)){
          numberBoxChangeContentVar+='1';
        }
        else{
          numberBoxChangeContentVar+='0';
        }
      }
      numberBoxChangeContentVar+=',-1)"><img src="/img/down2.png"></button></td>';
    }
  }
  document.getElementById('numberBoxChangeContent').innerHTML=numberBoxChangeContentVar+'</tr></table>';
  numberBoxChange(0,0);
}

function numberBoxChange(what,how){
  if (what<numberBoxStep){
    what=numberBoxStep;
  }
  numberBoxData+=what*how;
  if (numberBoxData<=numberBoxMin){
    numberBoxData=numberBoxMin;
  }
  else if (numberBoxData>=numberBoxMax){
    numberBoxData=numberBoxMax;
  }
  var temp3=(""+numberBoxStep).split(".");
  if (numberBoxStep<1){
    var factor=Math.pow(10,temp3[1].length);
    numberBoxData=Math.round(numberBoxData*factor)/factor;
  }
  var temp1=(""+numberBoxData).split(".");
  var temp2=numberBoxIsMax.split(".");
  while(temp1[0].length<temp2[0].length){
    temp1[0]=" "+temp1[0];
  }
  if (numberBoxStep<1){
    if(temp1.length==1){temp1[1]="";}
    while(temp1[1].length<temp3[1].length){
      temp1[1]+="0";
    }
    numberBoxData=temp1.join(".");
  }
  else{
    numberBoxData=temp1[0];
  }
  numberBoxDataArray=numberBoxData.split("");
  numberBoxData=parseFloat(numberBoxData);
  var stillNull=true;
  for(var i=0; i<numberBoxDataArray.length; i++){
    if (stillNull && numberBoxDataArray[i]===" " && i<(numberBoxDataArray.length-1) && (typeof(numberBoxDataArray[i+1])=="undefined" || numberBoxDataArray[i+1]!=".")){
      numberBoxDataArray[i]="&nbsp;";
    }
    else{
      stillNull=false;
    }
    if(numberBoxDataArray[i]=="."){
      i++;
      numberBoxDataArray[i]="."+numberBoxDataArray[i]+"&nbsp;";
    }
    document.getElementById('numberBoxChangeShowBox'+i).innerHTML=numberBoxDataArray[i];
  }
}

function numberBoxChangeOk(){
  if (numberBoxMin>numberBoxMax){
    numberBoxData=numberBoxData*-1;
  }
  tempDataCommand=true;
  TINY.box.hide();
}

function numberBoxClose(lable,callbackFunction){
  callbackFunction({OK:tempDataCommand,data:""+numberBoxData,lable:lable});
}
//-----------------------numberBoxEnd-------------------------------//
//---------------------sliderBoxStart-------------------------------//
var sld={
  box:{
    isOpen:false,
    tempDataCommand:false,
    show:function(currentId,callbackFunction,preData,minimum,maximum,step,sourcePageOmegaObject,lable){
      if (sld.box.isOpen==false){
        if (isNaN(parseFloat(preData))){
          preData=minimum;
        }
        sld.box.data=""+preData;
        sld.box.step=parseFloat(step);
        sld.box.minimum=parseFloat(minimum);
        sld.box.maximum=parseFloat(maximum);
        sld.box.tempDataCommand=false;
        sld.box.callbackFunction=callbackFunction;
        sld.omega=sourcePageOmegaObject;
        sld.box.lable=lable||"";
        var tempText=top.getText("files.json"+sld.omega.pageID,currentId);
        var content=tempText+':<br><table border="0" cellpadding="0" cellspacing="0" align="center"><tr><td><input id="'+currentId+'Slider" type="range" class="slider vertical big" min="'+minimum+'" max="'+maximum+'" step="'+step+'" value="'+sld.box.data+'" oninput="sld.sldToVal(\''+currentId+'\',this.value);" onchange="sld.sldToVal(\''+currentId+'\',this.value);"></td><td><table border="0" cellpadding="0" cellspacing="3"><tr><td><button onClick="sld.sldUpDown(\''+currentId+'\',\'[up]\');" class="p1 w2 default"><img src="/img/up2.png"/></button></td></tr><tr><td><button id="'+currentId+'ShowLevel" class="p1 w2 transparent1NH">'+sld.box.data+'</button></td></tr><tr><td><button onClick="sld.sldUpDown(\''+currentId+'\',\'[down]\');" class="p1 w2 default"><img src="/img/down2.png"/></button></td></tr></table></td></tr><tr style="height:9px"></tr><tr><td></td><td align="center"><button class="p1 w2 default" onClick="sld.box.onOk();">'+top.getText('ok',0)+'</button></td></tr></table>';
        TINY.box.show({html:content,boxid:'sliderBox',width:120,height:176,maskid:'whitemask',opacity:30,animate:false,close:false,openjs:function(){sld.box.onOpen(currentId);},closejs:function(){sld.box.onClose(currentId);}});
      }
    },
    onOpen:function(currentId){
      sld.box.isOpen=currentId;
      document.getElementById(currentId+'Slider').focus();
      $(document.getElementById(currentId+'Slider')).on("keyup", function(event){boxKeyEnterHandler(event,sld.box.onOk)});
    },
    onOk:function(){
      sld.box.tempDataCommand=true;
      TINY.box.hide();
    },
    onClose:function(currentId){
      data=parseFloat(sld.box.data);
      sld.box.isOpen=false;
      sld.box.callbackFunction({OK:sld.box.tempDataCommand,data:data,lable:sld.box.lable});
    }
  },
  sldUpDown:function(currentId,upDown){
    data=parseFloat(sld.box.data);
    if (upDown=="[up]"){
      data+=sld.box.step;
      if (data>sld.box.maximum){
        return false;
      }
    }
    else{
      data-=sld.box.step;
      if (data<sld.box.minimum){
        return false;
      }
    }
    document.getElementById(currentId+'Slider').value=data;
    sld.sldToVal(currentId,data);
  },
  sldToVal:function(currentId,data){
    if (sld.box.data!=data){
      sld.box.data=data;
      document.getElementById(currentId+'ShowLevel').innerHTML=data;
    }
  }
};
//-----------------------sliderBoxEnd-------------------------------//
//---------------------rgbBoxStart-------------------------------//
var rgb={
  box:{
    isOpen:false,
    tempDataCommand:false,
    show:function(currentId,callbackFunction,tempVal,sourcePageOmegaObject){
      if (rgb.box.isOpen==false){
        rgb.box.data=tempVal;
        rgb.box.tempDataCommand=false;
        rgb.box.callbackFunction=callbackFunction;
        rgb.omega=sourcePageOmegaObject;
        var tempText=top.getText("files.json"+rgb.omega.pageID,currentId);
        var content=tempText+':<br><table border="0" cellpadding="0" cellspacing="3" align="center"><tr><td align="center"><input id="'+currentId+'RGB" type="color" class="p1 w2 default" onChange="rgb.box.onOk();" /></td></tr><tr><td align="center"><button class="p1 w2 default" onClick="rgb.box.onOk();">'+top.getText('ok',0)+'</button></td></tr></table>';
        TINY.box.show({html:content,boxid:'sliderBox',width:84,height:90,maskid:'whitemask',opacity:30,animate:false,close:false,openjs:function(){rgb.box.onOpen(currentId,tempVal);},closejs:function(){rgb.box.onClose(currentId);}});
      }
    },
    onOpen:function(currentId,tempVal){
      rgb.box.isOpen=currentId;
      document.getElementById(currentId+'RGB').value=tempVal;
      document.getElementById(currentId+'RGB').focus();
    },
    onOk:function(){
      rgb.box.tempDataCommand=true;
      TINY.box.hide();
    },
    onClose:function(currentId){
      rgb.box.data=document.getElementById(currentId+'RGB').value;
      rgb.box.isOpen=false;
      rgb.box.callbackFunction({OK:rgb.box.tempDataCommand,data:rgb.box.data});
    }
  }
};
//-----------------------rgbBoxEnd-------------------------------//
//-----------------------dimBoxStart-------------------------------//
  
var dim={
  box:{
    isOpen:false,
    tempDataCommand:false,
    show:function(currentId,callbackFunction,tempValDim,sourcePageOmegaObject){
      if (dim.box.isOpen==false){
        dim.box.tempDataCommand=false;
        dim.box.callbackFunction=callbackFunction;
        dim.omega=sourcePageOmegaObject;
        var tempText=top.getText("files.json"+dim.omega.pageID,currentId);
        dim.omega.dimSliders[currentId]["lastValTo"]=tempValDim;
        var content=tempText+':<br><table border="0" cellpadding="0" cellspacing="0" align="center"><tr><td><input id="'+currentId+'Slider" type="range" class="slider vertical big" min="0" max="100" value="'+tempValDim+'" oninput="dim.dimToVal(\''+currentId+'\',this.value);" onchange="dim.dimToVal(\''+currentId+'\',this.value);"></td><td><table border="0" cellpadding="0" cellspacing="3"><tr><td><button id="'+currentId+'DimUp" class="p1 w2 default"><img src="/img/up2.png"/></button></td></tr><tr><td><button id="'+currentId+'ShowLevel" class="p1 w2 defaultNH transparent1NH">'+tempValDim+'%</button></td></tr><tr><td><button id="'+currentId+'DimDown" class="p1 w2 default"><img src="/img/down2.png"/></button></td></tr></table></td></tr><tr style="height:9px"></tr><tr><td></td><td align="center"><button class="p1 w2 default" onClick="dim.box.onOk();">'+top.getText('ok',0)+'</button></td></tr></table>';
        TINY.box.show({html:content,boxid:'dimmerBox',width:120,height:176,maskid:'whitemask',opacity:30,animate:false,close:false,openjs:function(){dim.box.onOpen(currentId);},closejs:function(){dim.box.onClose(currentId);}});
      }
    },
    onOpen:function(currentId){
      dim.omega.dimSliders[currentId]["setValOkFrom"]=true;
      dim.omega.dimSliders[currentId]["setValOkTo"]=true;
      dim.omega.ApplyHandlerEnduring({targetElement:document.getElementById(currentId+"DimUp"),eventData:{command:'buttons',targetState:'[up]',target:dim.omega.pageID+'/'+currentId}});
      dim.omega.ApplyHandlerEnduring({targetElement:document.getElementById(currentId+"DimDown"),eventData:{command:'buttons',targetState:'[down]',target:dim.omega.pageID+'/'+currentId}});
      document.getElementById(currentId+'Slider').focus();
      $(document.getElementById(currentId+'Slider')).on("keyup", function(event){boxKeyEnterHandler(event,dim.box.onOk)});
      dim.box.isOpen=currentId;
    },
    onOk:function(){
      dim.box.tempDataCommand=true;
      TINY.box.hide();
    },
    onClose:function(currentId){
      dim.box.isOpen=false;
      dim.box.callbackFunction({OK:dim.box.tempDataCommand,data:dim.omega.dimSliders[currentId]['lastValTo']});
    }
  },
  dimToVal:function(currentId,data){
    clearTimeout(dim.setDimValTimer);
    if (dim.omega.dimSliders[currentId]["lastValTo"]!=data){
      dim.omega.dimSliders[currentId]["lastValTo"]=data;
      document.getElementById(currentId+'ShowLevel').innerHTML=data+'%';
      if(dim.omega.dimSliders[currentId]["setValOkTo"]){
        dim.omega.dimSliders[currentId]["setValOkTo"]=false;
        dim.omega.dimSliders[currentId]["setValOkFrom"]=false;
        dim.setDimVal(currentId);
        setTimeout("dim.omega.dimSliders['"+currentId+"']['setValOkTo']=true;",250);
      }
    }
    dim.setDimValTimer=setTimeout("dim.setDimVal('"+currentId+"');",250);
  },
  showDimVal:function(currentId){
    if(dim.box.isOpen===currentId){
      dim.omega.dimSliders[currentId]['setValOkFrom']=true;
      document.getElementById(currentId+'ShowLevel').innerHTML=dim.omega.dimSliders[currentId]["lastValFrom"]+'%';
      document.getElementById(currentId+'Slider').value=dim.omega.dimSliders[currentId]["lastValFrom"];
      dim.omega.dimSliders[currentId]["lastValTo"]=dim.omega.dimSliders[currentId]["lastValFrom"];
    }
    else{
      dim.omega.dimSliders[currentId]["setValOkFrom"]=false;
    }
    clearTimeout(dim.omega.dimSliders[currentId]["showValTimer"]);
  },
  setDimVal:function(currentId){
    clearTimeout(dim.omega.dimSliders[currentId]["showValTimer"]);
    dim.omega.TriggerEvent({command:'buttons',targetState:'[value]',targetValue:[dim.omega.dimSliders[currentId]['lastValTo']],shadow:2,target:dim.omega.pageID+'/'+currentId});
    dim.omega.dimSliders[currentId]["showValTimer"]=setTimeout("dim.showDimVal('"+currentId+"');",3000);
  },
  setDimValTimer:""
};

//-----------------------dimBoxEnd-------------------------------//
//-----------------------TinyBoxes_end------------------------------//

function insert(aTag, eTag, target) {
    target.focus();
    if(typeof target.selectionStart != 'undefined'){// others 
      var start = target.selectionStart;
      var end = target.selectionEnd;
      var insText = target.value.substring(start, end);
      target.value = target.value.substr(0, start) + aTag + insText + eTag + target.value.substr(end);
      var pos;
      if (insText.length == 0) {
        pos = start + aTag.length;
      } else {
        pos = start + aTag.length + insText.length + eTag.length;
      }
      target.selectionStart = pos;
      target.selectionEnd = pos;
    }
    else{
      console.log("insert doesn't work with this browser!");
    }
}

var recordDataArray;
var sceneRecordDataArray1;
var forwardCommands=false;
var insertPauses=false;
var sceneSelectedLine=-1;
var sceneSelectedLevel=0;

function sceneRecordStart(nr,forwardCom,data,condition,insertPaus,selectedLine){
  forwardCommands=forwardCom;
  insertPauses=insertPaus;
  sceneSelectedLine=selectedLine;
  if (sceneSelectedLine==-1){
    sceneSelectedLevel=0;
  }
  else{
    sceneSelectedLevel=data[sceneSelectedLine][1];
    if (data[sceneSelectedLine][0]=='["ELSE"]'){
      sceneSelectedLevel++;
    }
  }
  top.frames['chooseframe'].sceneOnRecord(nr);
  recordDataArray=[];
  sceneRecordDataArray1=[];
  for (var i=0; i<data.length; i++){
    sceneRecordDataArray1.push(data[i]);
  }
  sceneActionsSave(nr,data);
  recording=true;
  conditionMode=condition;
  //top.frames['chooseframe'].tablePrint();
  indexReload('reload');
  //alarmAdvancedBdataOld=top.frames['topframe'].document.getElementById('advanced').innerHTML;
  //top.frames['topframe'].document.getElementById('advanced').innerHTML='<button class="p1 w2 default" onClick="top.showAdvancedAlarmBox()">'+top.getText('advanced',0)+'</button>';
  if (conditionMode==false){
    lastActionTime=0;
    lastCommandTimerThing=setTimeout('lastCommandTimer();',1000);
  }
  else{
    sceneRecordCondition=[];
    sceneRecordLable="";
  }
  openPage('dashboard');
}

function sceneRecordEnd(ext,site){
  recording=false;
  clearTimeout(lastCommandTimerThing);
  
  if (ext==true){
    tempArr=[];
    if (sceneSelectedLine==-1){
      tempArr=sceneRecordDataArray1.concat(recordDataArray);
    }
    else{
      for (var i=0; i<sceneRecordDataArray1.length; i++){
        //if (!conditionMode){
        //  tempArr.push(sceneRecordDataArray1[i]);
        //}
        if (i==sceneSelectedLine){
          tempArr=tempArr.concat(recordDataArray);
        }
        //if (conditionMode){
          tempArr.push(sceneRecordDataArray1[i]);
        //}
      }
    }
    sceneActionsSave(sceneRecording,tempArr);
  }
  conditionMode=false;
  top.frames['chooseframe'].sceneOnRecord(-1);
  //top.frames['chooseframe'].tablePrint();
  //indexReload('reload');
  //top.frames['topframe'].document.getElementById('advanced').innerHTML=alarmAdvancedBdataOld;
  if (site!==false){
    openPage("scene",false,false,true,site);
  }
  else{
    indexReload('reload');
  }
}

function sceneActionsSave(nr,data){
  var foundScene=scenesFindData[nr];
  showBox(getText('sceneSaved',0));
  var command=JSON.stringify({'method':'sceneSaveActions','args':[nr,encodeURIComponent(JSON.stringify(data))]});
  $.post("/empty",command, function(data){
    setTimeout("indexReload('load');",1000);
  });
}

function saveConfig(data){
  showBox(getText('configSaved',0));
  $.post("/empty",data, function(data){
    setTimeout("indexReload('reload');",1000);
  });
}

var saveUserSettingsTimeout;
function saveUserSettings(callbackFunction,wait){
  if (wait){
    clearTimeout(saveUserSettingsTimeout);
    saveUserSettingsTimeout=setTimeout(createSaveUserSettingsTimeoutCallback(callbackFunction),wait);
  }
  else{
    userSettingsDeviceAll[user["id"]]=userSettingsDevice;
    localStorage.userSettings=JSON.stringify(userSettingsDeviceAll);
    $.post('/empty', JSON.stringify({"method":"saveUserSettings","args":[encodeURIComponent(user["id"]),encodeURIComponent(JSON.stringify(userSettings1))]}), saveUserSettings2(callbackFunction));
  }
}

function createSaveUserSettingsTimeoutCallback(callbackFunction){
  return function (){
    saveUserSettings(callbackFunction,false);
  }
}

function saveUserSettings2(callbackFunction){
  return function(data){
    if (!data){
      console.log("Saving user settings failed!");
    }
    else if (callbackFunction){
      callbackFunction();
    }
  }
}

function saveLoginSettings(userId,pw,callbackFunction){
    localStorage.user=JSON.stringify({"id":userId,"pw":pw});
    if (callbackFunction){
        callbackFunction();
    }
}

function lastCommandTimer(){
  if (recording){
    lastActionTime+=1;
    clearTimeout(lastCommandTimerThing);
    lastCommandTimerThing=setTimeout(function(){lastCommandTimer();},1000);
  }
}

var responseTimeout;
function Request(eventname,time,shadow,lable){
  shadow=shadow||0;
  time=time||false;
  if(time){
    setTimeout(function(){Request(eventname,false,shadow,lable);},time);
  }
  else{
    var tevent=JSON.parse(eventname);
    if (tevent["method"]=="TriggerEnduringEvent" || tevent["method"]=="TriggerEvent"){
      tevent["kwargs"]["prefix"]="O-MEGA";
    }
    if (shadow==2){
      if (recording==false || forwardCommands){
        $(responseShowerElement).show();
        $.post("/empty",JSON.stringify(tevent))
          .always(function(){
            clearTimeout(responseTimeout);
            responseTimeout=setTimeout(function(){$(responseShowerElement).hide();},50);
          });
      }
    }
    else if (recording || (dashEditing && dashGoer==false)){
      var temArr=[JSON.stringify(JSON.parse(eventname)["kwargs"]),sceneSelectedLevel,0];
      if (lable){
        temArr.push(lable);
      }
      if (recording && conditionMode==false){
        if (insertPauses && lastActionTime>0 && recordDataArray.length>0){
          recordDataArray.push([JSON.stringify({"suffix":"[wait]","payload":[[],0,lastActionTime]}),sceneSelectedLevel,0]);
        }
        recordDataArray.push(temArr);
        lastActionTime=0;
        lastCommandTimerThing=setTimeout(function(){lastCommandTimer();},1000);
        showAddedCommandBox(temArr);
      }
      else if (dashEditing){
        dashAddBox(0,temArr[0],lable,false);
      }
    }
    if (shadow==0 && ((recording==false && dashEditing==false) || forwardCommands || dashGoer)){
      dashGoer=false;
      $(responseShowerElement).show();
      $.post("/empty",JSON.stringify(tevent))
        .always(function(){
          clearTimeout(responseTimeout);
          responseTimeout=setTimeout(function(){$(responseShowerElement).hide();},50);
        });
    }
    resetDashReturnTimeout();
  }
}