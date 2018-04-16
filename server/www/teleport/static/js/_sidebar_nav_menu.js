"use strict";

$tp.assist_checked = function () {
    if ($tp.assist.running) {
        $('#sidebar-tp-assist-ver').html('v'+$tp.assist.version);
    } else {
        $('#sidebar-tp-assist-ver').html('未能检测到');
    }
};
