<%!
	page_title_ = '录像回放'
%>

<%inherit file="../page_no_sidebar_base.mako"/>
<%block name="extend_js">
    <script type="text/javascript" src="${ static_url('js/common/term.js') }"></script>
    <script type="text/javascript" src="${ static_url('js/ui/record.js') }"></script>
</%block>

<%block name="breadcrumb">
    <ol class="breadcrumb">
        <li><i class="fa fa-server fa-fw"></i> 录像回放</li>
    </ol>
</%block>


<div class="page-content">
    <div ng-controller="TerminalRecordCtrl">
        <button id="btn-stop"  type="button" class="btn btn-danger btn-sm" ><i class="glyphicon glyphicon-stop"></i> 暂停</button>
        <button id="btn-conitune"  type="button" class="btn btn-primary btn-sm" ><i class="glyphicon glyphicon-send"></i> 继续</button>
        <button id="btn-restart"  type="button" class="btn btn-success btn-sm" ><i class="glyphicon glyphicon-refresh"></i> 重新播放</button>

        <button id="btn-speed"  type="button" class="btn btn-warning btn-sm" ><i class="glyphicon glyphicon-fast-forward"></i> 正常</button>
        <span id="play-status" class="badge badge-danger" style="margin-left:5px;">状态:正在获取数据</span>
        <span id="play-time" class="badge badge-success" style="margin-left:5px;">总时长:未知</span>
        <input id="process" type="range" value="0" min=0 max=100 style="margin-top: 10px;"/>
        <div id="terminal" style="margin-top: 10px;"></div>

    </div>
</div>




<%block name="extend_content">

</%block>



<%block name="embed_js">
    <script type="text/javascript">
        ywl.add_page_options({
            // 有些参数由后台python脚本生成到模板中，无法直接生成到js文件中，所以必须通过这种方式传递参数到js脚本中。
            record_id:${record_id}
        });

        $(document).ready(function () {
        });


    </script>
</%block>