:: v1.1
@echo off
echo The O-MEGA Project
echo Copyright (C) 2020 Thomas Bott
echo.
echo This program is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation; either version 2 of the License, or (at your option) any later version.
echo.
echo This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
echo.
echo You should have received a copy of the GNU General Public License along with this program; if not, write to the Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA
echo.
echo By proceeding you agree with these terms and conditions.
pause
echo.
echo Please make sure EventGhost is installed on your PC and only proceed if this is the case!
pause
echo.
set /p server="There can only be one PC that has the server role. Is this your server PC? (Y/N)"
set res=false
If %server%==Y set res=true
if %server%==y set res=true
If %res%==true (
    xcopy "%~dp0\web" "%appdata%\EventGhost\plugins\O-MEGA\web\" /E /Y
    del "%appdata%\EventGhost\plugins\O-MEGA\web\config\doku.json" /F  
    reg add HKCU\Software\EventGhost\O-MEGA /v server /t REG_SZ /d 1 /f
) else (
    reg add HKCU\Software\EventGhost\O-MEGA /v server /t REG_SZ /d 0 /f
)
xcopy "%~dp0\plugin" "%programdata%\EventGhost\plugins\O-MEGA\" /E /Y
echo.
echo After you imported the O-MEGA plugin to EventGhost, you now need to add the plugin to your configuration tree inside EventGhost.
echo Watch the EventGhost Log while you do that, it maybe required to add some other plugings to your configuration before the O-MEGA plugin can work and the log will tell you what you need to do!
pause
echo.
echo The installation is now complete. Thank you for installing the O-MEGA plugin.
echo Have fun! :)
pause