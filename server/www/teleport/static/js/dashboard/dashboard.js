"use strict";

$app.on_init = function (cb_stack) {
    $app.MAX_OVERLOAD_DATA = 20;
    $app.dom = {
        count_user: $('#count-user')
        , count_host: $('#count-host')
        , count_acc: $('#count-acc')
        , count_conn: $('#count-conn')
    };

    // refresh basic info every 1m.
    $app.load_basic_info();
    // refresh overload info every 5m.
    $app.load_overload_info();

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

$app.load_overload_info = function () {
    var i = 0;
    // var bar_x = [];
    // for (i = 0; i < $app.MAX_OVERLOAD_DATA; i++) {
    //     bar_x.push(i);
    // }

    var now = Math.floor(Date.now() / 1000);
    console.log('now', now);

    $app.bar_cpu_user = [];
    $app.bar_cpu_sys = [];
    var t = tp_local2utc(now - $app.MAX_OVERLOAD_DATA - 1);
    console.log(t);
    for (i = 0; i < $app.MAX_OVERLOAD_DATA; i++) {
        var x = t + i;
        console.log(x, t);
        $app.bar_cpu_user.push([
            {
                name: x.toString()
                , value: [tp_format_datetime(tp_utc2local(x)), 0]
            }
        ]);
        $app.bar_cpu_sys.push([
            {
                name: x.toString()
                , value: [tp_format_datetime(tp_utc2local(x)), 0]
            }
        ]);
    }
    //console.log('--', $app.bar_cpu_data);

    $app.bar_cpu = echarts.init(document.getElementById('bar-cpu'));
    $app.bar_cpu.setOption({
        title: {
            // show: false
            text: 'CPU负载'
            , top: 0
            , left: 50
            , textStyle: {
                color: 'rgba(0,0,0,0.5)'
                , fontSize: 14
            }
        },
        grid: {
            show: true
            , left: 30
            , right: 20
            , top: 30
            , bottom: 20
        },
        tooltip: {
            trigger: 'axis'
            , formatter: function (params) {
                console.log(params);
                //params = params[0];
                var t = parseInt(params[0].name);
                return tp_format_datetime(tp_utc2local(t), 'HH:mm:ss') + '<br/>' + params[0].value[1] + '%, ' + params[1].value[1] + '%';
            }
            , axisPointer: {
                animation: false
            }
        },
        // legend: {
        //     // show: false
        // },
        xAxis: {
            type: 'time'
            , boundaryGap: false
            , axisLine: {show: false}
        },
        // yAxis: {type: 'value', min: 'dataMin', axisLine: {show: false}, splitLine: {show: false}},
        yAxis: {
            type: 'value'
            , axisLine: {
                show: false
            }
            , min: 0
            , max: 100
            , boundaryGap: [0, '50%']

        },
        series: [
            {
                name: 'cpu-sys'
                , type: 'line'
                , smooth: true
                , symbol: 'none'
                , stack: 'a'
                , showSymbol: false
                , data: $app.bar_cpu_sys
            }
            , {
                name: 'cpu-user'
                , type: 'line'
                , smooth: true
                , symbol: 'none'
                , stack: 'a'
                , showSymbol: false
                , data: $app.bar_cpu_user
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
        // 订阅：
        $app.ws.send('{"method": "subscribe", "params": ["sys_real_status"]}');
    };
    $app.ws.onclose = function (e) {
        // console.log('[ws] ws-on-close', e);
        setTimeout($app.init_ws, 5000);
    };
    $app.ws.onmessage = function (e) {
        var t = JSON.parse(e.data);
        // console.log('[ws] ws-on-message', t);

        if (t.subscribe === 'sys_real_status') {
            $app.bar_cpu_user.shift();
            $app.bar_cpu_user.push({
                'name': t.data.t.toString(),
                'value': [tp_format_datetime(tp_utc2local(t.data.t)), t.data.c.u]
            });
            $app.bar_cpu_sys.shift();
            $app.bar_cpu_sys.push({
                'name': t.data.t.toString(),
                'value': [tp_format_datetime(tp_utc2local(t.data.t)), t.data.c.s]
            });
            //console.log($app.bar_cpu_data);
            console.log('--', t.data.t);

            $app.bar_cpu.setOption(
                {
                    // xAxis: {data: 1},
                    series: [
                        {
                            name: 'cpu-user'
                            , data: $app.bar_cpu_user
                        }
                        , {
                            name: 'cpu-sys'
                            , data: $app.bar_cpu_sys
                        }
                    ]
                }
            );

        }
    };
};
