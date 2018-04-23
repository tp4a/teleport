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

    $app.canvas = null;

    $app.last_cursor_t = 0;
    $app.last_cursor_x = 0;
    $app.last_cursor_y = 0;
    $app.last_cursor_covered_image = null;

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
        screen: $('#screen')
    };

    $app.dom.progress.width($('#toolbar').width()).val(0);

    $tp.ajax_post_json('/audit/get-record-header', {protocol: TP_PROTOCOL_TYPE_RDP, id: record_id},
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
    $tp.ajax_post_json('/audit/get-record-data', {protocol: TP_PROTOCOL_TYPE_RDP, id: record_id, offset: offset},
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

$app._draw_cursor = function (x, y) {

    if (!_.isNull($app.last_cursor_covered_image)) {
        $app.canvas.putImageData($app.last_cursor_covered_image, $app.last_cursor_x - 8, $app.last_cursor_y - 8);
    }

    $app.last_cursor_covered_image = $app.canvas.getImageData(x - 8, y - 8, 16, 16);
    $app.last_cursor_x = x;
    $app.last_cursor_y = y;

    $app.canvas.drawImage($app.cursor_img, x - 8, y - 8);
};

$app.init_and_play = function () {
    $app.dom.screen.css({width: $app.record_hdr.width + 2, height: $app.record_hdr.height + 2});
    // $app.dom.canvas.css({width: $app.record_hdr.width, height: $app.record_hdr.height});

    if (_.isNull($app.canvas)) {
        // $app.canvas = $app.dom.canvas[0].getContext('2d');
        var h = '<canvas id="canvas" width="' + $app.record_hdr.width + '" height="' + $app.record_hdr.height + '"></canvas>';
        $app.dom.screen.append($(h));
        $app.canvas = document.getElementById('canvas').getContext('2d');
    } else {
        $app.canvas.clearRect(0, 0, $app.record_hdr.width, $app.record_hdr.height);
    }

    // $app._draw_cursor(100, 100);
    var x = ($app.record_hdr.width - 500) / 2;
    var y = ($app.record_hdr.height - 360) / 2;
    $app.canvas.drawImage($app.player_bg_img, x, y);


    // $app.canvas.strokeStyle="red";
    // $app.canvas.strokeRect(10,90,50,50);

    if ($app.record_hdr.pkg_count === 0)
        return;

    $app.dom.progress.val(0);
    $app.dom.btn_play.children().removeClass().addClass('fa fa-pause').text(' 暂停');

    $app.is_need_stop = false;
    $app.is_playing = true;
    $app.is_finished = false;
    $app.played_pkg_count = 0;
    $app.do_play();
};

$app.decompress = function (bitmap) {
    var fName = null;
    switch (bitmap.bit_per_pixel) {
        case 15:
            fName = 'bitmap_decompress_15';
            break;
        case 16:
            fName = 'bitmap_decompress_16';
            break;
        case 24:
            fName = 'bitmap_decompress_24';
            break;
        case 32:
            fName = 'bitmap_decompress_32';
            break;
        default:
            throw 'invalid bitmap data format';
    }

    var input = new Uint8Array(bitmap.img_data);
    var inputPtr = Module._malloc(input.length);
    var inputHeap = new Uint8Array(Module.HEAPU8.buffer, inputPtr, input.length);
    inputHeap.set(input);

    var output_width = bitmap.right - bitmap.left + 1;
    var output_height = bitmap.bottom - bitmap.top + 1;
    var ouputSize = output_width * output_height * 4;
    var outputPtr = Module._malloc(ouputSize);

    var outputHeap = new Uint8Array(Module.HEAPU8.buffer, outputPtr, ouputSize);

    var res = Module.ccall(fName,
        'number',
        ['number', 'number', 'number', 'number', 'number', 'number', 'number', 'number'],
        [outputHeap.byteOffset, output_width, output_height, bitmap.width, bitmap.height, inputHeap.byteOffset, input.length]
    );

    var output = new Uint8ClampedArray(outputHeap.buffer, outputHeap.byteOffset, ouputSize);

    Module._free(inputPtr);
    Module._free(outputPtr);

    return {width: output_width, height: output_height, data: output};
};

$app.do_play = function () {
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
            if (play_data.a === 0x10) {
                //$app.player_console_term.resize(play_data.w, play_data.h);
                // console.log('mouse pos:', play_data, play_data.x, play_data.y);
                $app._draw_cursor(play_data.x, play_data.y);

                console.log('cursor-t-delta:', play_data.t - $app.last_cursor_t);

                $app.last_cursor_t = play_data.t;
            }
            else if(play_data.a === 0x12) {
                //$app.player_console_term.write(tp_base64_decode(play_data.d));
                var _data = tp_base64_to_binarray(play_data.d);
                console.log('pkg size:', _data.length);

                var s = Uint8Array.from(_data);
                // console.log(s);
                var offset = 0;
                var update_type = s[offset + 1] * 256 + s[offset];
                offset += 2;
                var update_count = s[offset + 1] * 256 + s[offset];
                offset += 2;
                console.log('type:', update_type, 'count:', update_count)

                var bc;
                for (bc = 0; bc < update_count; ++bc) {
                    var bitmap = {};

                    bitmap.left = s[offset + 1] * 256 + s[offset];
                    offset += 2;
                    bitmap.top = s[offset + 1] * 256 + s[offset];
                    offset += 2;
                    bitmap.right = s[offset + 1] * 256 + s[offset];
                    offset += 2;
                    bitmap.bottom = s[offset + 1] * 256 + s[offset];
                    offset += 2;
                    bitmap.width = s[offset + 1] * 256 + s[offset];
                    offset += 2;
                    bitmap.height = s[offset + 1] * 256 + s[offset];
                    offset += 2;
                    bitmap.bit_per_pixel = s[offset + 1] * 256 + s[offset];
                    offset += 2;

                    var _flag = s[offset + 1] * 256 + s[offset];
                    offset += 2;

                    bitmap.isCompress = (_flag & 0x0001) === 0x0001;

                    var _length = s[offset + 1] * 256 + s[offset];
                    offset += 2;

                    bitmap.img_data = s.subarray(offset, offset + _length);
                    offset += _length;

                    //console.log(dest_left, dest_top, dest_right, dest_bottom, dest_width, dest_height, dest_bit_per_pixel, dest_flag, dest_length);
                    // console.log(bitmap);
                    var output = null;
                    if(bitmap.isCompress)
                        output = $app.decompress(bitmap);
                    else
                        output = {width : bitmap.width, height : bitmap.height, data : new Uint8ClampedArray(bitmap.data)};
                    // console.log(output);

                    var img = $app.canvas.createImageData(output.width, output.height);
                    img.data.set(output.data);
                    $app.canvas.putImageData(img, bitmap.left, bitmap.top);

                    //offset += dest_length;
                }
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

$app.play = function () {
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

$app.pause = function () {
    if (!_.isNull($app.player_timer))
        clearTimeout($app.player_timer);
    $app.dom.btn_play.children().removeClass().addClass('fa fa-play').text(' 播放');
    $app.is_need_stop = true;
    $app.is_playing = false;
    $app.dom.status.text("已暂停");
};

$app.restart = function () {
    if (!_.isNull($app.player_timer))
        clearTimeout($app.player_timer);
    $app.player_current_time = 0;
    $app.init_and_play();
};

