/**
 * Created by mi on 2016/7/27.
 * Upgrade for new record-format by Apex on 2017-01-08
 */

var g_header = null;
var g_data = [];

var g_cur_play_file_id = 0;
var g_cur_play_file_offset = 0;
var g_last_time = 0;
var g_down_play_file_id = 0;

var g_total_time = 0;
var g_total_file_count = 0;
var g_process = 0;
var g_playing = false;
var g_need_stop = false;
var g_skip = true;
var g_timer = null;
var g_console_term = null;
var g_current_time;
var g_finish = false;
var g_req_count = 0;

var g_dom_time = null;
var g_dom_btn_play = null;
var g_dom_btn_speed = null;
var g_dom_btn_skip = null;
var g_dom_progress = null;
var g_dom_status = null;


var speed_table = [
    {speed: 1, name: '正常速度'},
    {speed: 2, name: '快进 x2'},
    {speed: 4, name: '快进 x4'},
    {speed: 8, name: '快进 x8'},
    {speed: 16, name: '快进 x16'}
];
var speed_offset = 0;

ywl.req_record_info = function (record_id, file_id, repeat) {
    ywl.ajax_post_json_time_out('/log/get-record-file-info', {id: record_id, file_id: file_id}, 30 * 1000,
        function (ret) {
            if (ret.code === TPE_OK) {
                g_data[file_id] = ret.data;

                if ((g_down_play_file_id + 1) <= g_total_file_count) {
                    if (repeat) {
                        ywl.req_record_info(record_id, g_down_play_file_id, true);
                        g_down_play_file_id++;
                    }
                }
            } else {
                console.log('req_record_info error ', ret.code);
            }
        },
        function () {
            console.log('req_record_info error');
        }
    );
};

ywl.on_init = function (cb_stack, cb_args) {
    var record_id = ywl.page_options.record_id;
    var record_tick = 16;
    var internal_tick = 0;

    g_dom_time = $('#play-time');
    g_dom_btn_play = $('#btn-play');
    g_dom_btn_speed = $('#btn-speed');
    g_dom_btn_skip = $('#btn-skip');
    g_dom_progress = $('#progress');
    g_dom_status = $('#play-status');

    Terminal.cursorBlink = false;

    ywl.ajax_post_json('/log/get-record-header', {id: record_id},
        function (ret) {
            if (ret.code === TPE_OK) {
                g_header = ret.data.header;
                g_total_file_count = g_header.file_count;
                g_total_time = g_header.time_used;

                $('#recorder-info').html(g_header.account + ' 于 ' + format_datetime(g_header.start) + ' 访问 ' + g_header.user_name + '@' + g_header.ip + ':' + g_header.port);

                // 请求第一个录像数据块
                g_down_play_file_id = 0;
                ywl.req_record_info(record_id, g_down_play_file_id, true);

                setTimeout(init, 1000);
            } else {
                ywl.notify_error('请求录像数据失败');
                console.log('load init info error ', ret.code);
            }
        },
        function () {
            ywl.notify_error('网络通讯失败');
        }
    );

    g_dom_btn_play.click(function () {
        if (g_playing)
            pause();
        else
            play();
    });

    g_dom_btn_skip.click(function () {
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

    $('#btn-restart').click(function () {
        replay();
    });

    speed_offset = 0;
    g_dom_btn_speed.text(speed_table[speed_offset].name);

    g_dom_btn_speed.click(function () {
        var length = speed_table.length;
        speed_offset += 1;
        if (speed_offset === length) {
            speed_offset = 0;
        }
        g_dom_btn_speed.text(speed_table[speed_offset].name);
        g_current_time = g_last_time;
    });

//    g_dom_progress.change(function () {
//        var process = g_dom_progress.val();
//        console.log('change.' + process);
//        //var beginTime = parseInt(g_total_time * process / 100);
//        speed_offset = 0;
//        g_dom_btn_speed.text(speed_table[speed_offset].name);
//    });

    function init() {
        g_last_time = 0;

        if (!_.isNull(g_console_term)) {
            g_console_term.destroy();
        }
        g_console_term = new Terminal({
            cols: g_header.width,
            rows: g_header.height,
            useStyle: true
        });
        g_console_term.open();
        $('.terminal').detach().appendTo('#terminal');
        var width = $('[class="terminal"]').width();
        g_dom_progress.width(width).val(g_process);

        g_dom_status.text("正在播放");
        g_dom_btn_play.children().removeClass().addClass('fa fa-pause').text(' 暂停');

        g_need_stop = false;
        g_playing = true;
        g_finish = false;
        g_current_time = 0;
        g_cur_play_file_id = 0;
        g_cur_play_file_offset = 0;
        g_timer = setInterval(done, record_tick);
    }

    function done() {
        if (g_need_stop) {
            g_playing = false;
            return;
        }

        if (_.isUndefined(g_data[g_cur_play_file_id])) {
            g_req_count++;
            if (g_req_count > 2000) {
                g_req_count = 0;
                g_dom_status.text("正在缓存数据[" + g_cur_play_file_id + ":" + g_total_file_count + "]");
                ywl.req_record_info(record_id, g_down_play_file_id, false);
            }

            return;
        }

        if ((g_cur_play_file_id + 1) > g_total_file_count) {
            console.log('g_cur_play_file_id error');
            return;
        }

        if ((g_cur_play_file_offset + 1) > g_data[g_cur_play_file_id].length) {
            console.log('g_cur_play_file_offset error');
            return;
        }
        g_dom_status.text("正在播放");
        g_current_time += record_tick * speed_table[speed_offset].speed;
        internal_tick += record_tick;
        var play_data = g_data[g_cur_play_file_id][g_cur_play_file_offset];

        //播放
        if (play_data.a === 1 || play_data.t < g_current_time) {
            var rec_length = g_data[g_cur_play_file_id].length;
            g_last_time = play_data.t;
            internal_tick = 0;

            if (play_data.a === 1)
                g_console_term.resize(play_data.w, play_data.h);
            else if (play_data.a === 2)
                g_console_term.write(play_data.d);
            else
                g_console_term.write(base64_decode(play_data.d));

            if ((g_cur_play_file_offset + 1) === rec_length) {
                if ((g_cur_play_file_id + 1) === g_total_file_count) {
                    g_dom_progress.val(100);
                    g_dom_status.text('播放完成');
                    g_dom_time.text(parseInt(g_total_time / 1000) + '秒');
                    g_finish = true;
                    g_playing = false;
                    g_dom_btn_play.children().removeClass().addClass('fa fa-play').text(' 播放');

                    clearInterval(g_timer);
                    return;
                } else {
                    g_cur_play_file_offset = 0;
                    g_cur_play_file_id++;
                }
            } else {
                g_cur_play_file_offset++;
            }
        } else {
            if (g_skip) {
                if (play_data.t - g_current_time > 1000) {
                    g_current_time = play_data.t - 999;
                }
            }
        }


        g_process = parseInt((g_last_time + internal_tick) * 100 / g_total_time);
        g_dom_progress.val(g_process);
        var temp = parseInt((g_last_time + internal_tick) / 1000);
        g_dom_time.text(temp + '/' + parseInt(g_total_time / 1000) + '秒');
    }

    function play() {
        if (g_playing) {
            return;
        }

        if (g_finish) {
            replay();
            return;
        }

        g_dom_btn_play.children().removeClass().addClass('fa fa-pause').text(' 暂停');

        g_need_stop = false;
        g_playing = true;
        g_timer = setInterval(done, record_tick);
    }

    function pause() {
        g_dom_btn_play.children().removeClass().addClass('fa fa-play').text(' 播放');
        clearInterval(g_timer);
        g_need_stop = true;
        g_playing = false;
        g_dom_status.text("已暂停");
    }

    function replay() {
        clearInterval(g_timer);
        init();
    }
};
