<?php
$path = isset($_SERVER['REQUEST_URI']) ? ltrim($_SERVER['REQUEST_URI'], '/') : '';
$target = "https://digitalcorpora.s3.amazonaws.com/s3_browser.html#" . $path;
header("Location: $target", true, 302);
exit;
?>
