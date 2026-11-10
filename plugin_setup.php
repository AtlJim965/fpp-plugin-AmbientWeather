<?php
// fpp-plugin-AmbientWeather settings page
$awPlugin     = "fpp-plugin-AmbientWeather";
$awConfigFile = "/home/fpp/media/config/plugin." . $awPlugin . ".json";
$awScript     = "/home/fpp/media/plugins/" . $awPlugin . "/ambient_weather.py";

$awDefaults = array(
    "api_key"         => "",
    "application_key" => "",
    "station_mac"     => "",
    "fpp_host"        => "http://127.0.0.1",
    "model_name"      => "LED Panels",
    "font"            => "FreeSans",
    "font_size"       => 22,
    "color"           => "#FFFFFF",
    "position"        => "Center",
    "scroll_speed"    => 35,
    "show_gust"       => false,
    "message"         => "{temp}  {wind}",
    "loop_interval"   => 60,
);

function awLoad($file, $defaults) {
    $cfg = $defaults;
    if (file_exists($file)) {
        $saved = json_decode(file_get_contents($file), true);
        if (is_array($saved))
            $cfg = array_merge($cfg, $saved);
    }
    return $cfg;
}

function awGetJson($url) {
    $ctx = stream_context_create(array("http" => array("timeout" => 3)));
    $raw = @file_get_contents($url, false, $ctx);
    return $raw === false ? null : json_decode($raw, true);
}

function h($s) { return htmlspecialchars((string)$s, ENT_QUOTES); }

$cfg    = awLoad($awConfigFile, $awDefaults);
$notice = "";
$output = "";

if ($_SERVER["REQUEST_METHOD"] === "POST" && isset($_POST["aw_action"])) {
    $action = $_POST["aw_action"];

    if ($action === "save" || $action === "save_show") {
        foreach (array("api_key", "application_key", "station_mac", "fpp_host",
                       "model_name", "font", "color", "position", "message") as $k) {
            if (isset($_POST[$k]))
                $cfg[$k] = trim($_POST[$k]);
        }
        foreach (array("font_size", "scroll_speed", "loop_interval") as $k) {
            if (isset($_POST[$k]))
                $cfg[$k] = intval($_POST[$k]);
        }
        $cfg["show_gust"] = isset($_POST["show_gust"]);

        if (@file_put_contents($awConfigFile, json_encode($cfg, JSON_PRETTY_PRINT)) === false) {
            $notice = "<span style='color:red'>Could not write $awConfigFile</span>";
        } else {
            @chmod($awConfigFile, 0600);
            $notice = "<span style='color:green'>Settings saved.</span>";
        }
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
        printf("<input type='text' name='%s' value='%s' size='30'>", h($name), h($value));
        return;
    }
    if (!in_array($value, $options))
        array_unshift($options, $value);
    printf("<select name='%s'>", h($name));
    foreach ($options as $o)
        printf("<option value='%s'%s>%s</option>", h($o), $o == $value ? " selected" : "", h($o));
    echo "</select>";
}

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

<?php if ($notice) echo "<p>$notice</p>"; ?>

<form method="post">
<table class="table table-sm">
<tr><th colspan="2"><h3>Ambient Weather account</h3>
    <small>Create both keys at
    <a href="https://ambientweather.net/account" target="_blank">ambientweather.net/account</a> (API Keys).</small></th></tr>
<tr><td>API Key</td>
    <td><input type="password" name="api_key" value="<?= h($cfg["api_key"]) ?>" size="70" autocomplete="off"></td></tr>
<tr><td>Application Key</td>
    <td><input type="password" name="application_key" value="<?= h($cfg["application_key"]) ?>" size="70" autocomplete="off"></td></tr>
<tr><td>Station MAC (optional)</td>
    <td><input type="text" name="station_mac" value="<?= h($cfg["station_mac"]) ?>" size="20">
    <small>Blank = first station on your account</small></td></tr>

<tr><th colspan="2"><h3>Matrix display</h3></th></tr>
<tr><td>Overlay Model</td><td><?php awSelectOrText("model_name", $cfg["model_name"], $models); ?></td></tr>
<tr><td>Message</td>
    <td><input type="text" name="message" value="<?= h($cfg["message"]) ?>" size="60"><br>
    <small><code>{temp}</code> and <code>{wind}</code> are replaced with live readings,
    e.g. <code>The weather right now is: {temp}  {wind}</code></small></td></tr>
<tr><td>Show wind gust</td>
    <td><input type="checkbox" name="show_gust" <?= $cfg["show_gust"] ? "checked" : "" ?>>
    <small>"Wind 5 G12 mph"</small></td></tr>
<tr><td>Font</td><td><?php awSelectOrText("font", $cfg["font"], $fonts); ?></td></tr>
<tr><td>Font size</td>
    <td><input type="number" name="font_size" value="<?= h($cfg["font_size"]) ?>" min="6" max="64"></td></tr>
<tr><td>Color</td>
    <td><input type="color" name="color" value="<?= h($cfg["color"]) ?>"></td></tr>
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

<tr><th colspan="2"><h3>Advanced</h3></th></tr>
<tr><td>FPP address</td>
    <td><input type="text" name="fpp_host" value="<?= h($cfg["fpp_host"]) ?>" size="30">
    <small>Leave as http://127.0.0.1</small></td></tr>
</table>

<button type="submit" name="aw_action" value="save" class="buttons btn-success">Save</button>
<button type="submit" name="aw_action" value="save_show" class="buttons">Save &amp; Show Now</button>
<button type="submit" name="aw_action" value="off" class="buttons">Turn Display Off</button>
</form>

<?php if ($output !== "" && $output !== null): ?>
<h3>Result</h3>
<pre style="background:#222;color:#0f0;padding:8px;white-space:pre-wrap"><?= h($output) ?></pre>
<?php endif; ?>

<h3>Using it in a playlist or the scheduler</h3>
<p>Add a <b>Run Script</b> command and choose <b>AmbientWeather.sh</b>. Optional arguments:</p>
<ul>
<li><i>(none)</i> &ndash; update the matrix once</li>
<li><code>--loop 60</code> &ndash; keep updating every 60 seconds</li>
<li><code>--off</code> &ndash; clear the text and turn the overlay off</li>
<li><code>--text "The weather right now is:"</code> &ndash; use different wording for this entry only</li>
</ul>
</fieldset>
</div>
