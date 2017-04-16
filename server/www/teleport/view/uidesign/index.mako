<%!
    page_title_ = '页面部件测试'
    page_menu_ = ['with-sidebar', 'normal']
%>
<%inherit file="../page_base.mako"/>

<%block name="extend_js">
</%block>

<%block name="breadcrumb">
    <ol class="breadcrumb">
        <li><i class="fa fa-paint-brush fa-fw"></i> ${self.attr.page_title_}</li>
        <li>普通页面</li>
    </ol>
</%block>


<%block name="embed_js">
    <script type="text/javascript">
        $(document).ready(function () {
        });
    </script>
</%block>

<%block name="extend_css">

</%block>

<%block name="sidebar_nav_menu">
    <%include file="_sidebar_nav_menu.mako" />
</%block>



<div class="page-content">
    <div class="box">
        <h1>这是一级标题，This is H1.</h1>
        <h2>这是二级标题，This is H2.</h2>
        <h3>这是三级标题，This is H3.</h3>
        <h4>这是四级标题，This is H4.</h4>
        <h5>这是五级标题，This is H5.</h5>
        <p>这是正文，this is content.</p>
    </div>

    <div class="box">
        <div>
            <p>徽章默认：[badge] <span class="badge">1</span></p>
            <p>徽章尺寸：[badge] <span class="badge">比较长的文字</span>，[badge badge-sm] <span class="badge badge-sm">小尺寸</span></p>
            <p>
                徽章上标：[badge badge-sup] <span class="badge badge-sup">1</span>，
                [badge badge-sm badge-sup] <span class="badge badge-sm badge-sup">1</span>，
                [badge badge-sm badge-sup badge-danger] <span class="badge badge-sm badge-sup badge-danger">3</span>，
                徽章配合图标：<span class="fa fa-bell fa-fw" style="font-size:16px;"></span><span class="badge badge-sm badge-sup badge-danger">3</span>
            </p>
            <p>
                徽章颜色：[badge] <span class="badge">默认</span>，
                [badge badge-info] <span class="badge badge-ignore">忽略</span>，
                [badge badge-info] <span class="badge badge-info">信息</span>，
                [badge badge-primary] <span class="badge badge-primary">重要</span>，
                [badge badge-success] <span class="badge badge-success">成功</span>，
                [badge badge-warning] <span class="badge badge-warning">警告</span>，
                [badge badge-danger] <span class="badge badge-danger">危险（错误）</span>
            </p>
            <p>
                徽章颜色（正常）：
                <span class="badge">默认</span>
                <span class="badge badge-ignore">忽略</span>
                <span class="badge badge-info">信息</span>
                <span class="badge badge-primary">重要</span>
                <span class="badge badge-success">成功</span>
                <span class="badge badge-warning">警告</span>
                <span class="badge badge-danger">危险（错误）</span>
            </p>
            <p>
                徽章颜色（小）：
                <span class="badge badge-sm">默认</span>
                <span class="badge badge-sm badge-ignore">忽略</span>
                <span class="badge badge-sm badge-info">信息</span>
                <span class="badge badge-sm badge-primary">重要</span>
                <span class="badge badge-sm badge-success">成功</span>
                <span class="badge badge-sm badge-warning">警告</span>
                <span class="badge badge-sm badge-danger">危险（错误）</span>
            </p>
        </div>
    </div>

    <div class="box">
        <div>
            <p>标签默认：[label] <span class="label">标签文字</span></p>
            <p>标签尺寸：[label] <span class="label">比较长的文字</span>，[label label-sm] <span class="label label-sm">小尺寸</span></p>
            <p>
                标签颜色：
                [label] <span class="label">默认</span>，
                [label label-ignore] <span class="label label-ignore">忽略</span>，
                [label label-info] <span class="label label-info">信息</span>，
                [label label-primary] <span class="label label-primary">重要</span>，
                [label label-success] <span class="label label-success">成功</span>，
                [label label-warning] <span class="label label-warning">警告</span>，
                [label label-danger] <span class="label label-danger">危险（错误）</span>，
            </p>
            <p>
                标签颜色（正常）：
                <span class="label">默认</span>
                <span class="label label-ignore">忽略</span>
                <span class="label label-info">信息</span>
                <span class="label label-primary">重要</span>
                <span class="label label-success">成功</span>
                <span class="label label-warning">警告</span>
                <span class="label label-danger">危险（错误）</span>
            </p>
            <p>
                标签颜色（小）：
                <span class="label label-sm">默认</span>
                <span class="label label-sm label-ignore">忽略</span>
                <span class="label label-sm label-info">信息</span>
                <span class="label label-sm label-primary">重要</span>
                <span class="label label-sm label-success">成功</span>
                <span class="label label-sm label-warning">警告</span>
                <span class="label label-sm label-danger">危险（错误）</span>
            </p>
        </div>
    </div>


</div>

