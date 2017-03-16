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
            padding-bottom: 20px;
        }

        h1 {
            font-size: 200%;
        }

        h2 {
            font-size: 160%;
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
                <input id="db-mysql" type="radio" name="database" value="mysql" disabled="disabled"/> <label for="db-mysql">MySQL（开发中，暂不支持）</label>
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


<%block name="embed_js">
    <script type="text/javascript">
        "use strict";

        ywl.on_init = function (cb_stack, cb_args) {
            ywl.dom = {
                btn_create_db: $('#btn-create-db'),
            };

            ywl.dom.btn_create_db.click(function () {
                console.log('create-db-click');
                ywl.ajax_post_json('/maintenance/rpc', {cmd: 'create_db'},
                        function (ret) {
                            console.log('create-db:', ret);
                            if (ret.code == 0) {
                                ywl.get_task_ret(ret.data.task_id);
                            }

                        },
                        function () {
                            ywl.show_message('error', '无法连接到服务器！');
                        }
                );

            });

            ywl.get_task_ret = function (task_id) {
                ywl.ajax_post_json('/maintenance/rpc', {cmd: 'get_task_ret', 'tid': task_id},
                        function (ret) {
                            console.log('get_task_ret:', ret);
                            if (ret.code == 0) {

                            }

                        },
                        function () {
                            ywl.show_message('error', '无法连接到服务器！');
                        }
                );

            };

            cb_stack.exec();
        };
    </script>
</%block>
