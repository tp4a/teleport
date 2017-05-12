<%!
    page_title_ = '配置管理'
    page_menu_ = ['set', 'info']
    page_id_ = 'set'
%>
<%inherit file="../page_base.mako"/>

<%block name="extend_js">
    ##     <script type="text/javascript" src="${ static_url('js/ui/teleport.js') }"></script>

    <script type="text/javascript" src="${ static_url('js/ui/config/info.js') }"></script>
</%block>

<%block name="breadcrumb">
    <ol class="breadcrumb">
        <li><i class="fa fa-cogs fa-fw"></i> ${self.attr.page_title_}</li>
        <li>配置信息</li>
    </ol>
</%block>

<%block name="extend_css">
    <style type="text/css">
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
    </style>
</%block>

## Begin Main Body.

<div class="page-content">

    <!-- begin box -->
    <div class="box">

        <div>
            <h4><strong>服务器配置信息</strong></h4>
            <table id="info-kv" class="table"></table>
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
