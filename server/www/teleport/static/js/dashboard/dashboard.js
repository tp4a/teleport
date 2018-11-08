"use strict";

$app.on_init = function (cb_stack) {
    $app.MAX_OVERLOAD_DATA = 10 * 60 / 5;
    $app.dom = {
        count_user: $('#count-user'),
        count_host: $('#count-host'),
        count_acc: $('#count-acc'),
        count_conn: $('#count-conn'),
        bar_cpu: $('#bar-cpu'),
        bar_mem: $('#bar-mem'),
        bar_net: $('#bar-net'),
        bar_disk: $('#bar-disk')
    };

    $app.stat_counter = {
        user: -1,
        host: -1,
        acc: -1,
        conn: -1
    };

    window.onresize = $app.on_screen_resize;

    $app.ws = null;
    $app.init_ws();

    cb_stack.exec();
};

$app.init_sys_status_info = function (data) {
    var i = 0;

    var grid_cfg = {
        show: true, left: 60, right: 20, top: 30, bottom: 20
    };

    var axis_time_cfg = {
        type: 'time',
        boundaryGap: false,
        splitNumber: 10,
        minInterval: 1000 * 60,
        maxInterval: 1000 * 60,
        axisLine: {show: false},
        axisTick: {show: false},
        axisLabel: {
            margin: 3,
            fontSize: 11,
            fontFamily: 'Monaco, Lucida Console, Consolas, Courier',
            formatter: function (value, index) {
                return tp_format_datetime_ms(tp_utc2local_ms(value), 'HH:mm');
            }
        }
    };

    var axis_percent_cfg = {
        type: 'value',
        axisLine: {show: false},
        axisTick: {show: false},
        boundaryGap: [0, '70%'],
        axisLabel: {
            fontSize: 11,
            fontFamily: 'Monaco, Lucida Console, Consolas, Courier',
            formatter: function (value, index) {
                if (index === 0)
                    return '';
                return value + '%';
            }
        }
    };

    var axis_size_cfg = {
        type: 'value',
        axisLine: {show: false},
        axisTick: {show: false},
        splitNumber: 5,
        boundaryGap: [0, '20%'],
        axisLabel: {
            margin: 3,
            fontSize: 11,
            fontFamily: 'Monaco, Lucida Console, Consolas, Courier',
            formatter: function (value, index) {
                if (index === 0)
                    return '';
                return tp_size2str(value, 1);
                // return tp_echarts_size(value).val;
            }
        }
    };

    //=====================================
    // CPU
    //=====================================

    $app.bar_cpu_user = [];
    $app.bar_cpu_sys = [];
    for (i = 0; i < data.length; i++) {
        $app.bar_cpu_user.push({name: tp_format_datetime_ms(tp_utc2local_ms(data[i].t), 'HH:mm:ss'), value: [data[i].t, data[i].cpu.u]});
        $app.bar_cpu_sys.push({name: tp_format_datetime_ms(tp_utc2local_ms(data[i].t), 'HH:mm:ss'), value: [data[i].t, data[i].cpu.s]});
    }

    var clr_cpu_user = '#e2524c';
    var clr_cpu_user_area = '#f7827a';
    var clr_cpu_sys = '#558c5a';
    var clr_cpu_sys_area = '#3dc34a';

    $app.bar_cpu = echarts.init(document.getElementById('bar-cpu'));
    $app.bar_cpu.setOption({
        title: {
            text: 'CPU负载',
            left: 'center',
            top: 0,
            textStyle: {
                color: 'rgba(0,0,0,0.5)',
                fontSize: 14
            }
        },
        useUTC: true,
        color: [clr_cpu_sys, clr_cpu_user],
        grid: grid_cfg,
        tooltip: {
            trigger: 'axis',
            formatter: function (params) {
                var ret = [];
                ret.push(params[0].name);
                ret.push(params[0].seriesName + ': ' + params[0].value[1] + '%');
                if (params.length > 1) {
                    ret.push(params[1].seriesName + ': ' + params[1].value[1] + '%');
                }
                return ret.join('<br/>');
            },
            axisPointer: {
                animation: false
            }
        },
        legend: {
            right: 20,
            data: [
                {name: '系统', icon: 'rect'},
                {name: '用户', icon: 'rect'}
            ]
        },
        xAxis: axis_time_cfg,
        yAxis: axis_percent_cfg,
        series: [
            {
                name: '系统',
                type: 'line', smooth: true, symbol: 'none', stack: 'a', showSymbol: false,
                lineStyle: {
                    normal: {
                        width: 1
                    }
                },
                areaStyle: {
                    normal: {
                        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{
                            offset: 0,
                            color: clr_cpu_sys
                        }, {
                            offset: 1,
                            color: clr_cpu_sys_area
                        }])
                    }
                },
                data: $app.bar_cpu_sys
            },
            {
                name: '用户', type: 'line', smooth: true, symbol: 'none', stack: 'a', showSymbol: false,
                lineStyle: {
                    normal: {width: 1}
                },
                areaStyle: {
                    normal: {
                        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{
                            offset: 0,
                            color: clr_cpu_user
                        }, {
                            offset: 1,
                            color: clr_cpu_user_area
                        }])
                    }
                },
                data: $app.bar_cpu_user
            }
        ]
    });

    //=====================================
    // Memory
    //=====================================

    $app.bar_mem_used = [];
    for (i = 0; i < data.length; i++) {
        $app.bar_mem_used.push({name: tp_format_datetime_ms(tp_utc2local_ms(data[i].t), 'HH:mm:ss'), value: [data[i].t, tp_digital_precision(data[i].mem.u * 100 / data[i].mem.t, 1)]});
    }

    var clr_mem = '#5671e2';
    var clr_mem_area = '#8da4f9';

    $app.bar_mem = echarts.init(document.getElementById('bar-mem'));
    $app.bar_mem.setOption({
        title: {
            text: '内存用量',
            left: 'center',
            top: 0,
            textStyle: {
                color: 'rgba(0,0,0,0.5)',
                fontSize: 14
            }
        },
        useUTC: true,
        color: [clr_mem],
        grid: grid_cfg,
        tooltip: {
            trigger: 'axis',
            formatter: function (params) {
                return params[0].name + '<br/>内存使用: ' + params[0].value[1] + '%';
            },
            axisPointer: {animation: false}
        },
        xAxis: axis_time_cfg,
        yAxis: {
            type: 'value',
            axisLine: {show: false},
            axisTick: {show: false},
            min: 0,
            max: 100,
            // boundaryGap: [0, '60%'],
            axisLabel: {
                margin: 5,
                fontSize: 11,
                fontFamily: 'Monaco, Lucida Console, Consolas, Courier',
                formatter: function (value, index) {
                    if (index === 0)
                        return '';
                    return value + '%';
                }
            }
        },
        series: [
            {
                //name: '系统',
                type: 'line', smooth: true, symbol: 'none', stack: 'a', showSymbol: false,
                lineStyle: {
                    normal: {
                        width: 1
                    }
                },
                areaStyle: {
                    normal: {
                        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{
                            offset: 0,
                            color: clr_mem
                        }, {
                            offset: 1,
                            color: clr_mem_area
                        }])
                    }
                },
                data: $app.bar_mem_used
            }
        ]
    });

    //=====================================
    // Network
    //=====================================

    $app.bar_net_recv = [];
    $app.bar_net_sent = [];
    for (i = 0; i < data.length; i++) {
        $app.bar_net_recv.push({name: tp_format_datetime_ms(tp_utc2local_ms(data[i].t), 'HH:mm:ss'), value: [data[i].t, data[i].net.r]});
        $app.bar_net_sent.push({name: tp_format_datetime_ms(tp_utc2local_ms(data[i].t), 'HH:mm:ss'), value: [data[i].t, data[i].net.s]});
    }

    var clr_net_sent = '#558c5a';
    var clr_net_recv = '#e2524c';

    $app.bar_net = echarts.init(document.getElementById('bar-net'));
    $app.bar_net.setOption({
        title: {
            text: '网络流量',
            left: 'center',
            top: 0,
            textStyle: {
                color: 'rgba(0,0,0,0.5)',
                fontSize: 14
            }
        },
        useUTC: true,
        color: [clr_net_sent, clr_net_recv],
        grid: grid_cfg,
        tooltip: {
            trigger: 'axis',
            formatter: function (params) {
                var ret = [];
                ret.push(params[0].name);
                ret.push(params[0].seriesName + ': ' + tp_size2str(params[0].value[1], 2));
                if (params.length > 1) {
                    ret.push(params[1].seriesName + ': ' + tp_size2str(params[1].value[1], 2));
                }
                return ret.join('<br/>');
            },
            axisPointer: {
                animation: false
            }
        },
        legend: {
            right: 20,
            data: [
                {name: '发送', icon: 'rect'},
                {name: '接收', icon: 'rect'}
            ]
        },
        xAxis: axis_time_cfg,
        yAxis: axis_size_cfg,
        series: [
            {
                name: '发送', type: 'line', smooth: true, symbol: 'none', stack: 'b', showSymbol: false,
                lineStyle: {
                    normal: {width: 1}
                },
                data: $app.bar_net_sent
            },
            {
                name: '接收',
                type: 'line', smooth: true, symbol: 'none', stack: 'a', showSymbol: false,
                lineStyle: {
                    normal: {
                        width: 1
                    }
                },
                data: $app.bar_net_recv
            }
        ]
    });

    //=====================================
    // Disk IO
    //=====================================

    $app.bar_disk_read = [];
    $app.bar_disk_write = [];
    for (i = 0; i < data.length; i++) {
        $app.bar_disk_read.push({name: tp_format_datetime_ms(tp_utc2local_ms(data[i].t), 'HH:mm:ss'), value: [data[i].t, data[i].disk.r]});
        $app.bar_disk_write.push({name: tp_format_datetime_ms(tp_utc2local_ms(data[i].t), 'HH:mm:ss'), value: [data[i].t, data[i].disk.w]});
    }

    var clr_disk_read = '#558c5a';
    var clr_disk_write = '#e2524c';

    $app.bar_disk = echarts.init(document.getElementById('bar-disk'));
    $app.bar_disk.setOption({
        title: {
            text: '磁盘读写',
            left: 'center',
            top: 0,
            textStyle: {
                color: 'rgba(0,0,0,0.5)',
                fontSize: 14
            }
        },
        useUTC: true,
        color: [clr_disk_read, clr_disk_write],
        grid: grid_cfg,
        tooltip: {
            trigger: 'axis',
            formatter: function (params) {
                var ret = [];
                ret.push(params[0].name);
                ret.push(params[0].seriesName + ': ' + tp_size2str(params[0].value[1], 2));
                if (params.length > 1) {
                    ret.push(params[1].seriesName + ': ' + tp_size2str(params[1].value[1], 2));
                }
                return ret.join('<br/>');
            },
            axisPointer: {
                animation: false
            }
        },
        legend: {
            right: 20,
            data: [
                {name: '读取', icon: 'rect'},
                {name: '写入', icon: 'rect'}
            ]
        },
        xAxis: axis_time_cfg,
        yAxis: axis_size_cfg,
        series: [
            {
                name: '读取',
                type: 'line', smooth: true, symbol: 'none', stack: 'a', showSymbol: false,
                lineStyle: {
                    normal: {
                        width: 1
                    }
                },
                data: $app.bar_disk_read
            },
            {
                name: '写入', type: 'line', smooth: true, symbol: 'none', stack: 'b', showSymbol: false,
                lineStyle: {
                    normal: {width: 1}
                },
                data: $app.bar_disk_write
            }
        ]
    });

};

$app.update_stat_counter = function (data) {
    if ($app.stat_counter.user === -1) {
        $app.stat_counter.user = data.user;
        $app.dom.count_user.text(data.user);
    } else if ($app.stat_counter.user !== data.user) {
        $app.stat_counter.user = data.user;
        $app.dom.count_user.fadeOut(300, function () {
            $app.dom.count_user.text(data.user).fadeIn(400);
        });
    }

    if ($app.stat_counter.host === -1) {
        $app.stat_counter.host = data.host;
        $app.dom.count_host.text(data.host);
    } else if ($app.stat_counter.host !== data.host) {
        $app.stat_counter.host = data.host;
        $app.dom.count_host.fadeOut(300, function () {
            $app.dom.count_host.text(data.host).fadeIn(400);
        });
    }

    if ($app.stat_counter.acc === -1) {
        $app.stat_counter.acc = data.acc;
        $app.dom.count_acc.text(data.acc);
    } else if ($app.stat_counter.acc !== data.acc) {
        $app.stat_counter.acc = data.acc;
        $app.dom.count_acc.fadeOut(300, function () {
            $app.dom.count_acc.text(data.acc).fadeIn(400);
        });
    }

    if ($app.stat_counter.conn === -1) {
        $app.stat_counter.conn = data.conn;
        $app.dom.count_conn.text(data.conn);
    } else if ($app.stat_counter.conn !== data.conn) {
        $app.stat_counter.conn = data.conn;
        $app.dom.count_conn.fadeOut(300, function () {
            $app.dom.count_conn.text(data.conn).fadeIn(400);
        });
    }
};

$app.init_ws = function () {
    if ($app.ws !== null)
        delete $app.ws;

    var _sid = Cookies.get('_sid');
    if(location.protocol === 'http:') {
        $app.ws = new WebSocket('ws://' + location.host + '/ws/' + _sid);
    } else {
        $app.ws = new WebSocket('wss://' + location.host + '/ws/' + _sid);
    }

    $app.ws.onopen = function (e) {
        $app.ws.send('{"method": "request", "param": "sys_status"}');
        $app.ws.send('{"method": "request", "param": "stat_counter"}');
    };
    $app.ws.onclose = function (e) {
        setTimeout($app.init_ws, 5000);
    };
    $app.ws.onmessage = function (e) {
        var t = JSON.parse(e.data);

        if (t.method === 'request' && t.param === 'sys_status') {
            $app.init_sys_status_info(t.data);
            // 订阅系统状态信息
            $app.ws.send('{"method": "subscribe", "params": ["sys_status"]}');
            return;
        }

        if (t.method === 'request' && t.param === 'stat_counter') {
            $app.update_stat_counter(t.data);
            // 订阅数量信息
            $app.ws.send('{"method": "subscribe", "params": ["stat_counter"]}');
            return;
        }

        if (t.method === 'subscribe' && t.param === 'sys_status') {
            $app.bar_cpu_user.shift();
            $app.bar_cpu_user.push({name: tp_format_datetime_ms(tp_utc2local_ms(t.data.t), 'HH:mm:ss'), value: [t.data.t, t.data.cpu.u]});
            $app.bar_cpu_sys.shift();
            $app.bar_cpu_sys.push({name: tp_format_datetime_ms(tp_utc2local_ms(t.data.t), 'HH:mm:ss'), value: [t.data.t, t.data.cpu.s]});
            $app.bar_cpu.setOption(
                {series: [{data: $app.bar_cpu_sys}, {data: $app.bar_cpu_user}]}
            );

            $app.bar_mem_used.shift();
            $app.bar_mem_used.push({name: tp_format_datetime_ms(tp_utc2local_ms(t.data.t), 'HH:mm:ss'), value: [t.data.t, Math.round(t.data.mem.u / t.data.mem.t * 100, 2)]});
            $app.bar_mem.setOption(
                {series: [{data: $app.bar_mem_used}]}
            );

            $app.bar_net_recv.shift();
            $app.bar_net_recv.push({name: tp_format_datetime_ms(tp_utc2local_ms(t.data.t), 'HH:mm:ss'), value: [t.data.t, t.data.net.r]});
            $app.bar_net_sent.shift();
            $app.bar_net_sent.push({name: tp_format_datetime_ms(tp_utc2local_ms(t.data.t), 'HH:mm:ss'), value: [t.data.t, t.data.net.s]});
            $app.bar_net.setOption(
                {series: [{data: $app.bar_net_sent}, {data: $app.bar_net_recv}]}
            );

            $app.bar_disk_read.shift();
            $app.bar_disk_read.push({name: tp_format_datetime_ms(tp_utc2local_ms(t.data.t), 'HH:mm:ss'), value: [t.data.t, t.data.disk.r]});
            $app.bar_disk_write.shift();
            $app.bar_disk_write.push({name: tp_format_datetime_ms(tp_utc2local_ms(t.data.t), 'HH:mm:ss'), value: [t.data.t, t.data.disk.w]});
            $app.bar_disk.setOption(
                {series: [{data: $app.bar_disk_read}, {data: $app.bar_disk_write}]}
            );
        }

        if (t.method === 'subscribe' && t.param === 'stat_counter') {
            $app.update_stat_counter(t.data);
        }
    };
};

$app.on_screen_resize = function () {
    // console.log('avail width:', screen.availWidth, 'avail height:', screen.availHeight);
    // console.log('page width:', $(document).width(), 'page height:', $(document).height());
    // console.log('window width:', $(window).width(), 'window height:', $(window).height());
    // console.log('client width:', $(window).innerWidth(), 'client height:', $(window).innerHeight());

    // var win = window, d = document, e = d.documentElement, b = d.getElementsByTagName('body')[0],
    //     w = win.innerWidth || e.clientWidth || b.clientWidth,
    //     h = win.innerHeight || e.clientHeight || b.clientHeight;

    $app.bar_cpu.resize({width: 'auto', height: 'auto'});
    $app.bar_mem.resize({width: 'auto', height: 'auto'});
    $app.bar_net.resize({width: 'auto', height: 'auto'});
    $app.bar_disk.resize({width: 'auto', height: 'auto'});
};
