"use strict";

var g_header = null;
var g_data = [];

var g_data_offset = 0;

var g_played_pkg_count = 0;

var g_timer = null;

var g_playing = false;
var g_need_stop = false;
var g_skip = true;
var g_console_term = null;
var g_current_time;
var g_finish = false;

var g_record_tick = 50;


var speed_table = [
    {speed: 1, name: '正常速度'},
    {speed: 2, name: '快进 x2'},
    {speed: 4, name: '快进 x4'},
    {speed: 8, name: '快进 x8'},
    {speed: 16, name: '快进 x16'}
];
var speed_offset = 0;

$app.req_record_data = function (record_id, offset) {
    $tp.ajax_post_json('/audit/get-record-data', {id: record_id, offset: offset},
        function (ret) {
            if (ret.code === TPE_OK) {
                // console.log('data', ret.data);
                g_data = g_data.concat(ret.data.data_list);
                g_data_offset += ret.data.data_size;

                if (g_data.length < g_header.pkg_count) {
                    $app.req_record_data(record_id, g_data_offset);
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

$app.on_init = function (cb_stack) {
    var record_id = $app.options.record_id;

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

    $tp.ajax_post_json('/audit/get-record-header', {id: record_id},
        function (ret) {
            if (ret.code === TPE_OK) {
                g_header = ret.data;
                console.log('header', g_header);

                $('#recorder-info').html(tp_format_datetime(g_header.start) + ': ' + g_header.user_name + '@' + g_header.client_ip + ' 访问 ' + g_header.account + '@' + g_header.conn_ip + ':' + g_header.conn_port);

                $app.req_record_data(record_id, 0);

                g_current_time = 0;
                //setTimeout(init, 500);
                init_and_play();
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

        g_console_term.charMeasure.measure();
        $app.adjust_viewport();
    });

    $app.dom.btn_small_font.click(function () {
        if (_.isNull($app.dom.xterm_terminal))
            return;

        var _size = parseInt($app.dom.xterm_terminal.css('font-size'));
        if (_size <= 12)
            return;

        $app.dom.xterm_terminal.css('font-size', _size - 1);

        g_console_term.charMeasure.measure();
        $app.adjust_viewport();
    });

    $app.dom.btn_play.click(function () {
        if (g_playing)
            pause();
        else
            play();
    });

    $app.dom.btn_skip.click(function () {
        var obj = $('#btn-skip i');
        if (g_skip) {
            g_skip = false;
            obj.removeClass('fa-check-square-o').addClass('fa-square-o');
        } else {
            g_skip = true;
            obj.removeClass('fa-square-o').addClass('fa-check-square-o');
        }

        // console.log('skip:', g_skip);
    });

    $app.dom.btn_restart.click(function () {
        restart();
    });

    speed_offset = 0;
    $app.dom.btn_speed.text(speed_table[speed_offset].name);

    $app.dom.btn_speed.click(function () {
        var length = speed_table.length;
        speed_offset += 1;
        if (speed_offset === length) {
            speed_offset = 0;
        }
        $app.dom.btn_speed.text(speed_table[speed_offset].name);
    });

    $app.dom.progress.mousedown(function () {
        pause();
    });
    $app.dom.progress.mouseup(function () {
        g_current_time = parseInt(g_header.time_used * $app.dom.progress.val() / 100);
        setTimeout(function () {
            init_and_play();
        }, 100);
    });
    $app.dom.progress.mousemove(function () {
        g_current_time = parseInt(g_header.time_used * $app.dom.progress.val() / 100);
        $app.dom.time.text(parseInt((g_current_time) / 1000) + '/' + parseInt(g_header.time_used / 1000) + '秒');
    });

    $app.adjust_viewport = function () {
        if (!_.isNull($app.dom.xterm_viewport)) {
            $app.dom.xterm_viewport.width(parseInt(window.getComputedStyle($app.dom.xterm_rows[0]).width));
            $app.dom.xterm_viewport.height(parseInt(window.getComputedStyle($app.dom.xterm_rows[0]).height) - 1);
        }
    };

    function init_and_play() {
        if (_.isNull(g_console_term)) {
            g_console_term = new Terminal({
                cols: g_header.width,
                rows: g_header.height
            });

            g_console_term.on('refresh', function () {
                $app.adjust_viewport();
            });

            g_console_term.open(document.getElementById('xterm-box'), true);

            $app.dom.xterm_terminal = $('#xterm-box .terminal');
            $app.dom.xterm_rows = $('#xterm-box .terminal .xterm-rows');
            $app.dom.xterm_viewport = $('#xterm-box .terminal .xterm-viewport');
        } else {
            g_console_term.reset(g_header.width, g_header.height);
        }

        if(g_header.pkg_count === 0)
            return;

        $app.dom.progress.val(0);
        // $app.dom.status.text("正在播放");
        $app.dom.btn_play.children().removeClass().addClass('fa fa-pause').text(' 暂停');

        g_need_stop = false;
        g_playing = true;
        g_finish = false;
        g_played_pkg_count = 0;
        //setTimeout(do_play, g_record_tick);
        do_play();
    }

    function do_play() {
        if (g_need_stop) {
            g_playing = false;
            return;
        }

        if (g_data.length <= g_played_pkg_count) {
            $app.dom.status.text("正在缓存数据...");
            g_timer = setTimeout(do_play, g_record_tick);
            return;
        }

        $app.dom.status.text("正在播放");
        g_current_time += g_record_tick * speed_table[speed_offset].speed;

        var _record_tick = g_record_tick;

        for (var i = g_played_pkg_count; i < g_data.length; i++) {
            if (g_need_stop)
                break;

            var play_data = g_data[i];

            if (play_data.t < g_current_time) {
                if (play_data.a === 1) {
                    g_console_term.resize(play_data.w, play_data.h);
                } else if (play_data.a === 2) {
                    g_console_term.write(play_data.d);
                }
                else {
                    g_console_term.write(tp_base64_decode(play_data.d));
                }

                if ((g_played_pkg_count + 1) === g_header.pkg_count) {
                    $app.dom.progress.val(100);
                    $app.dom.status.text('播放完成');
                    $app.dom.time.text(parseInt(g_header.time_used / 1000) + '秒');
                    g_finish = true;
                    g_playing = false;
                    $app.dom.btn_play.children().removeClass().addClass('fa fa-play').text(' 播放');

                    return;
                } else {
                    g_played_pkg_count++;
                }

            } else {
                break;
            }
        }

        if (g_need_stop)
            return;

        if (g_skip) {
            if (play_data.t - g_current_time > 800) {
                g_current_time = play_data.t; // - g_record_tick * speed_table[speed_offset].speed;
                _record_tick = 800;
            }
        }

        // sync progress bar.
        var _progress = parseInt(g_current_time * 100 / g_header.time_used);
        $app.dom.progress.val(_progress);
        var temp = parseInt(g_current_time / 1000);
        $app.dom.time.text(temp + '/' + parseInt(g_header.time_used / 1000) + '秒');

        // if all packages played
        if (g_played_pkg_count >= g_header.pkg_count) {
            $app.dom.progress.val(100);
            $app.dom.status.text('播放完成');
            $app.dom.time.text(parseInt(g_header.time_used / 1000) + '秒');
            g_finish = true;
            g_playing = false;
            $app.dom.btn_play.children().removeClass().addClass('fa fa-play').text(' 播放');
        } else {
            if (!g_need_stop)
                g_timer = setTimeout(do_play, _record_tick);
        }
    }

    function play() {
        if (g_playing) {
            return;
        }

        if (g_finish) {
            restart();
            return;
        }

        $app.dom.btn_play.children().removeClass().addClass('fa fa-pause').text(' 暂停');

        g_need_stop = false;
        g_playing = true;
        g_timer = setTimeout(do_play, g_record_tick);
    }

    function pause() {
        if (!_.isNull(g_timer))
            clearTimeout(g_timer);
        $app.dom.btn_play.children().removeClass().addClass('fa fa-play').text(' 播放');
        g_need_stop = true;
        g_playing = false;
        $app.dom.status.text("已暂停");
    }

    function restart() {
        if (!_.isNull(g_timer))
            clearTimeout(g_timer);
        g_current_time = 0;
        init_and_play();
    }

    cb_stack.exec();
};
