var omega={
  GetText:function(o){//text,mode,language
    if (typeof o=="string"){
      o={text:o};
    }
    if (typeof o.text=="undefined"){
      console.log("omega.GetText: Parameter \"text\" is undefined!");
      return "undefined";
    }
    if (typeof o.mode=="undefined"){
        o.mode=0;
    }
    if (typeof o.language=="undefined"){
      o.language=top.userSettings["language"];
    }
    try{
      return textDict[o.text][o.language];
    }
    catch(e){
      try{
        var tempText=textDict[o.text][0];
        console.log("getText: "+o.text+" is not available in the currently set language, will fallback to english! ("+tempText+")");
        return tempText;
      }
      catch(f){
        return top.getText(o.text,o.mode,o.language);
      }
    }
  },
  TriggerEvent:function(o){//command,targetState,targetValue,data,shadow,target,targetMode,lable,method
    //console.log(o);
    if (typeof o=="string"){
      o={command:o};
    }
    if (typeof o.command=="undefined"){
      console.log("omega.TriggerEvent: Parameter \"command\" is undefined!");
      return false;
    }
    var eventname=o.command;
    var method=o.method||"TriggerEvent";
    if (typeof o.targetState=="undefined"){
      o.targetState="";
    }
    var targetState=o.targetState;
    var targetValue=o.targetValue||[];
    var data = o.data;
    if (typeof data=="undefined" || data==null){
      data="";
    }
    var shadow=o.shadow||0;
    var target=o.target||"";
    var targetMode=o.targetMode||"";
    var lable = o.lable;
    var frontendCommands=false;
    if(eventname=="buttons"){
      var buttonData=top.buttonsArray[target];
      if (buttonData[2]=="jsCommand" && buttonData[1].split("/")[0]=="frontend"){//targetMode;target
        target=buttonData[1].split("/")[0];
        targetMode=buttonData[2];
        frontendCommands=buttonData[5][targetState]||"";
      }
    }
    else if(target==""){
      target=omega.getThisTarget();
    }
    else{
      target=target.split("/");
    }
    if(targetMode!=""){
      if(eventname==""){
        eventname=targetMode;
      }
      else{
        eventname+="."+targetMode;
      }
    }
    var tempid=target;
    if (tempid.length==2){
      tempid=tempid[1];
    }
    if (frontendCommands||(target=="frontend" && targetMode=="jsCommand")){
      var frontendCommand=frontendCommands["command"][0]||data;
      if (frontendCommand!=""){
        if (frontendCommand.indexOf("{value}")!=-1 && targetValue.length>0 && targetValue[frontendCommands["command"][1]-1]!=0){
          frontendCommand=frontendCommand.replace("{value}",targetValue[frontendCommands["command"][1]-1]);//??????????????????????????????????????????
        }
        console.log("Executing JS command: "+frontendCommand);
        eval(frontendCommand);
      }
      return true;
    }
    else if(target[0]=="devices"){
      var tempData=top.devices[top.devicesIDArray[target[1]]];
      if (tempData[1]=="PC_WIN"){
        eventname="EXT."+target[1]+"."+target[0]+"."+tempData[1]+"."+eventname;
      }
      else{
        //eventname=top.sysName+target[0]+"."+tempData[1]+"."+eventname;
        eventname="EXT."+tempData[3]+"."+target[0]+"."+tempData[1]+"."+eventname;
      }
    }
    else if(target[0]=="interfaces"){
      var tempData=top.interfaces[top.interfacesIDArray[target[1]]];
      eventname="EXT."+tempData[3]+"."+target[0]+"."+tempData[1]+"."+eventname;
    }
    else if(target[0]=="programs"){
      var tempData=top.programs[top.programsIDArray[target[1]]];
      eventname="EXT."+tempData[3]+"."+target[0]+"."+tempData[1]+"."+eventname;
    }
    else{
      eventname=top.sysName+eventname;
    }
    //console.log(eventname);
    tempParameters = {"target":tempid,"targetState":targetState};
    if ((Array.isArray(data) || typeof data=="string") && data.length==0){
    }
    else{
      tempParameters["data"] = data;
    }
    if (targetValue.length>0){
      tempParameters["targetValue"] = targetValue;
    }
    top.Request(JSON.stringify({"method":method,"kwargs":{"suffix":eventname,"payload":tempParameters}}),false,shadow,lable);
    return true;
  },
  TriggerEnduringEvent:function(o){
    o.shadow=o.shadow||0;
    if (o.shadow==0 && top.dashEditing){
      o.method="TriggerEvent";
    }
    else{
      o.method="TriggerEnduringEvent";
    }
    return omega.TriggerEvent(o);
  },
  RepeatEnduringEvent:function(){
    top.Request(JSON.stringify({"method":"RepeatEnduringEvent"}),false,2);
  },
  EndLastEvent:function(){
    top.Request(JSON.stringify({"method":"EndLastEvent"}),false,2);
  },
  TriggerAction:function(o){//lable,command,targetState,targetValue,data,possibleStates,statesDict,multi,variable,preSelectIndex,target,selectedObject
    if (typeof o.command=="undefined"){
      console.log("omega.TriggerAction: Parameter \"command\" is undefined!");
      return false;
    }
    else if (typeof o.targetState=="undefined"){
      console.log("omega.TriggerAction: Parameter \"targetState\" is undefined!");
      return false;
    }
    else if (typeof o.possibleStates=="undefined"){
      console.log("omega.TriggerAction: Parameter \"possibleStates\" is undefined!");
      return false;
    }
    var target = o.target||"";
    var tempTarget = target;
    if(o.command!="buttons"){
      if (tempTarget==""){
        tempTarget=omega.getThisTarget();
      }
      else{
        tempTarget=tempTarget.split("/");
      }
    }
    var lable = o.lable;
    var targetState = o.targetState;
    var targetValue = o.targetValue||[];
    var data = o.data;
    var variable=o.variable||'self.States[\"'+tempTarget[0]+'\"][\"'+omega.deviceID+'\"][\"'+o.command+'\"]';
    var preSelectIndex=o.preSelectIndex||o.possibleStates.indexOf(targetState);
    var statesDict = o.statesDict;
    if(preSelectIndex<0){
      preSelectIndex=0;
    }
    if(statesDict && !lable){
      lable=o.command;
    }
    if (o.command!="buttons" && tempTarget){
      var classLable=tempTarget[0]+"/"+tempTarget[1];
      try{
        classLable=top.text[tempTarget[0]+".jsonnames"][tempTarget[1]];
      }
      catch(e){
        console.log('Could not get text for "'+tempTarget[0]+'.jsonnames/'+tempTarget[1]+'", will take "'+classLable+'" instead');
      }
      lable=classLable+":"+lable;
    }
    if (o.multi && o.possibleStates.length>1 && (top.recording && !top.conditionMode || top.dashEditing)){
      var callbackFunction=omega.TriggerEvent;
      if (typeof o.selectedObject=="object"){
        $(o.selectedObject).addClass("blinking");
        callbackFunction=omega.createBlinkingCallback(o.selectedObject,callbackFunction);
      }
      return top.showOnOffBox(lable,o.command,data,o.possibleStates,statesDict,callbackFunction,target);
    }
    else if(top.conditionMode && top.recording){
      var callbackFunction;
      if (typeof o.selectedObject=="object"){
        $(o.selectedObject).addClass("blinking");
        callbackFunction=omega.createBlinkingCallback(o.selectedObject);
      }
      return top.showSceneConditionBox2({variable:variable,lable:lable,scope:o.possibleStates,choosenIndex:preSelectIndex,lables:statesDict,callback:callbackFunction});
    }
    else{
      if (o.command=="sceneOnOff"){
        lable="";
      }
      else if(targetState && lable){
        var tempTargetState=targetState;
        if (statesDict && statesDict[tempTargetState]){
          tempTargetState=statesDict[tempTargetState].replace(/<br>/g," ");
        }
        var tempstate=top.getText('statesCfg.json',tempTargetState).replace(/<br>/g," ");
        if (tempstate=="undefined"){
          tempstate=tempTargetState;
        }
        if (tempstate=="{value}"){
          tempstate=top.getText('statesCfg.json','[set]');
        }
        lable+=" "+tempstate;
        for (var i=0; i<targetValue.length; i++){
          var tempTargetState=targetValue[i];
          if (statesDict && statesDict[tempTargetState]){
            tempTargetState=statesDict[tempTargetState].replace(/<br>/g," ");
          }
          var tempstate=top.getText('statesCfg.json',tempTargetState).replace(/<br>/g," ");
          if (tempstate=="undefined"){
            tempstate=tempTargetState;
          }
          lable+=" "+tempstate;
        }
      }
      return omega.TriggerEvent({command:o.command,targetState:targetState,targetValue:targetValue,data:data,target:target,lable:lable});
    }
  },
  ShowNumberBox:function(o){//lable,command,preset,min,max,step,variable,callback,target,data,selectedObject
    if (typeof o.command=="undefined" && typeof o.callback=="undefined"){
      console.log("omega.ShowNumberBox: Parameter \"command\" and \"callback\" are undefined, at least one of them need to be defined!");
      return false;
    }
    var target=o.target||omega.getThisTarget();
    var callbackFunction=o.callback||omega.createEventExecute(o.command,o.data);
    var minimum=o.min||0;
    var maximum=o.max||100;
    var step=o.step||1;
    var preData=o.preset||minimum;
    if(top.conditionMode && top.recording && (typeof o.command!="undefined" || typeof o.variable!="undefined")){
      if (typeof o.selectedObject=="object"){
        $(o.selectedObject).addClass("blinking");
        callbackFunction=omega.createBlinkingCallback(o.selectedObject);
      }
      var variable=o.variable||'self.States[\"'+target[0]+'\"][\"'+omega.deviceID+'\"][\"'+o.command+'\"]';
      return top.showSceneConditionBox2({variable:variable,callback:callbackFunction});
    }
    else{
      if (typeof o.selectedObject=="object"){
        $(o.selectedObject).addClass("blinking");
        callbackFunction=omega.createBlinkingCallback(o.selectedObject,callbackFunction);
      }
      var lable = o.lable;
      if (lable && target){
        var classLable=target[0]+"/"+target[1];
        try{
          classLable=top.text[target[0]+".jsonnames"][target[1]];
        }
        catch(e){
          console.log('Could not get text for "'+target[0]+'.jsonnames/'+target[1]+'", will take "'+classLable+'" instead');
        }
        lable=classLable+":"+lable;
      }
      return top.showNumberBox(lable,callbackFunction,preData,minimum,maximum,step);
    }
  },
  ShowSliderBox:function(o){//lable,command,preset,min,max,step,variable,callback,target,data,selectedObject
    if (typeof o.command=="undefined" && typeof o.callback=="undefined"){
      console.log("omega.ShowSliderBox: Parameter \"command\" and \"callback\" are undefined, at least one of them need to be defined!");
      return false;
    }
    else if (typeof o.command=="undefined" && typeof o.variable=="undefined"){
      console.log("omega.ShowSliderBox: Parameter \"command\" and \"variable\" are undefined, at least one of them need to be defined!");
      return false;
    }
    if (typeof o.selectedObject=="object"){
      currentId=o.selectedObject.id;
    }
    else{
      currentId="1";
    }
    var target=o.target||omega.getThisTarget();
    var callbackFunction=o.callback||omega.createEventExecute(o.command,o.data);
    var minimum=o.min||0;
    var maximum=o.max||100;
    var step=o.step||1;
    var preData=o.preset||minimum;
    if(top.conditionMode && top.recording){
      if (typeof o.selectedObject=="object"){
        $(o.selectedObject).addClass("blinking");
        callbackFunction=omega.createBlinkingCallback(o.selectedObject);
      }
      var variable=o.variable||'self.States[\"'+target[0]+'\"][\"'+omega.deviceID+'\"][\"'+o.command+'\"]';
      return top.showSceneConditionBox2({variable:variable,callback:callbackFunction});
    }
    else{
      if (typeof o.selectedObject=="object"){
        $(o.selectedObject).addClass("blinking");
        callbackFunction=omega.createBlinkingCallback(o.selectedObject,callbackFunction);
      }
      var lable = o.lable;
      if (lable && target){
        var classLable=target[0]+"/"+target[1];
        try{
          classLable=top.text[target[0]+".jsonnames"][target[1]];
        }
        catch(e){
          console.log('Could not get text for "'+target[0]+'.jsonnames/'+target[1]+'", will take "'+classLable+'" instead');
        }
        lable=classLable+":"+lable;
      }
      return top.sld.box.show(currentId,callbackFunction,preData,minimum,maximum,step,omega,lable);
    }
  },
  ShowInputBox:function(o){//lable,text,command,preset,callback,target,data,parameters,selectedObject
    if (typeof o.command=="undefined" && typeof o.callback=="undefined"){
      console.log("omega.ShowInputBox: Parameter \"command\" and \"callback\" are undefined, at least one of them need to be defined!");
      return false;
    }
    var target=o.target||omega.getThisTarget();
    var callbackFunction=o.callback||omega.createEventExecute(o.command,o.data);
    var preData=o.preset||"";
    var lable = o.lable;
    if (typeof o.selectedObject=="object"){
      $(o.selectedObject).addClass("blinking");
      callbackFunction=omega.createBlinkingCallback(o.selectedObject,callbackFunction);
    }
    if (lable && target){
      var classLable=target[0]+"/"+target[1];
      try{
        classLable=top.text[target[0]+".jsonnames"][target[1]];
      }
      catch(e){
        console.log('Could not get text for "'+target[0]+'.jsonnames/'+target[1]+'", will take "'+classLable+'" instead');
      }
      lable=classLable+":"+lable;
    }
    var stext=o.text||lable;
    return top.showInputBox(lable,stext,callbackFunction,preData,o.parameters);
  },
  ShowAlertBox:function(o){//text,callback,selectedObject
    if (typeof o.text!="string"){
      console.log("omega.ShowAlertBox: Parameter \"text\" is undefined or not a string!");
      return false;
    }
    if (typeof o.selectedObject=="object"){
      $(o.selectedObject).addClass("blinking");
      o.callback=omega.createBlinkingCallback(o.selectedObject,o.callback);
    }
    return top.alertBox(o.text,o.callback);
  },
  ShowSubmitBox:function(o){//text,callback,selectedObject,buttons
    if (typeof o.selectedObject=="object"){
      $(o.selectedObject).addClass("blinking");
      o.callback=omega.createBlinkingCallback(o.selectedObject,o.callback);
    }
    return top.submitBox(o.text,o.callback,o.buttons);
  },
  createBlinkingCallback:function(selectedObject,callbackFunction){
    return function(o){
      $(selectedObject).removeClass("blinking");
      if (typeof callbackFunction=="function"){
        callbackFunction(o);
      }
    }
  },
  ON_OFF:["[on]","[off]"],
  IS_FRAME_SET:false,
  IS_TOUCH_DEVICE:false,
  buttons:"",
  FRAME_NAME:window.self.name,
  subPages:[],
  useNiceScroll:true,
  ApplyHandlerRepeat:function(o){//targetId,targetElement,interval,eventData,func
    if (typeof o.targetElement!="object" && typeof o.targetElement!="undefined"){
      console.log("omega.ApplyHandlerRepeat: Parameter \"targetElement\" is not an object!");
      return false;
    }
    else if (typeof o.targetElement=="undefined" && typeof o.targetId!="string"){
      console.log("omega.ApplyHandlerRepeat: Parameter \"targetElement\" is undefined and parameter \"targetId\" is undefined or not a string!");
      return false;
    }
    if (typeof o.func!="function" && typeof o.func!="undefined"){
      console.log("omega.ApplyHandlerRepeat: Parameter \"func\" is not a function!");
      return false;
    }
    else if (typeof o.func=="undefined" && typeof o.eventData!="object"){
      console.log("omega.ApplyHandlerRepeat: Parameter \"func\" is undefined and parameter \"eventData\" is undefined or not a dictionary!");
      return false;
    }
    var func = o.func||function (){omega.TriggerEvent(o.eventData);};
    var tempElement = o.targetElement || document.getElementById(o.targetId);
    var interval = o.interval || 0.5;
    if (omega.IS_TOUCH_DEVICE){
      $(tempElement).on("touchstart", omega.touchControlStart);
      $(tempElement).on("touchend", omega.touchControlEnd);
      $(tempElement).on("touchleave", omega.touchControlOut);
      $(tempElement).on("contextmenu", omega.preventDefault);
    }
    $(tempElement).on("mouseout", function(event){omega.buttonUnpressF(event.target.id)});
    $(tempElement).on("mouseup", function(event){omega.buttonUnpressF(event.target.id)});
    $(tempElement).on("mousedown", function(event){omega.buttonPressF(event.target.id, func, interval)});
    return true;
  },
  ApplyHandlerEnduring:function(o){//targetId,targetElement,eventData
    if (typeof o.targetElement!="object" && typeof o.targetElement!="undefined"){
      console.log("omega.ApplyHandlerEnduring: Parameter \"targetElement\" is not an object!");
      return false;
    }
    else if (typeof o.targetElement=="undefined" && typeof o.targetId!="string"){
      console.log("omega.ApplyHandlerEnduring: Parameter \"targetElement\" is undefined and parameter \"targetId\" is undefined or not a string!");
      return false;
    }
    if (typeof o.eventData!="object"){
      console.log("omega.ApplyHandlerEnduring: Parameter \"eventData\" is undefined or not a dictionary!");
      return false;
    }
    var tempElement = o.targetElement || document.getElementById(o.targetId);
    var func = function (){omega.TriggerEnduringEvent(o.eventData);};
    if (omega.IS_TOUCH_DEVICE){
      $(tempElement).on("touchstart", omega.touchControlStart);
      $(tempElement).on("touchend", omega.touchControlEnd);
      $(tempElement).on("touchleave", omega.touchControlOut);
    }
    $(tempElement).on("mouseout", function(event){omega.buttonUnpressF(event.target.id)});
    $(tempElement).on("mouseup", function(event){omega.buttonEnduringUnpressF(event.target.id)});
    $(tempElement).on("mousedown", function(event){omega.buttonEnduringPressF(event.target.id, func)});
    return true;
  },
  ApplyHandlerMouseWheel:function(o){//targetId,targetElement,eventData,funcDown,funcUp
    if (typeof o.targetElement!="object" && typeof o.targetElement!="undefined"){
      console.log("omega.ApplyHandlerMouseWheel: Parameter \"targetElement\" is not an object!");
      return false;
    }
    else if (typeof o.targetElement=="undefined" && typeof o.targetId!="string"){
      console.log("omega.ApplyHandlerMouseWheel: Parameter \"targetElement\" is undefined and parameter \"targetId\" is undefined or not a string!");
      return false;
    }
    var tempTargetState=[];
    if (typeof o.funcUp!="function" && typeof o.funcUp!="undefined"){
      console.log("omega.ApplyHandlerMouseWheel: Parameter \"funcUp\" is not a function!");
      return false;
    }
    else if (typeof o.funcDown!="function" && typeof o.funcDown!="undefined"){
      console.log("omega.ApplyHandlerMouseWheel: Parameter \"funcDown\" is not a function!");
      return false;
    }
    else if ((typeof o.funcUp=="undefined" || typeof o.funcDown=="undefined") && typeof o.eventData!="object"){
      console.log("omega.ApplyHandlerMouseWheel: Parameters \"funcUp\" or \"funcDown\" are undefined and parameter \"eventData\" is undefined or not a dictionary!");
      return false;
    }
    else if(typeof o.eventData=="object"){
      if (typeof o.eventData.targetState=="undefined"){
        tempTargetState="";
      }
      else{
        tempTargetState=o.eventData.targetState;
      }
    }
    var funcUp = o.funcUp || function (){omega.TriggerEvent({command:o.eventData.command,targetState:tempTargetState||"[up]",payload:o.eventData.payload,shadow:o.eventData.shadow,target:o.eventData.target,targetMode:o.eventData.targetMode,lable:o.eventData.lable});};
    var funcDown = o.funcDown || function (){omega.TriggerEvent({command:o.eventData.command,targetState:tempTargetState||"[down]",payload:o.eventData.payload,shadow:o.eventData.shadow,target:o.eventData.target,targetMode:o.eventData.targetMode,lable:o.eventData.lable});};
    var tempElement = o.targetElement || document.getElementById(o.targetId);
    $(tempElement).on("wheel", function(event){omega.mouseWeelHandler(event,funcUp,funcDown)});
    return true;
  },
  mouseWeelHandler:function(event,funcUp,funcDown){
    omega.preventDefault(event);
    var tempTarget=event.target;
    while (typeof tempTarget.value=="undefined" && tempTarget.tagName!="BODY"){
      tempTarget=tempTarget.parentNode;
    }
    //var o = JSON.parse(JSON.stringify(o1));//creates a copy of o1 (important)
    if(event.originalEvent.deltaY<0){
      funcUp();
    }
    else if(event.originalEvent.deltaY>0){
      funcDown();
    }
  },
  dimSliders:{},
  setColor:function(buttonI,thisStateId,actionIndex,button){
    if (actionIndex==0){
      omega.buttonActionDataArray=[];
    }
    omega.buttonAction(buttonI,thisStateId,(actionIndex+1),button,button.value);
  },
  getThisTarget:function(){
    if (omega.pageID=="system"){
      return [omega.deviceCategory,omega.deviceID];
    }
    else if(omega.pageID=="scene"){
      return false;
    }
    else{
      var tempTarget=top.files[top.filesIDArray[omega.pageID]][2].split("/");
      if (tempTarget.length==2){
        return tempTarget;
      }
      else{
        return false;
      }
    }
  },
  onLoadArray:[],
  OnLoad:function(func){
    if (typeof func!="function"){
      console.log("omega.OnLoad: 1st parameter is undefined or not a function!");
      return false;
    }
    omega.onLoadArray.push({func:func});
    return true;
  },
  onUpdateArray:[],
  OnUpdate:function(func){
    if (typeof func!="function"){
      console.log("omega.OnUpdate: 1st parameter is undefined or not a function!");
      return false;
    }
    omega.onUpdateArray.push({func:func});
    return true;
  },
  modeMenu:{enabled:false,showStates:true,record:true},
  CreateButtonTable:function(o){//targetElement,targetId,maxCols,startButtonIndex,endButtonIndex
    if (typeof o.targetElement!="object" && typeof o.targetElement!="undefined"){
      console.log("omega.CreateButtonTable: Parameter \"targetElement\" is not an object!");
      return false;
    }
    else if (typeof o.targetElement=="undefined" && typeof o.targetId!="string"){
      console.log("omega.CreateButtonTable: Parameter \"targetElement\" is undefined and parameter \"targetId\" is undefined or not a string!");
      return false;
    }
    if (typeof o.maxCols!="number" || o.maxCols<1){
      o.maxCols=8;
    }
    if (typeof o.startButtonIndex!="number"){
      o.startButtonIndex=0;
    }
    if (typeof o.endButtonIndex!="number"){
      o.endButtonIndex=omega.buttons.length;
    }
    var targetElement=o.targetElement||document.getElementById(o.targetId);
    var maxCols=o.maxCols;
    var tempCols=0;
    for (var i=o.startButtonIndex; tempCols<maxCols&&i<o.endButtonIndex; i++){
      if (parseInt(omega.buttons[i][3][0],10)>-10){
        tempCols+=parseInt(omega.buttons[i][3][1],10);
      }
    }
    if (tempCols<maxCols){
      maxCols=tempCols;
    }
    if (omega.buttons!=""){
      var tablestr='<table class="stdtable" border="0" cellpadding="0" cellspacing="0"><tr>';
      for (var i=0; i<maxCols; i++){
        tablestr+='<td class="cutTop cutLeft"></td>';
      }
      tablestr+='</tr><tr>';
      var col=0;
      //var row=0;
      var count=o.startButtonIndex;
      for (var i=o.startButtonIndex; i<o.endButtonIndex; i++){
        var buttonId1=parseInt(omega.buttons[i][3][0],10);
        if (buttonId1>-10){
          var newColAdd=parseInt(omega.buttons[i][3][1],10);
          if ((col+newColAdd)>maxCols){
            tablestr+='<td colspan="'+(maxCols-col)+'"></td></tr><tr>';
            col=0;
            //row++;
          }
          col+=newColAdd;
          if (buttonId1<=-5){
            tablestr+='<td id="'+count+':1B" class="p'+omega.buttons[i][3][0]+'" colspan="'+omega.buttons[i][3][1]+'" valign="top"></td>';
          }
          else{
            if (buttonId1==0){
              if (col>=maxCols){
                tablestr+='<td colspan="'+omega.buttons[i][3][1]+'" valign="top" class="cutTop cutLeft last">';
              }
              else{
                tablestr+='<td colspan="'+omega.buttons[i][3][1]+'" valign="top" class="cutTop cutLeft">';
              }
              tablestr+='<table class="stdtable" border="0" cellpadding="0" cellspacing="0">';
              var buttonsPerButton=1;
              if(typeof omega.buttons[i][3][2]!="undefined"){
                buttonsPerButton=newColAdd/parseInt(omega.buttons[i][3][2],10);
              }
              var currentButtonPerButton=0;
              for (var j=0;j<=omega.buttons[i][4].length;j++){
                if (j==0 || top.states[top.statesIDArray[omega.buttons[i][4][j-1]]][3]==0){
                  if(buttonsPerButton>1){
                    if(currentButtonPerButton==0){
                      tablestr+='<tr>';
                    }
                    if(j==0){
                      tablestr+='<td colspan="'+buttonsPerButton+'"><div id="'+count+':'+j+'B"></div></td>';
                      currentButtonPerButton=buttonsPerButton;
                    }
                    else{
                      tablestr+='<td><div id="'+count+':'+j+'B"></div></td>';
                      currentButtonPerButton++;
                    }
                    if(buttonsPerButton==currentButtonPerButton || j==omega.buttons[i][4].length){
                      tablestr+='</tr>';
                      currentButtonPerButton=0;
                    }
                  }
                  else{
                    tablestr+='<tr><td><div id="'+count+':'+j+'B"></div></td></tr>';
                  }
                }
              }
              tablestr+='</table></td>';
            }
            else{
              if (col>=maxCols){
                tablestr+='<td colspan="'+omega.buttons[i][3][1]+'" valign="top" class="last">';
              }
              else{
                tablestr+='<td colspan="'+omega.buttons[i][3][1]+'" valign="top">';
              }
              tablestr+='<div id="'+count+':1B"></div></td>';
            }
          }
          if (col>=maxCols){
            tablestr+='</tr><tr>';
            col=0;
          }
          count++;
        }
      }
      if (col!=0 && col<maxCols){
        tablestr+='<td class="w'+(maxCols-col)+'" colspan="'+(maxCols-col)+'"><br></td>';
      }
      tablestr+='</tr></table>';
      targetElement.innerHTML=tablestr;
    }
    return true;
  },
  updateModeMenu:function(ext,showStates,record){
    if (showStates || ext=="init" || ext=="load" || ext=="reload"){
      var noPage=true;
      for (var i=0; i<omega.subPages.length; i++){
        if (ext=="init" || ext=="load" || ext=="reload"){
          if (top.viewChoosen=="-" || top.files[omega.subPages[i]][10].indexOf(top.viewChoosen)!=-1 || omega.pageID=="scene" && (top.user["parameters"]["isSceneEditor"] || i==0) || omega.pageID=="sceneFunctions" && top.user["parameters"]["isSceneEditor"]){
            $(document.getElementById('omegaMode'+i+'R')).show();
            var tempButtonElement = document.getElementById('omegaMode'+i+'B');
            if (omega.subPages[i]==top.choosenFramesetPageArray[omega.pageID]){
              $(tempButtonElement).addClass("green");
              $(tempButtonElement).removeClass("default");
              tempButtonElement.onclick=omega.createOpenPage(true,i,record);
              omega.showActualFrame();
              noPage=false;
            }
            else{
              $(tempButtonElement).addClass("default");
              $(tempButtonElement).removeClass("green");
              tempButtonElement.onclick=omega.createOpenPage(false,i,record);
            }
            tempButtonElement.innerHTML = top.getText('files.json',top.files[omega.subPages[i]][0]);
          }
          else{
            $(document.getElementById('omegaMode'+i+'R')).hide();
          }
        }
        if (showStates){
          document.getElementById('omegaMode'+i+'S').innerHTML =top.rotgruen(top.allIndexDataGroupArray[top.files[omega.subPages[i]][0]]);
        }
      }
      if (noPage && (ext=="init" || ext=="load" || ext=="reload")){
        omega.ShowAlertBox({text:omega.GetText({text:"accessDenied"})+"!"});
        top.openPage("dashboard");
      }
    }
  },
  createOpenPage:function(activePage,i,record){
    if (activePage){
      return function(){
        top.openActivePage(omega.subPages[i]);
      };
    }
    else{
      return function(){
        top.openPage(top.files[omega.subPages[i]][0],false,false,record,omega.advancedPageNumber);
      };
    }
  },
  choosenFramesetPageOpened:false,
  update:function(ext){
    if (omega.IS_FRAME_SET){
      if (omega.modeMenu.enabled){
        omega.updateModeMenu(ext,omega.modeMenu.showStates,omega.modeMenu.record);
      }
      if (top.loadedFiles[top.choosenFramesetPageArray[omega.pageID]]){
        //console.log(ext);
        if (top.files[top.choosenFramesetPageArray[omega.pageID]][8]==1 || top.files[top.choosenFramesetPageArray[omega.pageID]][3].substr(0,1)!="/"){
          if (ext=="reload"){
            top.openPage(top.files[top.choosenFramesetPageArray[omega.pageID]][0],true,false,false,omega.advancedPageNumber,ext);
          }
        }
        else if (top.filesLoading[top.choosenFramesetPageArray[omega.pageID]]==false && top.choosenFramesetPageArray[omega.pageID]==top.nextChoosenFramesetPageArray[omega.pageID]){//internal pages only
          //console.log(omega.pageID);
          //console.log(top.choosenFramesetPageArray[omega.pageID]);
          //console.log(top.files[top.choosenFramesetPageArray[omega.pageID]][6]);
          window.frames[top.files[top.choosenFramesetPageArray[omega.pageID]][6]].omega.update(ext);
        }
      }
    }
    if (ext=="reload"){
      omega.createButtons();
    }
    omega.updateButtons();
    for (var i in omega.onUpdateArray){
      omega.onUpdateArray[i].func(ext);
    }
  },
  //buttonsCreated:false,
  buttonViews:false,
  createButtons:function(){
    var count=0;
    for (var i=0; i<omega.buttons.length; i++){
      var thisButton=omega.buttons[i];
      var currentId=thisButton[0];
      var currentId2=omega.pageID+"/"+currentId;
      if (thisButton[1]=="macro" && thisButton[2]=="copy"){
        currentId2=thisButton[5]["buttonID"];
      }
      var buttonId1=parseInt(thisButton[3][0],10);
      if (buttonId1>-10){
        var buttonId=buttonId1;
        var buttonWidth1=parseInt(thisButton[3][1],10);
        if (buttonId==-5){
          var cssClasses="";
          if (typeof thisButton[7]["[?]"]!="undefined"){
            cssClasses=thisButton[7]["[?]"]["cssClasses"]||"";
          }
          document.getElementById(count+":1B").innerHTML ='<p id="'+count+':1B2" class="selectable w'+buttonWidth1+' '+cssClasses+'"></p>';
        }
        else{
          var buttonWidth=parseInt(thisButton[3][2],10)||buttonWidth1;
          if (buttonId==0){
            buttonId=1;
            document.getElementById(count+":0B").innerHTML ='<button id="'+count+':0B2" class="p2 w'+buttonWidth1+' defaultNH"></button>';
          }
          for (var j=0; j<thisButton[4].length; j++){
            var tempString;
            var tempMouseWheelEventData;
            var actionString="";
            var tempEventData={};
            var valueString="";
            var thisStateId=thisButton[4][j];
            var thisStateId2=thisStateId;
            if (thisButton[1]=="macro" && thisButton[2]=="copy"){
              thisStateId2=thisButton[5][thisStateId][0];
            }
            if (top.states[top.statesIDArray[thisStateId]][3]==0){
              var buttonMode="std";
              var buttonModeSettings="";
              var cssClasses="";
              var mouseWheel=true;
              var buttonAfterThis=false;
              var enduringButton=false;
              if (typeof thisButton[7][thisStateId]!="undefined" && typeof thisButton[7][thisStateId]["buttonModes"]!="undefined"){
                buttonMode=thisButton[7][thisStateId]["buttonModes"][0]["mode"]||"std";
                buttonModeSettings=thisButton[7][thisStateId]["buttonModes"][0]["modeSettings"]||"";
                //mouseWheel=thisButton[7][thisStateId]["mouseWheel"]||0;
                cssClasses=thisButton[7][thisStateId]["cssClasses"];
                for (var z=1; z<thisButton[7][thisStateId]["buttonModes"].length; z++){
                  if (thisButton[7][thisStateId]["buttonModes"][z]["mode"]!="none" && (thisButton[7][thisStateId]["buttonModes"][z]["onlyRecord"]==0 || top.recording)){
                    buttonAfterThis=true;
                    break;
                  }
                }
              }
              if (!cssClasses){
                if (buttonId1<0){
                  cssClasses="transparent1NH";
                }
                else{
                  cssClasses="default";
                }
              }
              if (mouseWheel && buttonMode!="dim" && (!thisButton[5]["[up]"] || !thisButton[5]["[down]"])){
                mouseWheel=false;
              }
              var tempTarget=document.getElementById(count+":"+(j+1)+'B');
              var tempButtonId=count+":"+(j+1)+'B2';
              if (buttonMode=="rgb" && !top.recording && !top.dashEditing && !buttonAfterThis){
                tempString='<input id="'+tempButtonId+'" class="p'+buttonId+' w'+buttonWidth+'" type="color" onChange="omega.setColor('+i+',\''+thisStateId+'\',0,this);" />';//#click#
              }
              else{
                if(buttonMode=="dim"){
                  if (typeof omega.dimSliders[currentId]=="undefined"){
                    omega.dimSliders[currentId]={};
                    omega.dimSliders[currentId]["setValOkFrom"]=false;
                    omega.dimSliders[currentId]["setValOkTo"]=false;
                    omega.dimSliders[currentId]["lastValTo"]=-1;
                    omega.dimSliders[currentId]["lastValFrom"]=0;
                    omega.dimSliders[currentId]["showValTimer"]=null;
                  }
                }
                if(buttonId1>=0){
                  if (top.conditionMode && top.recording){
                    var tempIds=currentId2.split("/");
                    actionString=' onmouseup="top.showSceneConditionBox(\''+tempIds[0]+'\',\''+tempIds[1]+'/'+tempIds[2]+'\',\''+thisStateId2+'\');"';//#click#
                  }
                  else{
                    if (mouseWheel){
                      tempMouseWheelEventData={command:'buttons',target:currentId2};
                    }
                    if (buttonMode=="confirm" || buttonMode=="str" || buttonMode=="num" || buttonMode=="sld" || buttonMode=="none" || buttonMode=="dim" || buttonMode=="rgb" || buttonAfterThis){
                      actionString=' onmouseup="omega.buttonAction('+i+',\''+thisStateId+'\',0,this);"';//#click#
                    }
                    else if(buttonMode=="autoRepeat"){
                      buttonModeSettings=parseFloat(buttonModeSettings)||0.5;
                      tempEventData={command:'buttons',targetState:thisStateId2,target:currentId2};
                    }
                    else if (thisButton[1]=="frontend" && thisButton[2]=="jsCommand"){
                      actionString=' onmouseup="omega.TriggerEvent({command:\'buttons\',targetState:\''+thisStateId2+'\',target:\''+currentId2+'\'});"';//#click#
                    }
                    else{
                      var tempScope=thisButton[4];
                      /*if (top.recording){
                        for (var k=tempScope.length-1; k>=0; k--){
                          if (top.states[top.statesIDArray[tempScope[k]]][3]==1){
                            tempScope.splice(k,1);
                          }
                        }
                      }*/
                      if (tempScope.length==2 && typeof thisButton[5]["[none]"]!="undefined" && (typeof thisButton[5]["[none]"][0]=="undefined" || thisButton[5]["[none]"][0]!="" && thisButton[5]["[none]"][0]!=["[wait]",""])){
                        if (top.recording){
                          actionString=' onmouseup="omega.TriggerAction({command:\'buttons\',targetState:\''+thisStateId2+'\',possibleStates:[\''+thisStateId2+'\',\'[none]\',\'[toggle]\'],target:\''+currentId2+'\',multi:true,selectedObject:this});"';//#click#
                        }
                        else{
                          tempEventData={command:'buttons',targetState:"[toggle]",target:currentId2};
                          enduringButton=true;
                        }
                      }
                      else if (top.dashEditing && tempScope.length==2){
                        actionString=' onmouseup="omega.TriggerAction({command:\'buttons\',targetState:\''+thisStateId2+'\',possibleStates:[\''+tempScope[0]+'\',\''+tempScope[1]+'\',\'[toggle]\'],target:\''+currentId2+'\',multi:true,selectedObject:this});"';//#click#
                      }
                      else if (top.dashEditing && (thisStateId2=="[on]" || thisStateId2=="[off]") && (typeof thisButton[5]["[on]"]!="undefined" && typeof thisButton[5]["[off]"]!="undefined") && typeof thisButton[5]["[toggle]"]=="undefined"){
                        actionString=' onmouseup="omega.TriggerAction({command:\'buttons\',targetState:\''+thisStateId2+'\',possibleStates:[\'[on]\',\'[off]\',\'[toggle]\'],target:\''+currentId2+'\',multi:true,selectedObject:this});"';//#click#
                      }
                      else if (top.dashEditing && (thisStateId2=="[open]" || thisStateId2=="[close]") && (typeof thisButton[5]["[open]"]!="undefined" && typeof thisButton[5]["[close]"]!="undefined") && typeof thisButton[5]["[toggle]"]=="undefined"){
                        actionString=' onmouseup="omega.TriggerAction({command:\'buttons\',targetState:\''+thisStateId2+'\',possibleStates:[\'[open]\',\'[close]\',\'[toggle]\'],target:\''+currentId2+'\',multi:true,selectedObject:this});"';//#click#
                      }
                      else{
                        tempEventData={command:'buttons',targetState:thisStateId2,target:currentId2};
                        enduringButton=true;
                      }
                    }
                  }
                }
                tempString='<button id="'+tempButtonId+'" class="p'+buttonId+' w'+buttonWidth+' '+cssClasses+'"'+valueString+actionString+'></button>';
              }
              tempTarget.innerHTML=tempString;
              if(enduringButton){
                omega.ApplyHandlerEnduring({targetId:tempButtonId,eventData:tempEventData});
              }
              else if(buttonMode=="autoRepeat"){
                omega.ApplyHandlerRepeat({targetId:tempButtonId,eventData:tempEventData,interval:buttonModeSettings});
              }
              if (mouseWheel){
                omega.ApplyHandlerMouseWheel({targetId:tempButtonId,eventData:tempMouseWheelEventData});
              }
            }
          }
        }
        count++;
      }
    }
    //omega.buttonsCreated=true;
  },
  updateButtons:function(){
    var count=0;
    for (var i=0; i<omega.buttons.length; i++){
      var thisButton=omega.buttons[i];
      var currentId=thisButton[0];
      var currentId2=omega.pageID+"/"+currentId;
      if (thisButton[1]=="macro" && thisButton[2]=="copy"){
        currentId2=thisButton[5]["buttonID"];
      }
      var buttonId1=parseInt(thisButton[3][0],10);
      if (buttonId1>-10){
        var buttonId=buttonId1;
        if (!omega.buttonViews || top.viewChoosen=="-" || thisButton[9].indexOf(top.viewChoosen)!=-1){
          var tempState="[?]"
          var tempVal="?";
          if (typeof top.buttonStates[currentId2]!="undefined"){
            tempState=top.buttonStates[currentId2]["state"];
            tempVal=top.buttonStates[currentId2]["value"];
          }
          var tempText=top.getText("files.json"+omega.pageID,currentId).replace(/{value}/g,tempVal);
          if (buttonId==-5){
            if (tempText.replace(/&nbsp;/g,'').trim()==""){
              tempText="&nbsp;"
            }
            else{
              tempText=tempText.replace(/&nbsp;/g,' ');
            }
            $(document.getElementById(count+":1B")).show();
            document.getElementById(count+":1B2").innerHTML =tempText;
          }
          else{
            if (buttonId==0){
              $(document.getElementById(count+":0B")).show();
              document.getElementById(count+":0B2").innerHTML =tempText+':';
            }
            for (var j=0; j<thisButton[4].length; j++){
              var thisStateId=thisButton[4][j];
              var thisStateId2=thisStateId;
              if (thisButton[1]=="macro" && thisButton[2]=="copy"){
                thisStateId2=thisButton[5][thisStateId][0];
              }
              if (top.states[top.statesIDArray[thisStateId]][3]==0){
                var buttonMode="std";
                var buttonModeSettings="";
                var rename="";
                if (typeof thisButton[7][thisStateId]!="undefined" && typeof thisButton[7][thisStateId]["buttonModes"]!="undefined"){
                  buttonMode=thisButton[7][thisStateId]["buttonModes"][0]["mode"]||"std";
                  buttonModeSettings=thisButton[7][thisStateId]["buttonModes"][0]["modeSettings"]||"";
                  rename=thisButton[7][thisStateId]["rename"]||"";
                  rename=rename.split(",")[0];
                }
                var tempTarget=document.getElementById(count+":"+(j+1)+'B2');
                $(document.getElementById(count+":"+(j+1)+'B')).show();
                if (buttonMode=="rgb"){
                  var tempValRGB=buttonModeSettings||tempVal;
                  tempTarget.value=tempValRGB;
                  if (top.recording || top.dashEditing){
                    tempTarget.innerHTML=top.getText('edit',0)+"...";
                    tempTarget.style.color=tempValRGB;
                  }
                }
                else{
                  $(tempTarget).removeClass('red yellow green default');
                  if (tempState=="[error]"){
                    $(tempTarget).addClass('red');
                  }
                  else if (tempState==thisStateId2){
                    $(tempTarget).addClass('green');
                  }
                  else if(tempState=="#"+thisStateId2){
                    $(tempTarget).addClass('yellow');
                  }
                  else{
                    if (buttonId1>=0){
                      $(tempTarget).addClass('default');
                    }
                  }
                  if(buttonMode=="dim"){
                    omega.dimSliders[currentId]["lastValFrom"]=tempVal;
                    if (omega.dimSliders[currentId]["setValOkFrom"]!=false){
                      top.dim.showDimVal(currentId);
                    }
                    if (rename==""){
                      rename="{value}%";
                    }
                  }
                  if (rename!=""){
                    tempTarget.innerHTML=rename.replace(/{value}/g,tempVal);
                  }
                  else{
                    if (buttonId1<=0){
                      tempTarget.innerHTML=top.getText('statesCfg.json',thisStateId).replace(/{value}/g,tempVal);
                    }
                    else if (tempTarget.innerHTML!=tempText){
                      tempTarget.innerHTML=tempText;
                    }
                  }
                }
              }
            }
          }
        }
        else{
          if (buttonId==-5){
            $(document.getElementById(count+":1B")).hide();
          }
          else{
            if (buttonId==0){
              $(document.getElementById(count+":0B")).hide();
            }
            for (var j=0; j<thisButton[4].length; j++){
              $(document.getElementById(count+":"+(j+1)+'B')).hide();
            }
          }
        }
        count++;
      }
    }
  },
  GetValue:function(o){//targetCategory,targetId,name
    if (typeof o.name=="undefined"){
      console.log("omega.GetValue: Parameter \"name\" is undefined!");
      return false;
    }
    if (typeof o.targetCategory=="undefined"){
      o.targetCategory=omega.deviceCategory;
    }
    if (typeof o.targetId=="undefined"){
      o.targetId=omega.deviceID;
    }
    return top.States[o.targetCategory][o.targetId][o.name];
  },
  GetSetting:function(o){//targetCategory,targetId,name
    if (typeof o.name=="undefined"){
      console.log("omega.GetSetting: Parameter \"name\" is undefined!");
      return false;
    }
    if (typeof o.targetCategory=="undefined"){
      o.targetCategory=omega.deviceCategory;
    }
    if (typeof o.targetId=="undefined"){
      o.targetId=omega.deviceID;
    }
    if (o.targetCategory=="interfaces"){
      return top.interfaces[top.interfacesIDArray[o.targetId]][2][o.name];
    }
    else if (o.targetCategory=="devices"){
      return top.devices[top.devicesIDArray[o.targetId]][2][o.name];
    }
    else if (o.targetCategory=="programs"){
      return top.programs[top.programsIDArray[o.targetId]][2][o.name];
    }
    else{
      return false;
    }
  },
  Update:function(o){
    var mode = o.mode || "data";
    top.reloadF(mode);
  },
  buttonActionDataArray:[],
  buttonAction:function(buttonI,thisStateId,actionIndex,button,data){
    var thisButton=omega.buttons[buttonI];
    if(actionIndex==0){
      omega.buttonActionDataArray=[];
    }
    else{
      omega.buttonActionDataArray.push(data);
    }
    var currentId=thisButton[0];
    var currentId2=omega.pageID+"/"+currentId;
    if (thisButton[1]=="macro" && thisButton[2]=="copy"){
      currentId2=thisButton[5]["buttonID"];
    }
    if (typeof thisButton[7][thisStateId]=="undefined" || thisButton[7][thisStateId]["buttonModes"].length<=actionIndex){
      var tempEventObject={command:'buttons',targetState:thisStateId,targetValue:omega.buttonActionDataArray,target:currentId2};
      if (thisButton[7][thisStateId]["buttonModes"][0]["mode"]=="dim"){
        tempEventObject.shadow=1;
      }
      omega.TriggerEvent(tempEventObject);
      return;
    }
    var tempVal="?";
    if (typeof top.buttonStates[currentId2]!="undefined"){
      tempVal=top.buttonStates[currentId2]["value"];
    }
    var tempText=top.replaceuml(top.getText("files.json"+omega.pageID,currentId),true).replace(/{value}/g,tempVal);
    var thisStateId2=thisStateId;
    if (thisButton[1]=="macro" && thisButton[2]=="copy"){
      thisStateId2=thisButton[5][thisStateId][0];
    }
    var buttonMode="none";
    var buttonModeSettings="";
    var buttonOnlyRecord=0;
    var buttonAfterThis=false;
    if (typeof thisButton[7][thisStateId]!="undefined"){
      buttonMode=thisButton[7][thisStateId]["buttonModes"][actionIndex]["mode"]||"none";
      buttonModeSettings=thisButton[7][thisStateId]["buttonModes"][actionIndex]["modeSettings"]||"";
      buttonOnlyRecord=thisButton[7][thisStateId]["buttonModes"][actionIndex]["onlyRecord"]||0;
      for (var z=(actionIndex+1); z<thisButton[7][thisStateId]["buttonModes"].length; z++){
        if (thisButton[7][thisStateId]["buttonModes"][z]["mode"]!="none" && (thisButton[7][thisStateId]["buttonModes"][z]["onlyRecord"]==0 || top.recording)){
          buttonAfterThis=true;
          break;
        }
      }
    }
    if(buttonOnlyRecord===0 || top.recording || top.dashEditing){
      var buttonModeArr=buttonModeSettings.split(",");
      for (var i=0; i<buttonModeArr.length; i++){
        buttonModeArr[i]=top.replaceuml(buttonModeArr[i],true).replace(/{value}/g,tempVal);
      }
      if (buttonMode=="dim"){
        top.dim.box.show(currentId,omega.createButtonExecute(thisStateId2,buttonI,button,actionIndex),tempVal,omega);
      }
      else if (buttonMode=="confirm"){
        var description=buttonModeArr[0]||tempText;
        top.submitBox(description,omega.createButtonExecute(thisStateId2,buttonI,button,actionIndex));
      }
      else if (buttonMode=="str"){
        var description=buttonModeArr[1]||tempText;
        top.showInputBox(tempText,description,omega.createButtonExecute(thisStateId2,buttonI,button,actionIndex),buttonModeArr[0]||"");
      }
      else if (buttonMode=="num"){
        top.showNumberBox(tempText,omega.createButtonExecute(thisStateId2,buttonI,button,actionIndex),buttonModeArr[0]||"",buttonModeArr[1]||"0",buttonModeArr[2]||"100",buttonModeArr[3]||"1");
      }
      else if (buttonMode=="sld"){
        top.sld.box.show(currentId,omega.createButtonExecute(thisStateId2,buttonI,button,actionIndex),buttonModeArr[0]||"",buttonModeArr[1]||"0",buttonModeArr[2]||"100",buttonModeArr[3]||"1",omega);
      }
      else if (buttonMode=="rgb"){
        top.rgb.box.show(currentId,omega.createButtonExecute(thisStateId2,buttonI,button,actionIndex),tempVal,omega);
      }
      else{
        omega.buttonAction(buttonI,thisStateId,(actionIndex+1),button);
      }
    }
    else{
      omega.buttonAction(buttonI,thisStateId,(actionIndex+1),button);
    }
  },
  createButtonExecute:function(thisStateId,buttonI,button,actionIndex){
    $(button).addClass('blinking');
    return function (o){
      $(button).removeClass('blinking');
      if (o.OK){
        omega.buttonAction(buttonI,thisStateId,(actionIndex+1),button,o.data);
      }
    }
  },
  createEventExecute:function(command,payload,selectedObject){
    return function (o){
      if (o.OK){
        var lable=o.lable;
        var targetState='[value]';
        var targetValue=[o.data];
        if (lable){
          lable+=" "+top.getText('statesCfg.json','[set]');
          for (var i=0; i<targetValue.length; i++){
            var tempstate=top.getText('statesCfg.json',targetValue[i]).replace(/<br>/g," ");
            if (tempstate=="undefined"){
              tempstate=targetValue[i];
            }
            if (tempstate=="{value}"){
              tempstate=top.getText('statesCfg.json','[set]');
            }
            lable+=" "+tempstate;
          }
        }
        omega.TriggerEvent({command:command,targetState:targetState,targetValue:targetValue,lable:lable,data:payload});
      }
    }
  },
  lastTriggerCheckId:"",
  multiTriggerCheckClicks:0,
  MultiTriggerCheck:function(o){//id,time,callback
    if (typeof o.id=="undefined"){
      console.log("omega.MultiTriggerCheck: Parameter \"id\" is undefined!");
      return 0;
    }
    var tempTime=o.time||300;
    clearTimeout(omega.multiTriggerTimeout);
    omega.multiTriggerTimeout=setTimeout(omega.resetMultiTriggerCheck(o.callback),tempTime);
    if (omega.lastTriggerCheckId==o.id){
      omega.multiTriggerCheckClicks+=1;
    }
    else{
      omega.lastTriggerCheckId=o.id;
      omega.multiTriggerCheckClicks=1;
    }
    return omega.multiTriggerCheckClicks;
  },
  resetMultiTriggerCheck:function(callback){
    return function(){
      omega.lastTriggerCheckId="";
      if (typeof callback=="function"){
        callback(omega.multiTriggerCheckClicks);
      }
    };
  },
  buttonPressInterval:{},
  buttonPressF:function(id,func,interval){
    interval=interval||0.5;
    interval=interval*1000;
    window.clearInterval(omega.buttonPressInterval[id]);
    func();
    omega.buttonPressInterval[id]=window.setInterval(func,interval);
  },
  lastEnduringEventId:"",
  buttonEnduringPressF:function(id,func){
    window.clearInterval(omega.buttonPressInterval[id]);
    window.clearInterval(omega.buttonPressInterval[omega.lastEnduringEventId]);
    omega.lastEnduringEventId=id;
    func();
    omega.buttonPressInterval[id]=window.setInterval('omega.RepeatEnduringEvent();',1000);
  },
  buttonUnpressF:function(id){
    window.clearInterval(omega.buttonPressInterval[id]);
  },
  buttonEnduringUnpressF:function(id){
    omega.buttonUnpressF(id);
    omega.EndLastEvent();
  },
  touchControlStart:function(event){
    omega.preventDefault(event);
    $(event.target).triggerHandler("mousedown");
  },
  touchControlEnd:function(event){
    omega.preventDefault(event);
    $(event.target).triggerHandler("mouseup");
  },
  touchControlOut:function(event){
    //omega.preventDefault(event);
    $(event.target).triggerHandler("mouseout");
  },
  preventDefault:function(e){
    e.preventDefault && e.preventDefault();
    e.stopPropagation && e.stopPropagation();
    e.cancelBubble = true;
    e.returnValue = false;
    return false;
  },
  insert:function(aTag, eTag, target) {//unused, because moved to top, still needed?
    target.focus();
    if(typeof document.selection != 'undefined'){// for Internet Explorer 
      var range = document.selection.createRange();
      var insText = range.text;
      range.text = aTag + insText + eTag;
      range = document.selection.createRange();
      if (insText.length == 0) {
        range.move('character', -eTag.length);
      } else {
        range.moveStart('character', aTag.length + insText.length + eTag.length);      
      }
      range.select();
    }
    else if(typeof target.selectionStart != 'undefined'){// others 
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
  },
  PAGE_TITLE:"",
  CreateModeMenu:function(o){//targetElement,targetId,maxCols,startVisibleMinWidth,printNoTable,showStates,record
    if (omega.IS_FRAME_SET==false){
      console.log("omega.CreateModeMenu: This function can only be used on pages with subpages!");
      return false;
    }
    if (typeof o.printNoTable!="boolean"){
      o.printNoTable=false;
    }
    var targetElement;
    if (typeof o.targetElement!="object" && typeof o.targetElement!="undefined" && o.printNoTable==false){
      console.log("omega.CreateModeMenu: Parameter \"targetElement\" is not an object!");
      return false;
    }
    else if (typeof o.targetElement=="undefined" && typeof o.targetId!="string" && o.printNoTable==false){
      console.log("omega.CreateModeMenu: Parameter \"targetElement\" is undefined and parameter \"targetId\" is undefined or not a string!");
      return false;
    }
    else{
      targetElement=o.targetElement||document.getElementById(o.targetId);
    }
    if (typeof o.showStates!="boolean"){
      o.showStates=false;
    }
    if (typeof o.record!="boolean"){
      o.record=true;
    }
    if (typeof o.startVisibleMinWidth!="number" || o.startVisibleMinWidth<0){
      o.startVisibleMinWidth=1050;
    }
    if (typeof o.maxCols!="number" || o.maxCols<1){
      o.maxCols=2;
    }
    omega.pageWidth=41*o.maxCols+3;
    omega.thisFramesArray = [];
    var framesstr='<table class="frameTable" border="0" cellpadding="0" cellspacing="0"><tr>';
    for (var i=0; i<top.files.length; i++){
      if (top.files[i][1]==omega.pageID){
        omega.subPages.push(i);
        if (omega.thisFramesArray.indexOf(top.files[i][6])==-1 && top.files[i][6]!="showframe"){
          omega.thisFramesArray.push(top.files[i][6]);
          framesstr+='<td class="subFrames" style="display:none;" id="'+top.files[i][6]+'"><iframe style="height:100%; width:100%; margin-bottom:-3px;" name="'+top.files[i][6]+'" frameborder="0" allowtransparency="true"></iframe></td>';
        }
      }
    }
    $(document.body).wrapInner('<table class="menuTable" cellpadding="0" cellspacing="0" border="0"><tr><td id="controlsC" class="rightBorder"><div class="scrollable"></div></td><td class="subFrames">'+framesstr+'<td id="dummyC" style="display:none;"><br></td></tr></table></td></tr></table>');
    if (o.maxCols>2){
      $(document.getElementById("controlsC")).prepend('<div class="hideBackground"></div><div id="hideB"></div>');
      if (typeof top.menuHide[omega.pageID]=="undefined"){
        if (top.globalWindowWidth>=o.startVisibleMinWidth){
          top.menuHide[omega.pageID]=0;
        }
        else{
          top.menuHide[omega.pageID]=1;
        }
      }
      omega.hideMenu(top.menuHide[omega.pageID],false);
    }
    else{
      $(document.getElementById("controlsC")).prepend('<div class="hideBackground"></div>');
      document.getElementById("controlsC").style.width=85;
    }
    if (o.printNoTable==false){
      var modesstr='<table border="0" cellpadding="0" cellspacing="3"><tr><td><button class="p2 w2 defaultNH">'+top.getText('mode',0)+':</button></td>';
      if (o.showStates){
        modesstr+='<td class="hideThis"><button class="p2 w2 defaultNH">'+top.getText('status',0)+':</button></td>';
      }
      modesstr+='</tr>';
      for (var i=0; i<omega.subPages.length;i++){
        modesstr+='<tr id="omegaMode'+i+'R"><td><button id="omegaMode'+i+'B" class="p1 w2"></button></td>';
        if (o.showStates){
          modesstr+='<td class="hideThis"><button id="omegaMode'+i+'S" class="p1 w2 defaultNH"></button></td>';
        }
        modesstr+='</tr>';
      }
      modesstr+='</table>';
      targetElement.innerHTML=modesstr;
    }
    omega.modeMenu.enabled=true;
    omega.modeMenu.showStates=o.showStates;
    omega.modeMenu.record=o.record;
    return true;
  },
  niceScrollObjects:[],
  onMenuHideArray:[],
  OnMenuHide:function(func){
    if (omega.IS_FRAME_SET==false){
      console.log("omega.OnMenuHide: This function can only be used on pages with subpages!");
      return false;
    }
    if (typeof func!="function"){
      console.log("omega.OnMenuHide: 1st parameter is undefined or not a function!");
      return false;
    }
    omega.onMenuHideArray.push({func:func});
    return true;
  },
  onMenuShowArray:[],
  OnMenuShow:function(func){
    if (omega.IS_FRAME_SET==false){
      console.log("omega.OnMenuShow: This function can only be used on pages with subpages!");
      return false;
    }
    if (typeof func!="function"){
      console.log("omega.OnMenuShow: 1st parameter is undefined or not a function!");
      return false;
    }
    omega.onMenuShowArray.push({func:func});
    return true;
  },
  hideElementsToHide:function(onOff){
    if (onOff){
      for (var i in omega.onMenuHideArray){
        omega.onMenuHideArray[i]["func"]();
      }
      $(".hideThis").hide();
    }
    else{
      for (var i in omega.onMenuShowArray){
        omega.onMenuShowArray[i]["func"]();
      }
      $(".hideThis").show();
    }
  },
  showScrollBars:function(){
    for (var i = 0; i < omega.niceScrollObjects.length; i++){
      omega.niceScrollObjects[i].resize();
      omega.niceScrollObjects[i].show();
    }
  },
  showActualFrame:function(){
    if(top.loadedFiles[top.choosenFramesetPageArray[omega.pageID]] && document.getElementById(top.files[top.nextChoosenFramesetPageArray[omega.pageID]][6]).style.display=="none"){
      //console.log("show: "+top.files[top.nextChoosenFramesetPageArray[omega.pageID]][6]);
      $(document.getElementById(top.files[top.nextChoosenFramesetPageArray[omega.pageID]][6])).animate({width:"show",opacity:"show"},top.userSettings["effectTimePage"],"swing",function(){
        $(document.getElementById("dummyC")).hide(0,function(){
          $(document.getElementById(top.files[top.nextChoosenFramesetPageArray[omega.pageID]][6])).show()//somehow needed for more complex openPages...
        });
        //$(document.getElementById("dummyC")).hide();
      });
    }
  },
  hideActualFrame:function(){
    //console.log("hide: "+top.files[top.choosenFramesetPageArray[omega.pageID]][6]);
    $(document.getElementById("dummyC")).show(0,function(){
      $(document.getElementById(top.files[top.choosenFramesetPageArray[omega.pageID]][6])).hide();
    });
    //$(document.getElementById(top.files[top.choosenFramesetPageArray[omega.pageID]][6])).hide();
  },
  hideMenu:function(hidev,animation) {
    var telement=document.getElementById("controlsC");
    var target=85;
    if (hidev==1){
      top.menuHide[omega.pageID]=1;
      document.getElementById('hideB').innerHTML='<button class="p1 w2 transparent" onClick="omega.hideMenu(0,true);">&gt;&gt;</button>';
      window.setTimeout('omega.hideElementsToHide(true);',top.userSettings["effectTimeSlide"]);
      //omega.hideElementsToHide(true);
    }
    else{
      target=omega.pageWidth;
      top.menuHide[omega.pageID]=0;
      document.getElementById('hideB').innerHTML='<button class="p1 w2 default" onClick="omega.hideMenu(1,true);">&lt;&lt;</button>';
      omega.hideElementsToHide(false);
      //window.setTimeout('omega.hideElementsToHide(false);',top.userSettings["effectTimeSlide"]);
    }
    if (animation){
      for (var i = 0; i < omega.niceScrollObjects.length; i++){
        omega.niceScrollObjects[i].hide();
      }
      telement.style.transition="width "+top.userSettings["effectTimeSlide"]+"ms";
      window.setTimeout("omega.showScrollBars();",parseInt(top.userSettings["effectTimeSlide"]));
    }
    else{
      telement.style.transition="width 0s";
    }
    telement.style.width=target+"px";
  },
  frameHideAll:function(hidev){
    if (hidev==1){
      if (omega.pageTitleIsHidden){
        $(document.getElementById("controlsC")).hide();
      }
      else{
        $(document.getElementById('titleC')).hide(0,function(){$(document.getElementById("controlsC")).hide()});
      }
    }
    else {
      if (omega.pageTitleIsHidden){
        $(document.getElementById("controlsC")).show();
      }
      else{
        $(document.getElementById("controlsC")).show(0,function(){$(document.getElementById('titleC')).show()});
      }
    }
  },
  pageTitleIsHidden:false,
  RemovePageTitle:function(){
    if (document.getElementById('titleC')!=null){
      $(document.getElementById('titleC')).hide();
    }
    omega.pageTitleIsHidden=true;
  },
  GetUserSetting:function(o){//name,global
    if (typeof o.name!="string"){
      console.log("omega.GetUserSetting: Parameter \"name\" is undefined or not a string!");
      return;
    }
    if (o.global){
      return top.userSettings[o.name];
    }
    else{
      try{
        return top.userSettings[omega.deviceCategory][omega.deviceID][o.name];
      }
      catch(e){
        return;
      }
    }
  },
  SetUserSetting:function(o){//name,value,callback,useDevice
    if (typeof o.name!="string"){
      console.log("omega.SetUserSetting: Parameter \"name\" is undefined or not a string!");
      return false;
    }
    if (typeof o.value=="undefined"){
      console.log("omega.SetUserSetting: Parameter \"value\" is undefined!");
      return false;
    }
    if (typeof top.userSettings[omega.deviceCategory]=="undefined"){
      top.userSettings[omega.deviceCategory]={};
      top.userSettings1[omega.deviceCategory]={};
    }
    if (o.useDevice && typeof top.userSettingsDevice[omega.deviceCategory]=="undefined"){
      top.userSettingsDevice[omega.deviceCategory]={};
    }
    if (typeof top.userSettings[omega.deviceCategory][omega.deviceID]=="undefined"){
      top.userSettings[omega.deviceCategory][omega.deviceID]={};
      top.userSettings1[omega.deviceCategory][omega.deviceID]={};
    }
    if (o.useDevice && typeof top.userSettingsDevice[omega.deviceCategory][omega.deviceID]=="undefined"){
      top.userSettingsDevice[omega.deviceCategory][omega.deviceID]={};
    }
    if (o.useDevice){
      top.userSettings1[omega.deviceCategory][omega.deviceID][o.name]="[deviceSetting]";
      top.userSettingsDevice[omega.deviceCategory][omega.deviceID][o.name]=o.value;
    }
    else{
      top.userSettings1[omega.deviceCategory][omega.deviceID][o.name]=o.value;
    }
    top.userSettings[omega.deviceCategory][omega.deviceID][o.name]=o.value;
    top.saveUserSettings(o.callback,250);
    return true;
  },
  SetFullscreen:function(o){//active
    var tempMode;
    if (o.active){
      tempMode=2;
    }
    else{
      tempMode=0;
    }
    return top.fullscreen(tempMode,omega.pageID);
  },
  onBeforeUnloadArray:[],
  OnBeforeUnload:function(func){
    if (typeof func!="function"){
      console.log("omega.OnBeforeUnload: 1st parameter is undefined or not a function!");
      return false;
    }
    omega.onBeforeUnloadArray.push({func:func});
    return true;
  },
  Request:function(o){
    var finaldict={};
    if (typeof o.method!="string"){
      console.log("omega.Request: Parameter \"method\" is undefined or not a string!");
      return false;
    }
    else{
        finaldict.method=o.method;
    }
    if (typeof o.targetpc!="string"){
        if (omega.deviceCategory=="programs"){
            finaldict.targetpc=top.programs[top.programsIDArray[omega.deviceID]][3];
        }
        else if (omega.pageID!="system" && omega.deviceCategory=="devices" && top.devices[top.devicesIDArray[omega.deviceID]][1]=="PC_WIN"){
            finaldict.targetpc=omega.deviceID;
        }
        else{
            finaldict.targetpc="";
        }
    }
    else{
        finaldict.targetpc=o.targetpc;
    }
    if (typeof o.args=="object"){
        finaldict.args=o.args;
    }
    else if (typeof o.args!="undefined"){
        console.log("omega.Request: Parameter \"args\" is not an array!");
        return false;
    }
    if (typeof o.kwargs=="object"){
        finaldict.kwargs=o.kwargs;
    }
    else if (typeof o.kwargs!="undefined"){
        console.log("omega.Request: Parameter \"kwargs\" is not a dictionary!");
        return false;
    }
    $.post("/empty",JSON.stringify(finaldict), o.callback);
    return true;
  },
}
//deviceID,buttons,subPages,pageID

//console.log(omega.FRAME_NAME+top.toOpenFramesArray[omega.FRAME_NAME]);
if (top.allFramesArray.indexOf(omega.FRAME_NAME)==-1 || (typeof top.toOpenFramesArray[omega.FRAME_NAME]!="undefined" && top.toOpenFramesArray[omega.FRAME_NAME]!=-1 && top.files[top.toOpenFramesArray[omega.FRAME_NAME]][9]===1)){
  omega.pageID="system";
  omega.deviceCategory="devices";
  omega.pageTitleIsHidden=true;
  try{
    omega.pageID2=parent.omega.pageID+omega.FRAME_NAME;
  }
  catch(e){
    omega.pageID2=omega.pageID+omega.FRAME_NAME;
  }
  if (typeof top.backHashCount[omega.pageID2]=="undefined"){
    top.backHashCount[omega.pageID2]=0;
  }
}
else{
  omega.pageID=top.files[top.toOpenFramesArray[omega.FRAME_NAME]][0];
  omega.buttons=top.files[top.filesIDArray[omega.pageID]][5];
  omega.buttonViews=top.buttonViewsForPage[omega.pageID];
  var temp=top.files[top.filesIDArray[omega.pageID]][2].split("/");
  omega.deviceCategory=temp[0];
  omega.deviceID=temp[1];
  if (top.allFramesetsArray.indexOf(omega.pageID)!=-1){
    omega.IS_FRAME_SET=true;
    omega.frames=window.frames;
    omega.useNiceScroll=false;
  }
  omega.PAGE_TITLE=top.getText('files.json',omega.pageID).replace(/<br>/g," ");
  if (omega.PAGE_TITLE==""){
    omega.pageTitleIsHidden=true;
  }
  omega.pageID2=omega.pageID;
}
omega.IS_TOUCH_DEVICE=top.touchDevice;

window.location.hash="back";
window.location.hash="back2";//again because google chrome don't insert first hash into history
window.onhashchange=function(){
  //console.log(window.location.hash+" = "+omega.pageID2);
  if (window.location.hash=="#back2"){
    top.backHashCount[omega.pageID2]++;
    if (top.backHashCount[omega.pageID2]>1){
      var tempPageId=omega.pageID;
      //while(tempPageId=="system"){
      //  tempPageId=parent.omega.pageID;
      //}
      //var tempFileId=top.filesIDArray[tempPageId];
      //if(top.files[tempFileId][1]!="-"){
      //  tempFileId=top.files[tempFileId][1];
      //}
      //console.log("goBack "+tempPageId);
      if (tempPageId=="dashboard"){
        top.blankSubPages2(top.filesIDArray[tempPageId]);
      }
      top.openPage('back',false,top.fullscreenEnabled,false,-2);
    }
    window.location.hash="back";
  }
  else if(window.location.hash!="#back"){
    top.backHashCount[omega.pageID2]=0;
    window.location.hash="back2";
  }
}

$(document).ready(function(){
  for (var i in omega.onLoadArray){
    omega.onLoadArray[i].func();
  }
  if (omega.IS_TOUCH_DEVICE==false){
    if (omega.useNiceScroll){
      omega.niceScroll=$(document.body).niceScroll({horizrailenabled:false,cursorcolor:"red",cursorborder:"0px",spacebarenabled:false,enablekeyboard:false,smoothscroll:true,enablemouselockapi:false,scrollspeed:80,preservenativescrolling:true,enablemousewheel:true,disablemutationobserver:true,zindex:99});
      //console.log(omega.niceScroll);
    }
    var niceScrollElements=document.getElementsByClassName("scrollable");
    for (var i = 0; i < niceScrollElements.length; i++){
      omega.niceScrollObjects.push($(niceScrollElements[i]).niceScroll({horizrailenabled:false,cursorcolor:"red",cursorborder:"0px",spacebarenabled:false,enablekeyboard:false,smoothscroll:true,enablemouselockapi:false,scrollspeed:80,preservenativescrolling:true,enablemousewheel:true,disablemutationobserver:true,zindex:99}));
    }
  }
  else{
    omega.useNiceScroll=false;
    //$(document).bind('mouseover',function(e){
    //  omega.preventDefault(e);
    //});
    try {
      var ignore = /:hover/;
      for (var i = 0; i < document.styleSheets.length; i++) {
        var sheet = document.styleSheets[i];
        if (!sheet.cssRules) {
          continue;
        }
        for (var j = sheet.cssRules.length - 1; j >= 0; j--) {
          var rule = sheet.cssRules[j];
          if (rule.type === CSSRule.STYLE_RULE && ignore.test(rule.selectorText)) {
            sheet.deleteRule(j);
          }
        }
      }
    }
    catch(e) {
    } 
  }
  $(document).bind('click',function(e){
    e.stopPropagation();
    //omega.preventDefault(e);//??
  });
  omega.createButtons();
  if (omega.pageID!="system"){
    if (omega.pageTitleIsHidden==false){
      if (typeof top.files[top.filesIDArray[omega.pageID]][4][top.primHifiID]!="undefined" && top.files[top.filesIDArray[omega.pageID]][4][top.primHifiID][0]!="" && typeof top.States["devices"][top.primHifiID]["input"]!="undefined"){
        $(document.body).prepend('<div id="titleC" onClick="top.Request(JSON.stringify({\'method\':\'TriggerEvent\',\'kwargs\':{\'suffix\':\'EXT.'+top.devices[top.devicesIDArray[top.primHifiID]][3]+'.devices.'+top.devices[top.devicesIDArray[top.primHifiID]][1]+'.input\',\'payload\':{\'target\':\''+top.primHifiID+'\',\'targetState\':\'[value]\',\'targetValue\':[\''+top.files[top.filesIDArray[omega.pageID]][4][top.primHifiID][0]+'\',null,null,null]}}}));" class="title1">'+omega.PAGE_TITLE+':</div>');
      }
      else{
          $(document.body).prepend('<div id="titleC" class="title1">'+omega.PAGE_TITLE+':</div>');
      }
    }
    top.pageOpened(omega.pageID,omega);
  }
});