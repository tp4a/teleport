/*! ywl v1.0.1, (c)2016 eomsoft.net */
"use strict";

var LOG_LEVEL_DEBUG = 1;
var LOG_LEVEL_VERBOSE = 10;
var LOG_LEVEL_INFO = 20;
var LOG_LEVEL_WARN = 30;
var LOG_LEVEL_ERROR = 40;

var WITH_LOG_LEVEL = LOG_LEVEL_VERBOSE;
var WITH_LOG_TRACE = false;

var log = {};
if (window.console && LOG_LEVEL_ERROR >= WITH_LOG_LEVEL) {
    log.e = function () {
        console.error.apply(console, arguments);
        if (WITH_LOG_TRACE)
            console.trace();
    };
} else {
    log.e = function () {
    };
}
if (window.console && LOG_LEVEL_WARN >= WITH_LOG_LEVEL) {
    log.w = function () {
        console.warn.apply(console, arguments);
        if (WITH_LOG_TRACE)
            console.trace();
    };
} else {
    log.w = function () {
    }
}
if (window.console && LOG_LEVEL_INFO >= WITH_LOG_LEVEL) {
    log.i = function () {
        console.info.apply(console, arguments);
        if (WITH_LOG_TRACE)
            console.trace();
    };
} else {
    log.i = function () {
    }
}
if (window.console && LOG_LEVEL_VERBOSE >= WITH_LOG_LEVEL) {
    log.v = function () {
        console.log.apply(console, arguments);
        //if(WITH_LOG_TRACE)
        //	console.trace();
    };
} else {
    log.v = function () {
    }
}
if (window.console && LOG_LEVEL_DEBUG >= WITH_LOG_LEVEL) {
    log.d = function () {
        console.log.apply(console, arguments);
        //if(WITH_LOG_TRACE)
        //	console.trace();
    };
} else {
    log.d = function () {
    }
}


// 构造一个回调函数栈，遵循先进后出的原则进行调用。
var CALLBACK_STACK = {
    create: function () {
        var self = {};

        self.cb_stack = [];

        self.add = function (cb_func, cb_args) {
            if (!_.isFunction(cb_func)) {
                log.e('need callable function.');
            }
            cb_args = cb_args || {};
            self.cb_stack.push({func: cb_func, args: cb_args});
            return self;
        };

        self.exec = function (ex_args) {
            if (self.cb_stack.length > 0) {
                var cb = self.cb_stack.pop();
                var ex_ = ex_args || [];
                cb.func(self, cb.args, ex_);
            }
        };

        self.pop = function () {
            if (self.cb_stack.length == 0) {
                return null;
            } else {
                return self.cb_stack.pop();
            }
        };

        return self;
    }
};

if (!String.prototype.startsWith) {
    String.prototype.startsWith = function (searchString, position) {
        position = position || 0;
        return this.indexOf(searchString, position) === position;
    };
}

if (!String.prototype.realLength) {
    String.prototype.realLength = function () {
        var _len = 0;
        for (var i = 0; i < this.length; i++) {
            if (this.charCodeAt(i) > 255) _len += 2; else _len += 1;
        }
        return _len;
    };
}


function digital_precision(num, keep) {
    return Math.round(num * Math.pow(10, keep)) / Math.pow(10, keep);
}

function prefixInteger(num, length) {
    return (num / Math.pow(10, length)).toFixed(length).substr(2);
}

function size2str(size, precision) {
    precision = precision || 0;
    var s = 0;
    var k = '';
    if (size < KB) {
        s = size;
        k = 'B';
    }
    else if (size < MB) {
        s = digital_precision(size / KB, precision);
        k = 'KB'
    }
    else if (size < GB) {
        s = digital_precision(size / MB, precision);
        k = 'MB'
    }
    else if (size < TB) {
        s = digital_precision(size / GB, precision);
        k = 'GB'
    }
    else if (size < PB) {
        s = digital_precision(size / TB, precision);
        k = 'TB'
    }
    else {
        s = digital_precision(size / PB, precision);
        k = 'PB'
    }

    return '' + s + ' ' + k;
}

function second2str(sec) {
    var _ret = '';
    if (sec >= SECONDS_PER_DAY) {
        var _d = Math.floor(sec / SECONDS_PER_DAY);
        _ret = '' + _d + '天';
        sec = sec % SECONDS_PER_DAY;
    }

    if (sec >= SECONDS_PER_HOUR) {
        var _h = Math.floor(sec / SECONDS_PER_HOUR);
        _ret += '' + _h + '小时';
        sec = sec % SECONDS_PER_HOUR;
    } else if (_ret.length > 0) {
        _ret += '0小时';
    }

    if (sec >= SECONDS_PER_MINUTE) {
        var _m = Math.floor(sec / SECONDS_PER_MINUTE);
        _ret += '' + _m + '分';
        sec = sec % SECONDS_PER_MINUTE;
    } else if (_ret.length > 0) {
        _ret += '0分';
    }

    _ret += '' + sec + '秒';
    return _ret;
}

function get_cookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}

function utc_to_local(timestamp) {
    //console.log('utc_to_local:', timestamp);
    var d = new Date(timestamp * 1000);
    var _local = d.getTime() - (d.getTimezoneOffset() * 60000);
    return Math.round(_local / 1000);
}

function local_to_utc(timestamp) {
    var d = new Date(timestamp * 1000);
    var _utc = d.getTime() + (d.getTimezoneOffset() * 60000);
    return Math.round(_utc / 1000);
}
function format_datetime(timestamp) {
    var d = new Date(timestamp * 1000);
    //return '' + d.getFullYear() + '-' + (d.getMonth() + 1) + '-' + d.getDate() + ' ' + d.getHours() + ':' + d.getMinutes() + ':' + d.getSeconds();

    var fmt = 'yyyy-MM-dd HH:mm:ss';
    var o = {
        "M+": d.getMonth() + 1, //月份
        "d+": d.getDate(), //日
        "H+": d.getHours(), //小时
        "m+": d.getMinutes(), //分
        "s+": d.getSeconds() //秒
        //"q+": Math.floor((this.getMonth() + 3) / 3), //季度
        //"S": d.getMilliseconds() //毫秒
    };

    if (/(y+)/.test(fmt)) {
        fmt = fmt.replace(RegExp.$1, (d.getFullYear() + "").substr(4 - RegExp.$1.length));
    }
    for (var k in o) {
        if (new RegExp("(" + k + ")").test(fmt)) {
            if (o.hasOwnProperty(k))
                fmt = fmt.replace(RegExp.$1, (RegExp.$1.length == 1) ? (o[k]) : (("00" + o[k]).substr(("" + o[k]).length)));
        }
    }
    return fmt;
}

var base64KeyStr = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=";
function base64_encode(input) {
    var output = "";
    var chr1, chr2, chr3 = "";
    var enc1, enc2, enc3, enc4 = "";
    var i = 0;
    do {
        chr1 = input.charCodeAt(i++);
        chr2 = input.charCodeAt(i++);
        chr3 = input.charCodeAt(i++);
        enc1 = chr1 >> 2;
        enc2 = ((chr1 & 3) << 4) | (chr2 >> 4);
        enc3 = ((chr2 & 15) << 2) | (chr3 >> 6);
        enc4 = chr3 & 63;
        if (isNaN(chr2)) {
            enc3 = enc4 = 64;
        } else if (isNaN(chr3)) {
            enc4 = 64;
        }
        output = output + base64KeyStr.charAt(enc1) + base64KeyStr.charAt(enc2) + base64KeyStr.charAt(enc3) + base64KeyStr.charAt(enc4);
        chr1 = chr2 = chr3 = "";
        enc1 = enc2 = enc3 = enc4 = "";
    } while (i < input.length);
    return output;
}

function base64_decode(data) {
    var o1, o2, o3, h1, h2, h3, h4, bits, i = 0,
        ac = 0,
        tmp_arr = [];

    if (!data) {
        return data;
    }
    data += '';

    do { // unpack four hexets into three octets using index points in b64
        h1 = base64KeyStr.indexOf(data.charAt(i++));
        h2 = base64KeyStr.indexOf(data.charAt(i++));
        h3 = base64KeyStr.indexOf(data.charAt(i++));
        h4 = base64KeyStr.indexOf(data.charAt(i++));

        bits = h1 << 18 | h2 << 12 | h3 << 6 | h4;

        o1 = bits >> 16 & 0xff;
        o2 = bits >> 8 & 0xff;
        o3 = bits & 0xff;

        if (h3 === 64) {
            tmp_arr[ac++] = String.fromCharCode(o1);
        } else if (h4 === 64) {
            tmp_arr[ac++] = String.fromCharCode(o1, o2);
        } else {
            tmp_arr[ac++] = String.fromCharCode(o1, o2, o3);
        }
    } while (i < data.length);

    return tmp_arr.join('');
}



function get_file_name(path) {
    var reg = /(\\+)/g;
    path = path.replace(reg, "/");
    var _path = path.split('/');
    return _path[_path.length - 1]
}

var g_unique_id = (new Date()).valueOf();
function generate_id() {
    return g_unique_id++;
}


function htmlEncode(_s) {
    if (_s.length == 0) return "";
    var s = _s.replace(/&/g, "&amp;");
    s = s.replace(/</g, "&lt;");
    s = s.replace(/>/g, "&gt;");
    //s = s.replace(/ /g, "&nbsp;");
    s = s.replace(/\'/g, "&#39;");
    s = s.replace(/\"/g, "&quot;");
    return s;
}
//
///*2.用正则表达式实现html解码*/
//function htmlDecode(_s) {
//	if (_s.length == 0) return "";
//	var s = str.replace(/&amp;/g, "&");
//	s = s.replace(/&lt;/g, "<");
//	s = s.replace(/&gt;/g, ">");
//	s = s.replace(/&nbsp;/g, " ");
//	s = s.replace(/&#39;/g, "\'");
//	s = s.replace(/&quot;/g, "\"");
//	return s;
//}
