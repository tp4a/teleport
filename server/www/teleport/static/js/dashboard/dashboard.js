"use strict";

$app.on_init = function (cb_stack) {
    $app.MAX_OVERLOAD_DATA = 10 * 60 / 5;
    $app.dom = {
        count_user: $('#count-user')
        , count_host: $('#count-host')
        , count_acc: $('#count-acc')
        , count_conn: $('#count-conn')
    };

    // refresh basic info every 1m.
    $app.load_basic_info();
    // refresh overload info every 5m.
    //$app.load_overload_info();

    $app.ws = null;
    $app.init_ws();

    cb_stack.exec();
};

$app.load_basic_info = function () {
    $tp.ajax_post_json('/dashboard/do-get-basic', {},
        function (ret) {
            console.log(ret);
            if (ret.code === TPE_OK) {
                $app.dom.count_user.text(ret.data.count_user);
                $app.dom.count_host.text(ret.data.count_host);
                $app.dom.count_acc.text(ret.data.count_acc);
                $app.dom.count_conn.text(ret.data.count_conn);
            } else {
                console.log('do-get-basic failed：' + tp_error_msg(ret.code, ret.message));
            }

        },
        function () {
            console.log('can not connect to server.');
        }
    );

    setTimeout($app.load_basic_info, 60 * 1000);
};

$app.init_sys_status_info = function (data) {
    var i = 0;
    // var t = (Math.floor(Date.now() / 1000) - $app.MAX_OVERLOAD_DATA - 1) * 1000;
    console.log(data);

    //=====================================
    // CPU
    //=====================================

    $app.bar_cpu_user = [];
    $app.bar_cpu_sys = [];
    for (i = 0; i < data.length; i++) {
        // var x = t + i * 1000;
        $app.bar_cpu_user.push({name: tp_format_datetime(tp_utc2local(data[i].t), 'HH:mm:ss'), value: [tp_utc2local(data[i].t)*1000, data[i].c.u]});
        $app.bar_cpu_sys.push({name: tp_format_datetime(tp_utc2local(data[i].t), 'HH:mm:ss'), value: [tp_utc2local(data[i].t)*1000, data[i].c.s]});
    }

    var clr_user = '#e2524c';
    var clr_user_area = '#f7827a';
    var clr_sys = '#558c5a';
    var clr_sys_area = '#3dc34a';

    $app.bar_cpu = echarts.init(document.getElementById('bar-cpu'));
    $app.bar_cpu.setOption({
        title: {
            // show: false
            text: 'CPU负载',
            top: 0,
            textStyle: {
                color: 'rgba(0,0,0,0.5)',
                fontSize: 14
            }
        },
        color: [clr_sys, clr_user],
        grid: {
            show: true
            , left: 30
            , right: 20
            , top: 30
            , bottom: 20
        },
        tooltip: {
            trigger: 'axis',
            formatter: function (params) {
                return params[0].name + '<br/>'+ params[1].seriesName + ': ' + params[1].value[1] + '%<br/>' + params[0].seriesName + ': ' + params[0].value[1] + '%';
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
        xAxis: {
            type: 'time',
            boundaryGap: false,
            splitNumber: 10,
            axisLine: {show: false}
        },
        yAxis: {
            type: 'value',
            axisLine: {show: false},
            min: 0,
            max: 100,
            containLabel: true

        },
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
                            color: clr_sys
                        }, {
                            offset: 1,
                            color: clr_sys_area
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
                            color: clr_user
                        }, {
                            offset: 1,
                            color: clr_user_area
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
        $app.bar_mem_used.push({name: tp_format_datetime(tp_utc2local(data[i].t), 'HH:mm:ss'), value: [tp_utc2local(data[i].t)*1000, tp_digital_precision(data[i].m.u * 100 / data[i].m.t, 1)]});
    }

    var clr_mem = '#5671e2';
    var clr_mem_area = '#8da4f9';

    $app.bar_mem = echarts.init(document.getElementById('bar-mem'));
    $app.bar_mem.setOption({
        title: {
            text: '内存用量',
            top: 0,
            textStyle: {
                color: 'rgba(0,0,0,0.5)',
                fontSize: 14
            }
        },
        color: [clr_mem],
        grid: {
            show: true
            , left: 30
            , right: 20
            , top: 30
            , bottom: 20
        },
        tooltip: {
            trigger: 'axis',
            formatter: function (params) {
                return params[0].name + ': '+ params[0].value[1] + '%';
            },
            axisPointer: {
                animation: false
            }
        },
        xAxis: {
            type: 'time',
            boundaryGap: false,
            splitNumber: 10,
            axisLine: {show: false}
        },
        yAxis: {
            type: 'value',
            axisLine: {show: false},
            min: 0,
            max: 100,
            containLabel: true
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
};

$app.init_ws = function () {
    if ($app.ws !== null)
        delete $app.ws;

    var _sid = Cookies.get('_sid');
    $app.ws = new WebSocket('ws://' + location.host + '/ws/' + _sid);

    $app.ws.onopen = function (e) {
        $app.ws.send('{"method": "request", "param": "sys_status"}');
        // 订阅：
        // $app.ws.send('{"method": "subscribe", "params": ["sys_status"]}');
    };
    $app.ws.onclose = function (e) {
        // console.log('[ws] ws-on-close', e);
        setTimeout($app.init_ws, 5000);
    };
    $app.ws.onmessage = function (e) {
        var t = JSON.parse(e.data);
        // console.log(t);

        if (t.method === 'request' && t.param === 'sys_status') {
            $app.init_sys_status_info(t.data);
            // 订阅系统状态信息
            $app.ws.send('{"method": "subscribe", "params": ["sys_status"]}');
            return;
        }

        if (t.method === 'subscribe' && t.param === 'sys_status') {
            $app.bar_cpu_user.shift();
            $app.bar_cpu_user.push({name: tp_format_datetime(tp_utc2local(t.data.t), 'HH:mm:ss'), value: [tp_utc2local(t.data.t) * 1000, t.data.c.u]});
            $app.bar_cpu_sys.shift();
            $app.bar_cpu_sys.push({name: tp_format_datetime(tp_utc2local(t.data.t), 'HH:mm:ss'), value: [tp_utc2local(t.data.t) * 1000, t.data.c.s]});
            $app.bar_cpu.setOption(
                {series: [{data: $app.bar_cpu_sys}, {data: $app.bar_cpu_user}]}
            );

            $app.bar_mem_used.shift();
            $app.bar_mem_used.push({name: tp_format_datetime(tp_utc2local(t.data.t), 'HH:mm:ss'), value: [tp_utc2local(t.data.t) * 1000, Math.round(t.data.m.u / t.data.m.t * 100, 2)]});
            $app.bar_mem.setOption(
                {series: [{data: $app.bar_mem_used}]}
            );

        }
    };
};
