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
        <li><i class="fa fa-server"></i> ${self.attr.page_title_}</li>
        <li><span id="recorder-info"></span></li>
    </ol>
</%block>


<div class="page-content">
    <div ng-controller="TerminalRecordCtrl">
        <button id="btn-play" type="button" class="btn btn-primary btn-sm" style="width:80px;"><i class="fa fa-pause"> 暂停</i></button>
        <button id="btn-restart" type="button" class="btn btn-success btn-sm"><i class="fa fa-refresh"></i> 重新播放</button>

        <button id="btn-speed" type="button" class="btn btn-warning btn-sm" style="width:80px;">正常速度</button>
        <span id="play-status" class="badge badge-normal" style="margin-left:5px;">状态:正在获取数据</span>
        <span id="play-time" class="badge badge-success" style="margin-left:5px;">总时长:未知</span>
        <input id="progress" type="range" value="0" min=0 max=100 style="margin-top: 10px;"/>
        <div id="terminal" style="margin-top: 10px;"></div>

    </div>
</div>




<%block name="extend_content">

</%block>



<%block name="embed_js">
    <script type="text/javascript">
        ywl.add_page_options({
            record_id:${record_id}
        });

    </script>
</%block>