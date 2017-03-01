<%!
    page_title_ = '系统维护'
    ## 	page_menu_ = ['user']
    ## 	page_id_ = 'user'
%>
<%inherit file="../page_maintenance_base.mako"/>

<%block name="breadcrumb">
    <ol class="breadcrumb">
        <li><i class="fa fa-cog fa-fw"></i> ${self.attr.page_title_}</li>
    </ol>
</%block>

<%block name="embed_css">
    <style type="text/css">
        .content_box {
            margin-top:48px;
        }

        .content_box .error_sidebar {
            float: left;
            width: 160px;
            margin-left: 120px;
            font-size: 260px;
            color: #e3693b;
        }

        .content_box .error_content {
            min-height: 400px;
            width: 800px;
            padding: 30px;
            margin-left: 300px;
            background: #ffffff;
            border-radius: 5px;

            background: rgba(255, 255, 255, 0.8);
            background: #fff \9;
            z-index: 9;
            position: relative;
        }

        h1 .fa-spin {
            color:#aaa;
        }
    </style>
</%block>

## Begin Main Body.

<div class="page-content">

    <div class="content_box">
        <div class="container">

            <div class="error_sidebar">
                <i class="fa fa-exclamation-triangle"></i>
            </div>

            <div class="error_content">
                <br/>
                <h1><i class="fa fa-cog fa-spin"></i> 系统维护中...</h1>
                <hr/>
                <p>系统管理员正在紧张地维护系统，请稍后刷新页面重试！</p>
            </div>

        </div>
    </div>

</div>
