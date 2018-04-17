<%!
    page_title_ = '录像回放'
%>

<%inherit file="../page_single_base.mako"/>

<%block name="extend_js_file">
    <script type="text/javascript" src="${ static_url('plugins/xterm/xterm.js') }"></script>
    <script type="text/javascript" src="${ static_url('js/audit/replay-telnet.js') }"></script>
</%block>

<%block name="extend_css_file">
    <link href="${ static_url('plugins/xterm/xterm.css') }" rel="stylesheet" type="text/css"/>
</%block>

<%block name="embed_css">
    <style type="text/css">
        .container {
            width:100%;
            padding-right: 20px;
        }
        #xterm-box {
            margin: 10px 0;
##             background-color: #1e1e1e;
            ##             margin-top: 10px;
            ##             margin-bottom: 48px;
            ##             width: 300px;
##             border: 1px solid #9c9c9c;
        }

        .terminal {
            font-family: Consolas, Monaco, courier-new, courier, monospace;
            color: #b7b7b7;
            font-size: 13px;
            display: inline-block;
        }

        .terminal {
            ##             background-color: transparent;
        }

        .terminal .xterm-viewport {
            ##             background-color: transparent;
            ##             display:none;
            ##             overflow: auto;
            padding-right:17px;
        }

        .terminal .xterm-rows {
##             margin:5px;
            padding:5px;
            border-right: 1px dashed #363636;
            background-color: #1e1e1e;
        }
    </style>
</%block>

<%block name="page_header">
    <div class="container-fluid top-navbar">
        <div class="breadcrumb-container">
            <ol class="breadcrumb">
                <li><i class="fa fa-server"></i> ${self.attr.page_title_}</li>
                <li class="sub-title"><span id="recorder-info"></span></li>
            </ol>
        </div>
    </div>
</%block>


<div class="page-content">
    <div id="toolbar" style="display: inline-block;">
        <button id="btn-play" type="button" class="btn btn-primary btn-sm" style="width:80px;"><i class="fa fa-pause fa-fw"> 暂停</i></button>
        <button id="btn-restart" type="button" class="btn btn-success btn-sm"><i class="fas fa-undo fa-fw"></i> 重新播放</button>

        <button id="btn-speed" type="button" class="btn btn-info btn-sm" style="width:80px;">正常速度</button>

        <button id="btn-big-font" type="button" class="btn btn-default btn-sm"><i class="fa fa-font fa-fw"></i>+</button>
        <button id="btn-small-font" type="button" class="btn btn-default btn-sm"><i class="fa fa-font fa-fw"></i>-</button>

        <div style="display:inline-block;position:relative;top:4px;margin-left:10px;margin-right:15px;">
            <span id="btn-skip" style="cursor:pointer;"><i class="far fa-check-square fa-fw"></i> 跳过无操作时间</span>
        </div>

        <span id="play-status" class="badge badge-normal" style="margin-left:5px;">正在获取数据</span>
        <span id="play-time" class="badge badge-success" style="margin-left:5px;">总时长:未知</span>
    </div>
    <input id="progress" type="range" value="0" min=0 max=100 style="margin-top: 10px;"/>
    <div id="xterm-box"></div>

</div>




<%block name="extend_content">

</%block>



<%block name="embed_js">
    <script type="text/javascript">
        $app.add_options(${page_param});
    </script>
</%block>