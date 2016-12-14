/*! ywl_log v1.0.1, (c)2015 eomsoft.net */
"use strict";

var ywl_log_analysis = {
    43:log_process_get_process_by_name_43,
    61:log_analysis_file_list_61

};

function log_analysis_file_list_61(data) {

    var message = data;
    var _obj = JSON.parse(data);
    var _file_path = _obj['path'];
    if (_file_path != undefined){
        message = _file_path;
    }
    return message;
}

function log_process_get_process_by_name_43(data) {

    var message = data;
    var _obj = JSON.parse(data);
    var _process_name = _obj['Name'];
    if (_process_name != undefined){
        message = _process_name;
    }
    return message;
}