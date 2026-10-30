# Samsung TV apps (Tizen)

- `TVHome/` – customizable Apple TV style home screen (backgrounds, widgets, app row,
  website tiles). Personal values live in `TVHome/custom.js`.
- `Nama/` – shortcut app that opens https://30nama.com/ in the TV's Internet app.
- `install.ps1` – packages and installs an app folder with Tizen Studio on Windows.

To build an installable `.wgt`, zip the *contents* of an app folder (so `config.xml`
is at the root of the zip) and rename it to `.wgt`. Install it with Apps2Samsung
(https://github.com/Apps2Samsung/Apps2Samsung) or Tizen Studio.
