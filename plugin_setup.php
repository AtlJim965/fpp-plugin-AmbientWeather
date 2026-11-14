<?php
// fpp-plugin-AmbientWeather settings page
// Settings: config/plugin.fpp-plugin-AmbientWeather (FPP's plugin settings
// format). Ambient Weather keys: plugindata/fpp-plugin-AmbientWeather/
// credentials.json (0600) - never printed back into the page.
$awPlugin     = "fpp-plugin-AmbientWeather";
$awMedia      = (isset($settings['mediaDirectory']) && $settings['mediaDirectory'] !== '')
                ? $settings['mediaDirectory'] : (getenv("MEDIADIR") ?: "/home/fpp/media");
$awConfigFile = "$awMedia/config/plugin.$awPlugin";
$awDataDir    = "$awMedia/plugindata/$awPlugin";
$awCredFile   = "$awDataDir/credentials.json";
$awScript     = dirname(__FILE__) . "/ambient_weather.py";

$awDefaults = array(
    "api_key"         => "",
    "application_key" => "",
    "station_mac"     => "",
    "fpp_host"        => "http://127.0.0.1",
    "model_name"      => "LED Panels",
    "font"            => "FreeSans",
    "font_size"       => 22,
    "color"           => "#FFFFFF",
    "text_color_mode"  => "Single",
    "text_palette"     => "Rainbow",
    "text_num_colors"  => 2,
    "text_color2"      => "#0000FF",
    "text_color3"      => "#00FF00",
    "text_color4"      => "#FFFF00",
    "text_color5"      => "#FF00FF",
    "text_color_speed" => 0,
    "position"        => "Center",
    "scroll_speed"    => 35,
    "show_gust"       => false,
    "message"         => "{temp}  {wind}",
    "loop_interval"   => 60,
    "border_enabled"       => false,
    "border_thickness"     => 3,
    "border_palette"       => "Christmas",
    "border_custom_colors" => "#FF0000,#FFFFFF,#00C83C",
    "border_stripe"        => 6,
    "border_chase"         => false,
    "chase_speed"          => 4,
);

// FPP's plugin settings format: key = "value" lines
function awLoad($file, $defaults) {
    $cfg = $defaults;
    if (file_exists($file))
        foreach (file($file, FILE_IGNORE_NEW_LINES) as $line)
            if (preg_match('/^\s*([^=\s#]+)\s*=\s*"?(.*?)"?\s*$/', $line, $m) && array_key_exists($m[1], $defaults))
                $cfg[$m[1]] = $m[2];
    foreach (array("show_gust", "border_enabled", "border_chase") as $k)
        $cfg[$k] = in_array($cfg[$k], array(true, 1, "1", "true", "on"), true);
    return $cfg;
}

function awSaveSetting($key, $value, $plugin, $file) {
    if (is_bool($value)) $value = $value ? "1" : "0";
    $value = str_replace('"', "'", (string)$value);
    if (function_exists('WriteSettingToFile')) {        // FPP's own helper
        WriteSettingToFile($key, $value, $plugin);
        return;
    }
    // same format, for running the page outside FPP
    $lines = file_exists($file) ? file($file, FILE_IGNORE_NEW_LINES) : array();
    $out = array(); $done = false;
    foreach ($lines as $l) {
        if (preg_match('/^\s*' . preg_quote($key, '/') . '\s*=/', $l)) { $out[] = "$key = \"$value\""; $done = true; }
        else $out[] = $l;
    }
    if (!$done) $out[] = "$key = \"$value\"";
    file_put_contents($file, implode("\n", $out) . "\n");
}

function awLoadCreds($file) {
    $c = file_exists($file) ? json_decode(file_get_contents($file), true) : null;
    return is_array($c) ? $c : array();
}

function awGetJson($url) {
    $ctx = stream_context_create(array("http" => array("timeout" => 3)));
    $raw = @file_get_contents($url, false, $ctx);
    return $raw === false ? null : json_decode($raw, true);
}

function h($s) { return htmlspecialchars((string)$s, ENT_QUOTES); }

$cfg    = awLoad($awConfigFile, $awDefaults);
$creds  = awLoadCreds($awCredFile);
$notice = "";
$output = "";

if ($_SERVER["REQUEST_METHOD"] === "POST" && isset($_POST["aw_action"])) {
    $action = $_POST["aw_action"];

    if ($action === "save" || $action === "save_show") {
        foreach (array("station_mac", "fpp_host",
                       "model_name", "font", "color", "position", "message",
                       "border_palette", "border_custom_colors",
                       "text_color_mode", "text_palette", "text_color2", "text_color3",
                       "text_color4", "text_color5") as $k) {
            if (isset($_POST[$k]))
                $cfg[$k] = trim($_POST[$k]);
        }
        foreach (array("font_size", "scroll_speed", "loop_interval",
                       "border_thickness", "border_stripe", "chase_speed",
                       "text_num_colors", "text_color_speed") as $k) {
            if (isset($_POST[$k]))
                $cfg[$k] = intval($_POST[$k]);
        }
        $cfg["show_gust"]      = isset($_POST["show_gust"]);
        $cfg["border_enabled"] = isset($_POST["border_enabled"]);
        $cfg["border_chase"]   = isset($_POST["border_chase"]);
        foreach ($awDefaults as $k => $v)
            if ($k !== "api_key" && $k !== "application_key")
                awSaveSetting($k, $cfg[$k], $awPlugin, $awConfigFile);

        // keys: only replaced when something new is typed in
        $ok = true;
        $newCreds = $creds;
        if (isset($_POST["api_key"]) && trim($_POST["api_key"]) !== "") $newCreds["APIKey"] = trim($_POST["api_key"]);
        if (isset($_POST["application_key"]) && trim($_POST["application_key"]) !== "") $newCreds["ApplicationKey"] = trim($_POST["application_key"]);
        if ($newCreds !== $creds) {
            @mkdir($awDataDir, 0775, true);
            $ok = @file_put_contents($awCredFile, json_encode($newCreds)) !== false;
            @chmod($awCredFile, 0600);
            $creds = $newCreds;
        }
        $notice = $ok ? array("text-success", "Settings saved.")
                      : array("text-danger", "Couldn't save the Ambient Weather keys.");
    }

    if ($action === "save_show") {
        $output = shell_exec("timeout 30 /usr/bin/python3 " . escapeshellarg($awScript) . " 2>&1");
    } elseif ($action === "off") {
        $output = shell_exec("timeout 30 /usr/bin/python3 " . escapeshellarg($awScript) . " --off 2>&1");
    }
}

// Lists for dropdowns (fall back to a text box if FPP doesn't answer)
$models = array();
$m = awGetJson("http://127.0.0.1/api/overlays/models");
if (is_array($m))
    foreach ($m as $model)
        if (isset($model["Name"])) $models[] = $model["Name"];

$fonts = array();
$f = awGetJson("http://127.0.0.1/api/overlays/fonts");
if (is_array($f)) {
    foreach ($f as $k => $v) {
        if (is_string($v))                      $fonts[] = $v;
        elseif (is_array($v) && isset($v["Name"])) $fonts[] = $v["Name"];
        elseif (is_string($k))                  $fonts[] = $k;
    }
    sort($fonts);
}

function awSelectOrText($name, $value, $options) {
    if (count($options) == 0) {
        printf("<input type='text' class='form-control' name='%s' value='%s'>", h($name), h($value));
        return;
    }
    if (!in_array($value, $options))
        array_unshift($options, $value);
    printf("<select class='form-select' name='%s'>", h($name));
    foreach ($options as $o)
        printf("<option value='%s'%s>%s</option>", h($o), $o == $value ? " selected" : "", h($o));
    echo "</select>";
}

$palettes = array("Christmas" => "Christmas (red, white, green)",
                  "Red & Green" => "Red & Green", "Candy Cane" => "Candy Cane (red & white)",
                  "Winter" => "Winter (blues & white)", "Gold & Silver" => "Gold & Silver",
                  "Rainbow" => "Rainbow", "Custom" => "Custom (colors below)");

$textModes = array(
    "Single"              => "One color",
    "Per Letter"          => "Each letter a different color",
    "Per Word"            => "Each word a different color",
    "Per Line"            => "Each line a different color",
    "Random Letter"       => "Random color per letter",
    "Random Word"         => "Random color per word",
    "Gradient Horizontal" => "Gradient, left to right",
    "Gradient Vertical"   => "Gradient, top to bottom",
    "Gradient Diagonal"   => "Gradient, corner to corner",
    "Sparkle"             => "Sparkle (scrolling text only)",
    "Chase"               => "Chase (scrolling text only)",
);
$textPalettes = array("Rainbow", "Christmas", "Winter", "Fire", "Ocean", "Forest",
                      "Patriotic", "Pastel", "Party", "Halloween", "Custom");

$positions = array(
    "Center" => "Center (no scrolling)",
    "R2L"    => "Scroll right to left",
    "L2R"    => "Scroll left to right",
    "B2T"    => "Scroll bottom to top",
    "T2B"    => "Scroll top to bottom",
);
?>

<div id="global" class="settings">
<fieldset>
<legend>Ambient Weather Display</legend>

<?php if ($notice) printf("<p class='%s'>%s</p>", $notice[0], h($notice[1])); ?>

<form method="post">
<div class="table-responsive">
<table class="table table-sm align-middle">
<tr><th colspan="2"><h3>Ambient Weather account</h3>
    <small>Create both keys at
    <a href="https://ambientweather.net/account" target="_blank">ambientweather.net/account</a> (API Keys).</small></th></tr>
<tr><td>API Key</td>
    <td><input type="password" class="form-control" name="api_key" value="" autocomplete="new-password"
         placeholder="<?= empty($creds["APIKey"]) ? "paste your API Key" : "saved - leave blank to keep it" ?>"></td></tr>
<tr><td>Application Key</td>
    <td><input type="password" class="form-control" name="application_key" value="" autocomplete="new-password"
         placeholder="<?= empty($creds["ApplicationKey"]) ? "paste your Application Key" : "saved - leave blank to keep it" ?>"></td></tr>
<tr><td>Station MAC (optional)</td>
    <td><input type="text" class="form-control" name="station_mac" value="<?= h($cfg["station_mac"]) ?>">
    <small>Blank = first station on your account</small></td></tr>

<tr><th colspan="2"><h3>Matrix display</h3></th></tr>
<tr><td>Overlay Model</td><td><?php awSelectOrText("model_name", $cfg["model_name"], $models); ?></td></tr>
<tr><td>Message</td>
    <td><input type="text" class="form-control" name="message" value="<?= h($cfg["message"]) ?>"><br>
    <small><code>{temp}</code> and <code>{wind}</code> are replaced with live readings,
    e.g. <code>The weather right now is: {temp}  {wind}</code></small></td></tr>
<tr><td>Show wind gust</td>
    <td><input type="checkbox" name="show_gust" <?= $cfg["show_gust"] ? "checked" : "" ?>>
    <small>"Wind 5 G12 mph"</small></td></tr>
<tr><td>Font</td><td><?php awSelectOrText("font", $cfg["font"], $fonts); ?></td></tr>
<tr><td>Font size</td>
    <td><input type="number" name="font_size" value="<?= h($cfg["font_size"]) ?>" min="6" max="64"></td></tr>
<tr><td>Text colors</td>
    <td><select name="text_color_mode" id="awMode" onchange="awColors()">
    <?php foreach ($textModes as $k => $label)
        printf("<option value='%s'%s>%s</option>", h($k), $cfg["text_color_mode"] == $k ? " selected" : "", h($label)); ?>
    </select></td></tr>
<tr class="awMulti"><td>Color palette</td>
    <td><select name="text_palette" id="awPalette" onchange="awColors()">
    <?php foreach ($textPalettes as $k)
        printf("<option value='%s'%s>%s</option>", h($k), $cfg["text_palette"] == $k ? " selected" : "", h($k == "Custom" ? "Custom (pick below)" : $k)); ?>
    </select></td></tr>
<tr id="awColorRow"><td>Color<span class="awCustom">s</span></td>
    <td><input type="color" name="color" value="<?= h($cfg["color"]) ?>">
    <span class="awCustom">
    <?php for ($c = 2; $c <= 5; $c++)
        printf("<input type='color' class='awExtra' name='text_color%d' value='%s'>", $c, h($cfg["text_color$c"])); ?>
    &nbsp;use the first
    <select name="text_num_colors" id="awNum" onchange="awColors()">
    <?php for ($c = 1; $c <= 5; $c++)
        printf("<option%s>%d</option>", intval($cfg["text_num_colors"]) == $c ? " selected" : "", $c); ?>
    </select> colors</span></td></tr>
<tr class="awMulti"><td>Color movement</td>
    <td><input type="range" name="text_color_speed" min="0" max="100" value="<?= h($cfg["text_color_speed"]) ?>"
         oninput="document.getElementById('awSpeedVal').textContent=this.value">
    <span id="awSpeedVal"><?= h($cfg["text_color_speed"]) ?></span>
    <small>0 = colors stay put; higher = colors flow through the letters (scrolling text only;
    needed for Sparkle and Chase)</small></td></tr>
<script>
function awColors() {
    var multi = document.getElementById("awMode").value != "Single";
    var custom = multi && document.getElementById("awPalette").value == "Custom";
    document.querySelectorAll(".awMulti").forEach(function (e) { e.style.display = multi ? "" : "none"; });
    document.querySelectorAll(".awCustom").forEach(function (e) { e.style.display = custom ? "" : "none"; });
    document.getElementById("awColorRow").style.display = (!multi || custom) ? "" : "none";
    var n = parseInt(document.getElementById("awNum").value);
    document.querySelectorAll(".awExtra").forEach(function (e, i) { e.style.display = (i + 2 <= n) ? "" : "none"; });
}
awColors();
</script>
<tr><td>Position</td>
    <td><select name="position">
    <?php foreach ($positions as $k => $label)
        printf("<option value='%s'%s>%s</option>", $k, $cfg["position"] == $k ? " selected" : "", $label); ?>
    </select></td></tr>
<tr><td>Scroll speed</td>
    <td><input type="number" name="scroll_speed" value="<?= h($cfg["scroll_speed"]) ?>" min="1" max="200">
    <small>pixels/second (scrolling only)</small></td></tr>
<tr><td>Default loop interval</td>
    <td><input type="number" name="loop_interval" value="<?= h($cfg["loop_interval"]) ?>" min="30" max="3600">
    <small>seconds, used by <code>--loop</code> with no number</small></td></tr>

<tr><th colspan="2"><h3>Christmas border</h3>
    <small>With the border on, the message is drawn in the matrix's pixel font and sized
    automatically to fit inside the border (Font, Font size, Position and Scroll speed
    above are not used). Put <code>|</code> in the message to start a new line, e.g.
    <code>The weather right now is:|{temp}  {wind}</code></small></th></tr>
<tr><td>Show border</td>
    <td><input type="checkbox" name="border_enabled" <?= $cfg["border_enabled"] ? "checked" : "" ?>></td></tr>
<tr><td>Border colors</td>
    <td><select name="border_palette">
    <?php foreach ($palettes as $k => $label)
        printf("<option value='%s'%s>%s</option>", h($k), $cfg["border_palette"] == $k ? " selected" : "", h($label)); ?>
    </select></td></tr>
<tr><td>Custom colors</td>
    <td><input type="text" class="form-control" name="border_custom_colors" value="<?= h($cfg["border_custom_colors"]) ?>">
    <small>comma-separated, used when Border colors is Custom</small></td></tr>
<tr><td>Border thickness</td>
    <td><input type="number" name="border_thickness" value="<?= h($cfg["border_thickness"]) ?>" min="1" max="8">
    <small>pixels</small></td></tr>
<tr><td>Stripe length</td>
    <td><input type="number" name="border_stripe" value="<?= h($cfg["border_stripe"]) ?>" min="1" max="32">
    <small>pixels per color</small></td></tr>
<tr><td>Chase</td>
    <td><input type="checkbox" name="border_chase" <?= $cfg["border_chase"] ? "checked" : "" ?>>
    <small>stripes move around the edge (only while running with <code>--loop</code>)</small></td></tr>
<tr><td>Chase speed</td>
    <td><input type="number" name="chase_speed" value="<?= h($cfg["chase_speed"]) ?>" min="1" max="10">
    <small>steps per second</small></td></tr>

<tr><th colspan="2"><h3>Advanced</h3></th></tr>
<tr><td>FPP address</td>
    <td><input type="text" class="form-control" name="fpp_host" value="<?= h($cfg["fpp_host"]) ?>">
    <small>Leave as http://127.0.0.1</small></td></tr>
</table>
</div>

<button type="submit" name="aw_action" value="save" class="btn btn-success">Save</button>
<button type="submit" name="aw_action" value="save_show" class="btn btn-primary">Save &amp; Show Now</button>
<button type="submit" name="aw_action" value="off" class="btn btn-outline-secondary">Turn Display Off</button>
</form>

<?php if ($output !== "" && $output !== null): ?>
<h3>Result</h3>
<pre class="bg-body-tertiary border rounded p-2 text-wrap"><?= h($output) ?></pre>
<?php endif; ?>

<h3>Using it in a playlist or the scheduler</h3>
<p>Add a <b>Run Script</b> command and choose <b>AmbientWeather.sh</b>. Optional arguments:</p>
<ul>
<li><i>(none)</i> &ndash; update the matrix once</li>
<li><code>--loop 60</code> &ndash; keep updating every 60 seconds</li>
<li><code>--off</code> &ndash; stop a running display, clear it and put the overlay model back</li>
<li><code>--text "The weather right now is:"</code> &ndash; use different wording for this entry only
    (with the border on, <code>|</code> starts a new line)</li>
</ul>
</fieldset>
</div>
