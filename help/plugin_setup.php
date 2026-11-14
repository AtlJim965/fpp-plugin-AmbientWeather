<?php
// Help for the settings page (Content Setup > Ambient Weather Display). FPP
// shows it in its help window when you press F1 or the help button there:
// plugin.php?plugin=fpp-plugin-AmbientWeather&nopage=1&page=help/plugin_setup.php
?>
<style>
#fppawhelp h3 { font-size: 1.15rem; margin-top: 1.25rem; }
#fppawhelp dt { margin-top: .5rem; }
#fppawhelp dd { margin-left: 1rem; margin-bottom: .25rem; }
</style>

<div id="fppawhelp">
  <h2 class="h4">Ambient Weather Display help</h2>
  <p>Shows the temperature and wind from your Ambient Weather station on a
    Pixel Overlay Model. Nothing is saved until you press <b>Save</b> or
    <b>Save &amp; Show Now</b>.</p>

  <h3>Ambient Weather account</h3>
  <dl>
    <dt>API Key, Application Key</dt>
    <dd>From ambientweather.net &gt; Account &gt; API Keys. Once saved they
      aren't shown again; leave the boxes blank to keep them, or type a new
      key to replace one. "401 Unauthorized" means one is wrong or they are
      swapped.</dd>
    <dt>Station MAC</dt>
    <dd>Only needed if your account has more than one station. Blank uses the
      first one.</dd>
  </dl>

  <h3>Matrix display</h3>
  <dl>
    <dt>Overlay Model</dt><dd>The Pixel Overlay Model to draw on.</dd>
    <dt>Message</dt>
    <dd><code>{temp}</code> and <code>{wind}</code> are replaced with the live
      readings. Text without them gets the readings added at the end. With the
      border on, <code>|</code> starts a new line.</dd>
    <dt>Show wind gust</dt><dd>"Wind 5 G12 mph" instead of "Wind 5 mph".</dd>
    <dt>Font, Font size</dt><dd>For text without the border.</dd>
    <dt>Text colors</dt>
    <dd>One color, or a different color per letter, word or line, random
      colors, a gradient, Sparkle or Chase. Pick a <b>Color palette</b>
      (Rainbow, Christmas, ...) or <b>Custom</b> to choose up to five colors.
      <b>Color movement</b> above 0 makes the colors flow (scrolling text
      only; needed for Sparkle and Chase). Multi-color scrolling text needs
      FPP 10.2 or newer.</dd>
    <dt>Position, Scroll speed</dt>
    <dd>Center for still text, or a scrolling direction and its speed in
      pixels per second.</dd>
    <dt>Default loop interval</dt>
    <dd>Seconds between updates for <code>--loop</code> without a number (at
      least 30).</dd>
  </dl>

  <h3>Christmas border</h3>
  <dl>
    <dt>Show border</dt>
    <dd>A striped border with the message drawn inside it in a pixel font,
      as large as fits. Font, Font size and Position aren't used.</dd>
    <dt>Border colors, Custom colors</dt>
    <dd>A ready-made set, or Custom with a comma-separated list such as
      <code>#FF0000,#FFFFFF,#00C83C</code>.</dd>
    <dt>Border thickness, Stripe length</dt><dd>In pixels.</dd>
    <dt>Chase, Chase speed</dt>
    <dd>Move the stripes around the edge while running with
      <code>--loop</code>.</dd>
  </dl>

  <h3>Buttons</h3>
  <dl>
    <dt>Save &amp; Show Now</dt>
    <dd>Saves, then shows the weather once. The result or error appears
      below the buttons.</dd>
    <dt>Turn Display Off</dt>
    <dd>Stops a running display, clears it and puts the overlay model back
      the way it was.</dd>
  </dl>

  <h3>Playlists and the scheduler</h3>
  <p>Add <b>Run Script &gt; AmbientWeather.sh</b> with <code>--loop 60</code>
    to keep it updating, <code>--off</code> to stop it, or
    <code>--text "..."</code> for different wording. A running loop reads the
    settings when it starts, so restart it after changing them.</p>

  <p>More: the plugin's DOCUMENTATION.md on GitHub, and its log in
    Content Setup &gt; File Manager &gt; Logs
    (<code>plugin-fpp-plugin-AmbientWeather.log</code>).</p>
</div>
