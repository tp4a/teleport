<%!
    page_title_ = '配置管理'
    page_menu_ = ['config']
    page_id_ = 'config'
%>
<%inherit file="../page_base.mako"/>

<%block name="extend_js">
    ##     <script type="text/javascript" src="${ static_url('js/ui/teleport.js') }"></script>

    <script type="text/javascript" src="${ static_url('js/ui/config/info.js') }"></script>
</%block>

<%block name="breadcrumb">
    <ol class="breadcrumb">
        <li><i class="fa fa-cogs fa-fw"></i> ${self.attr.page_title_}</li>
    </ol>
</%block>

<%block name="extend_css">
    <style type="text/css">
        .box {
            padding-left: 30px;
        }

        h2 {
            margin-left:-20px;
            font-size:160%;
        }

        h3 {
            font-size: 120%;
            font-weight: bold;
        }

        .table {
            width: auto;
        }

        .table .key {
            text-align: right;
        }

        .table .value {
            text-align: left;
            font-weight: bold;
        }

        .table .value .error {
            color: #ff4c4c;
        }

        .table .value .disabled {
            color: #ffa861;
        }

        .db-box {
            margin-bottom: 20px;
        }

        .notice-box {
            border: 1px solid #e2cab4;
            background-color: #ffe4cb;
            padding: 15px;
            color: #000000;
            margin-bottom: 10px;
        }

    </style>
</%block>

## Begin Main Body.

<div class="page-content">

    <!-- begin box -->
    <div class="box">

        <div>
            <h2><strong>服务器配置信息</strong></h2>
            <table id="info-kv" class="table"></table>
        </div>

        <div>
            <hr/>
            <h2><strong>数据库管理</strong></h2>

            <div class="db-box">
                <h3>导出</h3>
                <p>将数据库中所有数据导出到sql文件，可用作备份。</p>
                <button type="button" id="btn-db-export" class="btn btn-sm btn-primary"><i class="fa fa-sign-out fa-fw"></i> 导出数据库</button>
            </div>

            <div class="db-box">
                <h3>导入</h3>
                <p>清空当前数据库中所有数据，然后从sql文件中导入数据到数据库中。</p>
                <p class="notice-box">注意！导入操作将导致现有数据被清除且无法恢复，请谨慎使用！</p>
                <button type="button" id="btn-db-import" class="btn btn-sm btn-danger"><i class="fa fa-sign-in fa-fw"></i> 导入数据库</button>
            </div>
        </div>

    </div>
    <!-- end of box -->
</div>


<%block name="extend_content"></%block>


<%block name="embed_js">
    <script type="text/javascript">
        ywl.add_page_options(${ page_param });
    </script>
</%block>
