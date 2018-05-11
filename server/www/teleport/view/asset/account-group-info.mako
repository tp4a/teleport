<%!
    page_icon_class_ = 'fa fa-user-secret fa-fw'
    page_title_ = ['资产', '账号分组管理']
    page_id_ = ['asset', 'account-group']
%>
<%inherit file="../page_base.mako"/>

<%block name="extend_js_file">
    <script type="text/javascript" src="${ static_url('js/asset/account-group-info.js') }"></script>
</%block>

<%block name="breadcrumb">
    <ol class="breadcrumb">
        %for i in range(len(self.attr.page_title_)):
            %if i == 0:
                <li><i class="${self.attr.page_icon_class_}"></i> ${self.attr.page_title_[i]}</li>
            %else:
                <li>${self.attr.page_title_[i]}</li>
            %endif
        %endfor
        <li><strong id="group-name-breadcrumb"></strong><span id="group-desc"></span></li>
    </ol>
</%block>

<%block name="embed_js">
    <script type="text/javascript">
        $app.add_options(${page_param});
        if($app.options.group_id !== 0) {
            $('#group-name-breadcrumb').text($app.options.group_name);
            $('#group-name-table').text($app.options.group_name);
            if ($app.options.group_desc.length > 0)
                $('#group-desc').text(' (' + $app.options.group_desc+')');
        } else {
##             $tp.notify_error('账号组不存在！');
            $tp.disable_dom('#work-area', '账号组不存在！');
        }
    </script>
</%block>


<%block name="embed_css">
    <style>
        .user-email {
            font-family: Monaco, Lucida Console, Consolas, Courier, 'Courier New', monospace;
        }

        .user-surname {
            display: inline-block;
            min-width: 8em;
            padding-right: 15px;
        }

        .user-account {
            color: #989898;
            font-family: Monaco, Lucida Console, Consolas, Courier, 'Courier New', monospace;
        }
    </style>
</%block>

## Begin Main Body.

<div class="page-content-inner">

    <!-- begin box -->
    <div class="box" id="work-area">
        <div class="table-prefix-area">
            <div class="table-extend-cell">
                <span class="table-name"><i class="fa fa-list fa-fw"></i> 账号组 <strong id="group-name-table"></strong> 成员列表</span>
                <button id="btn-refresh-members" class="btn btn-sm btn-default"><i class="fa fa-redo fa-fw"></i> 刷新列表</button>
            </div>
            <div class="table-extend-cell table-extend-cell-right group-actions">
                <button id="btn-add-members" class="btn btn-sm btn-primary"><i class="fa fa-plus-circle fa-fw"></i> 添加账号</button>
            </div>
        </div>

        <table id="table-members" class="table table-striped table-bordered table-hover table-data no-footer dtr-inline"></table>

        <div class="table-extend-area">
            <div class="table-extend-cell checkbox-select-all"><input id="table-members-select-all" type="checkbox"/></div>
            <div class="table-extend-cell group-actions">
                <div class="btn-group" role="group">
                    <button id="btn-remove-members" type="button" class="btn btn-default"><i class="fa fa-times-circle fa-fw"></i> 移除成员账号</button>
                </div>
            </div>
            <div class="table-extend-cell table-item-counter">
                <ol id="table-members-paging"></ol>
            </div>
        </div>

        <div class="table-extend-area">
            <div class="table-extend-cell">
                <div style="text-align:right;">
                    <nav>
                        <ul id="table-members-pagination" class="pagination"></ul>
                    </nav>
                </div>
            </div>
        </div>
    </div>
    <!-- end of box -->

    <div class="box">
        <p>说明：</p>
        <ul class="help-list">
            <li>可以通过表格标题栏进行搜索或过滤，以便快速定位你需要的信息。标题栏左侧的 <i class="fa fa-undo fa-fw"></i> 可以重置过滤器。</li>
        </ul>
    </div>
</div>


<%block name="extend_content">
    <div class="modal fade" id="dlg-select-members" tabindex="-1" role="dialog">
        <div class="modal-dialog modal-lg" role="document">
            <div class="modal-content">
                <div class="modal-header">
                    <button type="button" class="close" data-dismiss="modal" aria-label="Close"><i class="fa fa-times-circle fa-fw"></i></button>
                    <h3 data-field="dlg-title" class="modal-title">选择账号</h3>
                </div>
                <div class="modal-body">

                    <table id="table-acc" class="table table-striped table-bordered table-hover table-data no-footer dtr-inline"></table>
                    <div class="table-extend-area">
                        <div class="table-extend-cell checkbox-select-all"><input id="table-acc-select-all" type="checkbox"/></div>
                        <div class="table-extend-cell group-actions">
                            <div class="btn-group" role="group">
                                <button id="btn-add-to-group" type="button" class="btn btn-primary"><i class="fa fa-edit fa-fw"></i> 添加为组成员</button>
                            </div>
                        </div>
                        <div class="table-extend-cell table-item-counter">
                            <ol id="table-acc-paging"></ol>
                        </div>
                    </div>
                    <div class="table-extend-area">
                        <div class="table-extend-cell">
                            <div style="text-align:right;">
                                <nav>
                                    <ul id="table-acc-pagination" class="pagination"></ul>
                                </nav>
                            </div>
                        </div>
                    </div>

                </div>


                <div class="modal-footer">
                    <button type="button" class="btn btn-sm btn-default" data-dismiss="modal"><i class="fa fa-times fa-fw"></i> 关闭</button>
                </div>
            </div>
        </div>
    </div>
</%block>
