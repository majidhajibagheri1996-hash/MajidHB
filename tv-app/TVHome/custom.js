/* Personal settings baked into the app. Everything here can also be changed
 * on the TV from the Settings tile; these are only the starting values. */
window.TVHOME_CUSTOM = {
  name: 'Majid',                       // shown in the greeting
  city: 'Waterloo',                    // label for the weather widget
  latitude: 43.4643,                   // weather location
  longitude: -80.5204,

  // Websites that get their own tile; they open in Samsung's Internet app.
  websites: [
    { name: '30nama', url: 'https://30nama.com/' }
  ],

  // "My photos (from phone)": every image in this GitHub folder becomes a background.
  // Upload photos there from your phone; the TV picks them up within 30 minutes
  // (or right away when the app is reopened). The repository is public.
  photoFeed: {
    owner: 'majidhajibagheri1996-hash',
    repo: 'MajidHB',
    branch: 'ccr-926cf38e-r05h1c',
    folder: 'tv-photos'
  },

  // Images in the backgrounds/ folder. Add your own files there and list them here.
  backgrounds: [
    { name: 'Aurora', file: 'backgrounds/aurora.jpg' },
    { name: 'Dusk',   file: 'backgrounds/dusk.jpg' },
    { name: 'Ocean',  file: 'backgrounds/ocean.jpg' }
  ]
};
