/**
 * Created by mi on 2016/7/27.
 */
var g_term_list = null;
var g_header = null;
var g_data = [];

var g_cur_play_file_id = 0;
var g_cur_play_file_offset = 0;
var g_last_time = 0;
var g_down_play_file_id = 0;

var g_total_time = 0;
var g_total_file_count = 0;
var g_process = 0;
var g_bPlay = false;
var g_bNeedStop = false;
var g_time_id = null;
var g_console_term = null;
var g_current_time;
var g_finish = false;
var g_req_count = 0;

var g_win_size_next_idx = 0;	// 下一个改变尺寸的命令索引
var g_win_size_total_cnt = 0;

var speed_table = [
	{speed: 1, name: '正常速度'},
	{speed: 4, name: '快进X2'},
	{speed: 8, name: '快进X4'},
	{speed: 16, name: '快进X8'},
	{speed: 32, name: '快进X16'}
];
var speed_offset = 0;

ywl.req_record_info = function (record_id, file_id, repeat) {
	ywl.ajax_post_json_time_out('/log/get-record-file-info', {id: record_id, file_id: file_id}, 30 * 1000,
		function (ret) {
			if (ret.code == 0) {
				g_data[file_id] = ret.data;

				if ((g_down_play_file_id + 1) <= g_total_file_count) {
					if (repeat) {
						ywl.req_record_info(record_id, g_down_play_file_id, true);
						g_down_play_file_id++;
					}

				}
				//console.log('req_record_info successful');
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
	var interal_tick = 0;
	Terminal.cursorBlink = false;

	ywl.ajax_post_json('/log/get-record-header', {id: record_id},
		function (ret) {
			if (ret.code == 0) {
				g_header = ret.data.header;
				g_total_file_count = g_header.t_count;
				g_total_time = g_header.t_time + 1000;

				$("#play-time").text('0/' + parseInt(g_total_time / 1000) + '秒');
				g_term_list = ret.data.term;
				//console.log('term-list', g_term_list);
				g_win_size_total_cnt = g_term_list.term_list.length;

				// 请求第一个录像数据块
				g_down_play_file_id = 0;
				ywl.req_record_info(record_id, g_down_play_file_id, true);

				setTimeout(init, 1000);

				//console.log('load init info successful');
			} else {
				ywl.notify_error('请求录像数据失败');
				console.log('load init info error ', ret.code);
			}
		},
		function () {
			ywl.notify_error('网络通讯失败');
			//console.log('load init info error');

		}
	);
	$('#btn-stop').click(function () {
		pasue();
	});
	$('#btn-conitune').click(function () {
		play();
	});
	$('#btn-restart').click(function () {
		replay();
	});

	speed_offset = 0;
	$('#btn-speed').text(speed_table[speed_offset].name);

	$('#btn-speed').click(function () {
		var length = speed_table.length;
		speed_offset += 1;
		if (speed_offset === length) {
			speed_offset = 0;
		}
		$('#btn-speed').text(speed_table[speed_offset].name);
		g_current_time = g_last_time;

	});

	$('#process').change(function () {
		var process = $('#process').val();
		//var beginTime = parseInt(g_total_time * process / 100);
		speed_offset = 0;
		$('#btn-speed').text(speed_table[speed_offset].name);
		//console.log('xxxxxx', $('#process').val(), beginTime);
	});

	function init() {
		var term_info = g_term_list.term_list[0];
		g_win_size_next_idx = 1;
		if (g_console_term != null) {
			g_console_term.destroy();
		}
		g_console_term = new Terminal({
			cols: term_info.w,
			rows: term_info.h,
			useStyle: true
		});
		g_console_term.open();
		$('.terminal').detach().appendTo('#terminal');
		var width = $('[class="terminal"]').width();
		$('#process').width(width);
		$('#process').val(g_process);

		$("#play-status").text("正在播放");

		g_bNeedStop = false;
		g_bPlay = true;
		g_finish = false;
		g_current_time = 0;
		g_cur_play_file_id = 0;
		g_cur_play_file_offset = 0;
		g_time_id = setInterval(done, record_tick);

	}

	function done() {
		if (g_bNeedStop) {
			g_bPlay = false;
			return;
		}

		if (typeof(g_data[g_cur_play_file_id]) == "undefined") {
			g_req_count++;
			if (g_req_count > 2000) {
				g_req_count = 0;
				$("#play-status").text("正在缓存数据[" + g_cur_play_file_id + ":" + g_total_file_count + "]");
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
		$("#play-status").text("正在播放");
		g_current_time += record_tick;
		interal_tick += record_tick;
		var play_data = g_data[g_cur_play_file_id][g_cur_play_file_offset];
		var temp_time = g_current_time * speed_table[speed_offset].speed;

		if (g_win_size_next_idx < g_win_size_total_cnt) {
			var size_info = g_term_list.term_list[g_win_size_next_idx];
			if (size_info.t < temp_time) {
				//console.log('resize to', size_info.w, size_info.h);
				g_console_term.resize(size_info.w, size_info.h);
				g_win_size_next_idx += 1;
			}
		}

		//播放
		if (play_data.t < temp_time) {
			var rec_length = g_data[g_cur_play_file_id].length;
			//console.log('time', g_current_time, play_data.t, 'file_count', g_total_file_count, 'file_index', g_cur_play_file_id, 'length', rec_length, 'offset:', g_cur_play_file_offset);
			g_last_time = play_data.t;
			interal_tick = 0;
			g_console_term.write(play_data.d);
			//console.log('g_process:', g_process, 't:', play_data.t, 'totol time:', g_total_time);
			if ((g_cur_play_file_offset + 1) == rec_length) {
				if ((g_cur_play_file_id + 1) == g_total_file_count) {
					//console.log('play finish');
					$('#process').val(100);
					$("#play-status").text('播放完成');
					$("#play-time").text(parseInt(g_total_time / 1000) + '秒');
					g_finish = true;
					clearInterval(g_time_id);
					return;
				} else {
					g_cur_play_file_offset = 0;
					g_cur_play_file_id++;
				}
			} else {
				g_cur_play_file_offset++;
			}
		} else {
			//不播放
		}
		g_process = parseInt((g_last_time + interal_tick) * 100 / g_total_time);
		$('#process').val(g_process);
		var temp = parseInt((g_last_time + interal_tick) / 1000);
		$("#play-time").text(temp + '/' + parseInt(g_total_time / 1000) + '秒');
	}

	function play() {
		if (g_finish || g_bPlay) {
			return;
		}
		g_bNeedStop = false;
		g_bPlay = true;
		g_time_id = setInterval(done, record_tick);
	}

	function pasue() {
		clearInterval(g_time_id);
		g_bNeedStop = true;
		g_bPlay = false;
		$("#play-status").text("已经暂停");
	}

	function replay() {
		clearInterval(g_time_id);
		init();
	}
};
