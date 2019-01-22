<%!
    import app.app_ver as app_ver
    page_title_ = '升级TELEPORT服务'
%>

<%inherit file="../page_single_base.mako"/>

<%block name="extend_js_file">
    <script type="text/javascript" src="${ static_url('js/maintenance/upgrade.js') }"></script>
</%block>

<%block name="page_header">
    <div class="container-fluid top-navbar">
        <div class="brand"><a href="/" target="_blank"><span class="site-logo"></span></a></div>
        <div class="breadcrumb-container">
            <ol class="breadcrumb">
                <li><i class="fa fa-cog fa-fw"></i> ${self.attr.page_title_}</li>
            </ol>
        </div>
    </div>
</%block>


## Begin Main Body.

<div class="content-box">
    <p class="welcome-message"><i class="fa fa-heart"></i> <span>欢迎升级到 TELEPORT v${app_ver.TP_SERVER_VER} 社区版！现在还剩下一点点操作需要执行！</span></p>

    <hr/>
    <h2><i class="fa fa-chevron-right"></i> 第一步：升级数据库</h2>
    <button id="btn-upgrade" type="button" class="btn btn-primary"><i class="fa fa-wrench fa-fw"></i> 执行</button>

    <div id="steps-detail" class="steps-detail"></div>
    <div><p id="message" class="op_box" style="display:none;"></p></div>


    <div id="step2" style="display:none;">
        <hr/>
        <h2><i class="fa fa-chevron-right"></i> 已完成！</h2>
        <p>是的，没有第二步啦，升级已经完成！刷新页面即可登录 TELEPORT 啦~~</p>
    </div>

</div>
