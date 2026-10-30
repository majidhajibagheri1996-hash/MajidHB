TVHome - your own customizable home screen for the Samsung QN70Q60D (Tizen)
==========================================================================

WHAT'S IN THIS FOLDER
  TVHome.wgt    the customizable home screen (install this)
  30nama.wgt    a 30nama app: opens the site straight in the TV's Internet app
  TVHome\, Nama\  the apps' source, used by install.ps1 (Option B)
  install.ps1   install script for Option B

Paths and menu names below come from public guides and have not been tested on
your exact TV. If a step looks different, take a phone photo and send it to Claude.


STEP 1 - TURN ON DEVELOPER MODE ON THE TV (one time)
  1. Find the IP address of the device you will install from (phone OR PC):
       Android: Settings > About phone > Status > IP address  (or Wi-Fi > your network)
       Windows: open PowerShell, type  ipconfig , use "IPv4 Address"
  2. On the TV: press Home > go to Apps.
  3. On the Apps screen type 1 2 3 4 5 on the remote
     (SolarCell remote: press the 123 button to show the number pad).
  4. Turn Developer mode ON, enter the IP from step 1 as "Host PC IP", press OK.
  5. Restart the TV fully: hold the remote's power button until it turns off and back on.


STEP 2 (OPTION A, EASIEST) - INSTALL WITH APPS2SAMSUNG
  Apps2Samsung is a free community tool (not made by Samsung or Claude) that
  creates the Samsung signing certificate and installs custom apps for you.
  Download: https://github.com/Apps2Samsung/Apps2Samsung/releases
    Windows: the Windows file from the latest Stable release
    Android: the file ending in -android.apk (allow "install unknown apps")
  Then:
  1. Copy TVHome.wgt to the phone or PC.
  2. Open Apps2Samsung, pick your TV (or type its IP:
     TV Settings > All Settings > Connection > Network > Network Status > IP Settings).
  3. Choose "custom .wgt" and select TVHome.wgt. Repeat for 30nama.wgt if you
     want 30nama as its own app on Samsung's home row too.
  4. First time only: sign in to your Samsung account when asked (for the certificate).
  5. Install. "Home" appears in the TV's Apps list.


STEP 2 (OPTION B, BACKUP) - INSTALL WITH SAMSUNG'S TIZEN STUDIO ON WINDOWS
  1. Install Tizen Studio to C:\tizen-studio:
     https://developer.tizen.org/development/tizen-studio/download
  2. In Package Manager > Extension SDK, install "Samsung Certificate Extension"
     and "TV Extensions".
  3. Tizen Studio > Tools > Device Manager > Remote Device Manager > + >
     TV IP, port 26101 > Add, then switch Connection on.
  4. Tools > Certificate Manager > + > Samsung > TV > profile name: TVHome >
     new author certificate > sign in with Samsung account > distributor:
     Public (your TV's DUID should already be listed) > Finish.
  5. In this folder: Shift + right-click > Open PowerShell window here, then:
       Set-ExecutionPolicy -Scope Process Bypass
       .\install.ps1 -TvIp <TV IP> -CertProfile TVHome
       .\install.ps1 -TvIp <TV IP> -CertProfile TVHome -App Nama   (30nama app)


STEP 3 - PUT IT FIRST ON THE TV
  Home > Apps > find "Home" > add it to the home row and move it to the first spot.


USING IT (REMOTE)
  Left / Right     move between apps
  OK               open the app
  Hold OK or Down  Move / Remove menu for that app
  "+" tile         choose which installed apps appear (OK toggles, Back = done)
  Gear tile        CUSTOMIZE:
                     background (gradient, Aurora, Dusk, Ocean, or slideshow),
                     slideshow speed, darkness, 12/24-hour clock, date,
                     greeting, weather, tile size, glass/colorful tiles,
                     corner shape, highlight color, row position, hints
  Back             close the app


YOUR OWN PHOTOS FROM YOUR PHONE (no reinstall needed)
  1. On the phone open:
     https://github.com/majidhajibagheri1996-hash/MajidHB/tree/ccr-926cf38e-r05h1c/tv-photos
     (sign in to GitHub).
  2. Tap "Add file" > "Upload files", pick photos, tap "Commit changes".
  3. On the TV: Gear tile > Background > "My photos (from phone)".
     New photos appear within 30 minutes, or right away if you reopen the app.
     Several photos rotate as a slideshow (speed: "Slideshow every").
  To remove a photo: open it on GitHub > "..." menu > Delete file.
  PRIVACY: this GitHub repository is public - anyone can see these photos.
  Don't upload anything private.

30NAMA
  A "30nama" tile is already in the TVHome app row. It opens 30nama.com in
  Samsung's Internet app, which has the pointer you need to use a website
  with the remote. 30nama.wgt does the same from Samsung's own home row.
  Your login stays saved in the Internet app. Note: the site may still
  load fresh each time it's opened; this saves the steps, not the loading.

NAME / CITY / MORE WEBSITES
  Tell Claude in the chat; Claude rebuilds the app and you reinstall
  (Step 2). Settings and app choices you made on the TV are kept.


HONEST LIMITS
  - It does not replace Samsung's own home screen (Tizen does not allow that);
    it is an app you open from the first spot on the home row.
  - The Samsung certificate is temporary (roughly a year, as far as I know);
    then reinstall with Step 2.
  - Opening other apps and showing their icons has not yet been tested on your
    TV. If something fails, an error appears at the top of the screen -
    photograph it and send it to Claude.
