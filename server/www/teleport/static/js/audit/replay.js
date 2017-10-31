/**
 * Created by mi on 2016/7/27.
 * Upgrade for new record-format by Apex on 2017-01-08
 */

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
                console.log('data', ret.data);
                g_data = g_data.concat(ret.data.data_list);
                g_data_offset += ret.data.data_size;

                if (g_data.length < g_header.pkg_count) {
                    $app.req_record_data(record_id, g_data_offset);
                }
                // else if(g_header.pkg_count < g_data.length) {
                //     g_header.pkg_count = g_data.length;
                // }
            } else {
                console.log('req_record_info error ', ret.code);
            }
        },
        function () {
            console.log('req_record_info error');
        },
        30 * 1000
    );
};

$app.on_init = function (cb_stack, cb_args) {
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
        xterm_box: $('#xterm-box')
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

                setTimeout(init, 1000);
            } else {
                $tp.notify_error('请求录像数据失败');
                console.log('load init info error ', ret.code);
            }
        },
        function () {
            $tp.notify_error('网络通讯失败');
        }
    );

    $app.dom.btn_big_font.click(function () {
        var obj = $('.terminal');
        obj.css('font-size', parseInt(obj.css('font-size')) + 2);
    });
    $app.dom.btn_small_font.click(function () {
        var obj = $('.terminal');
        obj.css('font-size', parseInt(obj.css('font-size')) - 2);
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

        console.log('skip:', g_skip);
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

//    $app.dom.progress.change(function () {
//        var process = g_dom_progress.val();
//        console.log('change.' + process);
//        //var beginTime = parseInt(g_header.time_used * process / 100);
//        speed_offset = 0;
//        g_dom_btn_speed.text(speed_table[speed_offset].name);
//    });

    function init() {
        if (_.isNull(g_console_term)) {
            g_console_term = new Terminal({
                cols: g_header.width,
                rows: g_header.height
            });
            g_console_term.open(document.getElementById('xterm-box'), false);

            // g_console_term.on('resize', function (obj, x, y) {
            //     var y = window.getComputedStyle($('#xterm-box .terminal .xterm-rows')[0]);
            //     var w = parseInt(y.width);
            //
            //     // $('#xterm-box .terminal .xterm-viewport').width(w+17);
            //
            //     $app.dom.xterm_box.width(w + 17);
            //     // $app.dom.progress.width(w).val(g_process);
            // });

        } else {
            g_console_term.reset(g_header.width, g_header.height);
            // g_console_term.setOption('scrollback', g_header.height);
        }

        $app.dom.progress.val(0);
        $app.dom.status.text("正在播放");
        $app.dom.btn_play.children().removeClass().addClass('fa fa-pause').text(' 暂停');

        g_need_stop = false;
        g_playing = true;
        g_finish = false;
        g_current_time = 0;
        g_played_pkg_count = 0;
        setTimeout(done, g_record_tick);
    }

    function done() {
        if (g_need_stop) {
            g_playing = false;
            return;
        }

        if (g_data.length <= g_played_pkg_count) {
            $app.dom.status.text("正在缓存数据...");
            g_timer = setTimeout(done, g_record_tick);
            return;
        }

        $app.dom.status.text("正在播放");
        g_current_time += g_record_tick * speed_table[speed_offset].speed;
        for (var i = g_played_pkg_count; i < g_data.length; i++) {
            var play_data = g_data[i];

            if (g_skip && play_data.a === 1) {
                g_console_term.resize(play_data.w, play_data.h);
                // g_console_term.setOption('scrollback', play_data.h);

                g_played_pkg_count++;
                continue;
            }

            console.log(play_data.t, g_current_time);
            if (play_data.t < g_current_time) {
                if(play_data.a === 1) {
                    g_console_term.resize(play_data.w, play_data.h);
                    // g_console_term.setOption('scrollback', play_data.h);
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
        if (g_skip) {
            if (play_data.t - g_current_time > 500) {
                g_current_time = play_data.t; // - g_record_tick * speed_table[speed_offset].speed;
            }
        }

        // sync progress bar.
        var _progress = parseInt((g_current_time) * 100 / g_header.time_used);
        $app.dom.progress.val(_progress);
        var temp = parseInt((g_current_time) / 1000);
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
            g_timer = setTimeout(done, g_record_tick);
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
        g_timer = setTimeout(done, g_record_tick);
    }

    function pause() {
        $app.dom.btn_play.children().removeClass().addClass('fa fa-play').text(' 播放');
        g_need_stop = true;
        g_playing = false;
        $app.dom.status.text("已暂停");
    }

    function restart() {
        if(!_.isNull(g_timer))
            clearTimeout(g_timer);
        init();
    }

    cb_stack.exec();
};
