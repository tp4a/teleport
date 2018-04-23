"use strict";

$app.on_init = function (cb_stack) {
    var record_id = $app.options.record_id;

    $app.record_hdr = null;
    $app.record_data = [];
    $app.record_data_offset = 0;
    $app.played_pkg_count = 0;
    $app.player_timer = null;
    $app.is_playing = false;
    $app.is_need_stop = false;
    $app.need_skip = true;
    $app.player_console_term = null;
    $app.player_current_time = null;
    $app.is_finished = false;
    $app.record_tick = 50;


    $app.speed_table = [
        {speed: 1, name: '正常速度'},
        {speed: 2, name: '快进 x2'},
        {speed: 4, name: '快进 x4'},
        {speed: 8, name: '快进 x8'},
        {speed: 16, name: '快进 x16'}
    ];
    $app.speed_offset = 0;


    $app.dom = {
        time: $('#play-time'),
        btn_play: $('#btn-play'),
        btn_speed: $('#btn-speed'),
        btn_skip: $('#btn-skip'),
        btn_restart: $('#btn-restart'),
        btn_big_font: $('#btn-big-font'),
        btn_small_font: $('#btn-small-font'),
        progress: $('#progress'),
        status: $('#play-status'),
        xterm_box: $('#xterm-box'),
        xterm_terminal: null,
        xterm_viewport: null
    };

    $app.dom.progress.width($('#toolbar').width()).val(0);

    Terminal.cursorBlink = false;

    $tp.ajax_post_json('/audit/get-record-header', {protocol: TP_PROTOCOL_TYPE_SSH, id: record_id},
        function (ret) {
            if (ret.code === TPE_OK) {
                $app.record_hdr = ret.data;
                if ($app.record_hdr.width === 0)
                    $app.record_hdr.width = 80;
                if ($app.record_hdr.height === 0)
                    $app.record_hdr.height = 24;
                console.log('header', $app.record_hdr);

                $('#recorder-info').html(tp_format_datetime($app.record_hdr.start) + ': ' + $app.record_hdr.user_name + '@' + $app.record_hdr.client_ip + ' 访问 ' + $app.record_hdr.account + '@' + $app.record_hdr.conn_ip + ':' + $app.record_hdr.conn_port);

                $app.req_record_data(record_id, 0);

                $app.player_current_time = 0;
                //setTimeout(init, 500);
                $app.init_and_play();
            } else {
                $tp.notify_error('读取录像信息失败：' + tp_error_msg(ret.code, ret.message));
                console.error('load init info error ', ret.code);
            }
        },
        function () {
            $tp.notify_error('网络通讯失败');
        }
    );

    $app.dom.btn_big_font.click(function () {
        if (_.isNull($app.dom.xterm_terminal))
            return;
        var _size = parseInt($app.dom.xterm_terminal.css('font-size'));
        if (_size >= 24)
            return;

        $app.dom.xterm_terminal.css('font-size', _size + 1);

        $app.player_console_term.charMeasure.measure();
        $app.adjust_viewport();
    });

    $app.dom.btn_small_font.click(function () {
        if (_.isNull($app.dom.xterm_terminal))
            return;

        var _size = parseInt($app.dom.xterm_terminal.css('font-size'));
        if (_size <= 12)
            return;

        $app.dom.xterm_terminal.css('font-size', _size - 1);

        $app.player_console_term.charMeasure.measure();
        $app.adjust_viewport();
    });

    $app.dom.btn_play.click(function () {
        if ($app.is_playing)
            $app.pause();
        else
            $app.play();
    });

    $app.dom.btn_skip.click(function () {
        var obj = $('#btn-skip i');
        if ($app.need_skip) {
            $app.need_skip = false;
            obj.removeClass('fa-check-square').addClass('fa-square');
        } else {
            $app.need_skip = true;
            obj.removeClass('fa-square').addClass('fa-check-square');
        }

        // console.log('skip:', $app.need_skip);
    });

    $app.dom.btn_restart.click(function () {
        $app.restart();
    });

    $app.speed_offset = 0;
    $app.dom.btn_speed.text($app.speed_table[$app.speed_offset].name);

    $app.dom.btn_speed.click(function () {
        var length = $app.speed_table.length;
        $app.speed_offset += 1;
        if ($app.speed_offset === length) {
            $app.speed_offset = 0;
        }
        $app.dom.btn_speed.text($app.speed_table[$app.speed_offset].name);
    });

    $app.dom.progress.mousedown(function () {
        $app.pause();
    });
    $app.dom.progress.mouseup(function () {
        $app.player_current_time = parseInt($app.record_hdr.time_used * $app.dom.progress.val() / 100);
        setTimeout(function () {
            $app.init_and_play();
        }, 100);
    });
    $app.dom.progress.mousemove(function () {
        $app.player_current_time = parseInt($app.record_hdr.time_used * $app.dom.progress.val() / 100);
        $app.dom.time.text(parseInt(($app.player_current_time) / 1000) + '/' + parseInt($app.record_hdr.time_used / 1000) + '秒');
    });

    $app.adjust_viewport = function () {
        if (!_.isNull($app.dom.xterm_viewport)) {
            $app.dom.xterm_viewport.width(parseInt(window.getComputedStyle($app.dom.xterm_rows[0]).width));
            $app.dom.xterm_viewport.height(parseInt(window.getComputedStyle($app.dom.xterm_rows[0]).height) - 1);
        }
    };

    cb_stack.exec();
};

$app.req_record_data = function (record_id, offset) {
    $tp.ajax_post_json('/audit/get-record-data', {protocol: TP_PROTOCOL_TYPE_SSH, id: record_id, offset: offset},
        function (ret) {
            if (ret.code === TPE_OK) {
                // console.log('data', ret.data);
                $app.record_data = $app.record_data.concat(ret.data.data_list);
                $app.record_data_offset += ret.data.data_size;

                if ($app.record_data.length < $app.record_hdr.pkg_count) {
                    $app.req_record_data(record_id, $app.record_data_offset);
                }
            } else {
                $app.dom.status.text("读取录像数据失败：" + tp_error_msg(ret.code));
                $tp.notify_error('读取录像数据失败：' + tp_error_msg(ret.code, ret.message));
                console.log('req_record_info error ', ret.code);
            }
        },
        function () {
            console.log('req_record_info error');
        },
        30 * 1000
    );
};

$app.init_and_play = function() {
    if (_.isNull($app.player_console_term)) {
        $app.player_console_term = new Terminal({
            cols: $app.record_hdr.width,
            rows: $app.record_hdr.height
        });

        $app.player_console_term.on('refresh', function () {
            $app.adjust_viewport();
        });

        $app.player_console_term.open(document.getElementById('xterm-box'), true);

        $app.dom.xterm_terminal = $('#xterm-box .terminal');
        $app.dom.xterm_rows = $('#xterm-box .terminal .xterm-rows');
        $app.dom.xterm_viewport = $('#xterm-box .terminal .xterm-viewport');
    } else {
        $app.player_console_term.reset($app.record_hdr.width, $app.record_hdr.height);
    }

    if ($app.record_hdr.pkg_count === 0)
        return;

    $app.dom.progress.val(0);
    // $app.dom.status.text("正在播放");
    $app.dom.btn_play.children().removeClass().addClass('fa fa-pause').text(' 暂停');

    $app.is_need_stop = false;
    $app.is_playing = true;
    $app.is_finished = false;
    $app.played_pkg_count = 0;
    //setTimeout(do_play, $app.record_tick);
    $app.do_play();
};

$app.do_play = function() {
    if ($app.is_need_stop) {
        $app.is_playing = false;
        return;
    }

    if ($app.record_data.length <= $app.played_pkg_count) {
        $app.dom.status.text("正在缓存数据...");
        $app.player_timer = setTimeout($app.do_play, $app.record_tick);
        return;
    }

    $app.dom.status.text("正在播放");
    $app.player_current_time += $app.record_tick * $app.speed_table[$app.speed_offset].speed;

    var _record_tick = $app.record_tick;

    for (var i = $app.played_pkg_count; i < $app.record_data.length; i++) {
        if ($app.is_need_stop)
            break;

        var play_data = $app.record_data[i];

        if (play_data.t < $app.player_current_time) {
            if (play_data.a === 1) {
                $app.player_console_term.resize(play_data.w, play_data.h);
            } else if (play_data.a === 2) {
                $app.player_console_term.write(play_data.d);
            }
            else {
                $app.player_console_term.write(tp_base64_decode(play_data.d));
            }

            if (($app.played_pkg_count + 1) === $app.record_hdr.pkg_count) {
                $app.dom.progress.val(100);
                $app.dom.status.text('播放完成');
                $app.dom.time.text(parseInt($app.record_hdr.time_used / 1000) + '秒');
                $app.is_finished = true;
                $app.is_playing = false;
                $app.dom.btn_play.children().removeClass().addClass('fa fa-play').text(' 播放');

                return;
            } else {
                $app.played_pkg_count++;
            }

        } else {
            break;
        }
    }

    if ($app.is_need_stop)
        return;

    if ($app.need_skip) {
        if (play_data.t - $app.player_current_time > 800) {
            $app.player_current_time = play_data.t; // - $app.record_tick * $app.speed_table[$app.speed_offset].speed;
            _record_tick = 800;
        }
    }

    // sync progress bar.
    var _progress = parseInt($app.player_current_time * 100 / $app.record_hdr.time_used);
    $app.dom.progress.val(_progress);
    var temp = parseInt($app.player_current_time / 1000);
    $app.dom.time.text(temp + '/' + parseInt($app.record_hdr.time_used / 1000) + '秒');

    // if all packages played
    if ($app.played_pkg_count >= $app.record_hdr.pkg_count) {
        $app.dom.progress.val(100);
        $app.dom.status.text('播放完成');
        $app.dom.time.text(parseInt($app.record_hdr.time_used / 1000) + '秒');
        $app.is_finished = true;
        $app.is_playing = false;
        $app.dom.btn_play.children().removeClass().addClass('fa fa-play').text(' 播放');
    } else {
        if (!$app.is_need_stop)
            $app.player_timer = setTimeout($app.do_play, _record_tick);
    }
};

$app.play = function() {
    if ($app.is_playing) {
        return;
    }

    if ($app.is_finished) {
        $app.restart();
        return;
    }

    $app.dom.btn_play.children().removeClass().addClass('fa fa-pause').text(' 暂停');

    $app.is_need_stop = false;
    $app.is_playing = true;
    $app.player_timer = setTimeout($app.do_play, $app.record_tick);
};

$app.pause = function() {
    if (!_.isNull($app.player_timer))
        clearTimeout($app.player_timer);
    $app.dom.btn_play.children().removeClass().addClass('fa fa-play').text(' 播放');
    $app.is_need_stop = true;
    $app.is_playing = false;
    $app.dom.status.text("已暂停");
};

$app.restart = function() {
    if (!_.isNull($app.player_timer))
        clearTimeout($app.player_timer);
    $app.player_current_time = 0;
    $app.init_and_play();
};

