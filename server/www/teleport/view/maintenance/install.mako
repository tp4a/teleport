<%!
    page_title_ = '配置TELEPORT服务'
%>
<%inherit file="../page_maintenance_base.mako"/>

<%block name="breadcrumb">
    <ol class="breadcrumb">
        <li><i class="fa fa-cog fa-fw"></i> ${self.attr.page_title_}</li>
    </ol>
</%block>

<%block name="embed_css">
    <style type="text/css">
        .container {
            background-color: #fff;
            padding-bottom:20px;
        }
        h1 {
            font-size:200%;
        }
        h2 {
            font-size:160%;
        }
    </style>
</%block>

## Begin Main Body.

<div class="page-content">

    <div class="content_box">
        <div class="container">

            <h1>配置TELEPORT服务</h1>
            <hr/>

            <h2>第一步：创建数据表 <span id="step-create-db-result"></span></h2>
            <div id="step-create-db">
                <p>请选择要使用的数据库类型（暂时仅支持sqlite，其它类型开发中）：</p>
                <input id="db-sqlite" type="radio" checked="checked" name="database" value="sqlite"/> <label for="db-sqlite">SQLite</label><br/>
                <input id="db-mysql" type="radio" name="database" value="mysql" disabled="disabled"/> <label for="db-mysql">MySQL（暂不支持）</label>
                <div>
                    <button id="btn-create-db" type="button" class="btn btn-primary"><i class="fa fa-wrench fa-fw"></i> 开始创建</button>
                </div>

                <div class="step-detail">
                    <i class="fa fa-cog fa-spin"></i> 正在创建用户表...
                </div>
            </div>


        </div>
    </div>

</div>
