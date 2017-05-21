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

        .steps-detail {
            display: none;
            margin: 10px;
            padding: 10px;
            border: 1px solid #b4b4b4;
            background-color: #dcdcdc;
        }

        .steps-detail p {
            padding-left: 5px;
            margin: 2px 0 2px 1px;
        }

        .steps-detail p.error {
            color: #ffffff;
            margin: 2px 0 2px 0;
            background-color: #cc3632;
            border: 1px solid #9c2a26;
        }

        #sqlite-info, #mysql-info {
            display: none;
        }
    </style>
</%block>

## Begin Main Body.

<div class="page-content">

    <div class="content_box">
        <div class="container">

            <h1>配置TELEPORT服务</h1>
            <hr/>

            <h2>第一步：创建数据表</h2>
            <div>
                <p>请选择要使用的数据库类型（暂时仅支持sqlite，其它类型开发中）：</p>
                <input id="db-sqlite" type="radio" checked="checked" name="database" value="sqlite"/> <label for="db-sqlite">SQLite</label><br/>
                <input id="db-mysql" type="radio" name="database" value="mysql"/> <label for="db-mysql">MySQL（开发中，暂不支持）</label>
                <div id="sqlite-info"></div>
                <div id="mysql-info"></div>
                <div>
                    <button id="btn-create-db" type="button" class="btn btn-primary"><i class="fa fa-wrench fa-fw"></i> 开始创建</button>
                </div>

                <div id="steps-detail" class="steps-detail"></div>
            </div>

            <div id="step2" style="display:none;">
                <hr/>
                <h2>已完成！</h2>
                <p>是的，没有第二步了，安装配置已经完成了！刷新页面即可进入Teleport主界面啦~~</p>
            </div>

        </div>
    </div>

</div>


<%block name="embed_js">
    <script type="text/javascript">
        "use strict";
        ywl.add_page_options(${ page_param });

        ywl.on_init = function (cb_stack, cb_args) {
            ywl.dom = {
                btn_create_db: $('#btn-create-db'),
                steps_detail: $('#steps-detail'),
                sqlite_info: $('#sqlite-info'),
                mysql_info: $('#mysql-info')
            };

            if (ywl.page_options.db.type === DB_TYPE_SQLITE) {
            } else if (ywl.page_options.db.type === DB_TYPE_MYSQL) {
            } else {
                ywl.show_message('error', '未知的数据库类型，请检查您的配置文件！');
                ywl.dom.btn_create_db.attr('disabled', 'disabled').hide();
            }

            ywl.dom.btn_create_db.click(function () {

                ywl.dom.btn_create_db.attr('disabled', 'disabled').hide();
                ywl.dom.steps_detail.show();

                console.log('create-db-click');
                ywl.ajax_post_json('/maintenance/rpc', {cmd: 'create_db'},
                        function (ret) {
                            console.log('create-db:', ret);
                            if (ret.code === TPE_OK) {

                                var cb_stack = CALLBACK_STACK.create();
                                cb_stack
                                        .add(ywl.get_task_ret, {task_id: ret.data.task_id})
                                        .add(ywl.delay_exec, {delay_ms: 500})
                                        .exec();
                            }

                        },
                        function () {
                            ywl.show_message('error', '无法连接到服务器！');
                        }
                );

            });

            ywl.get_task_ret = function (cb_stack, cb_args) {
                var task_id = cb_args.task_id || 0;
                if (task_id === 0) {
                    console.log('task-id', task_id);
                    return;
                }

                ywl.ajax_post_json('/maintenance/rpc', {cmd: 'get_task_ret', 'tid': task_id},
                        function (ret) {
                            console.log('get_task_ret:', ret);
                            if (ret.code === TPE_OK) {

                                // show step progress.
                                var steps = ret.data.steps;
                                ywl.dom.steps_detail.empty();

                                var html = [];
                                var icon_class = '';
                                var err_class = '';
                                for (var i = 0; i < steps.length; ++i) {
                                    if (steps[i].stat === 0)
                                        icon_class = 'fa-check';
                                    else
                                        icon_class = 'fa-cog fa-spin';

                                    if (steps[i].code !== 0) {
                                        icon_class = 'fa-exclamation-circle';
                                        err_class = ' class="error"';
                                        steps[i].msg += ' 失败！'
                                    }
                                    else {
                                        err_class = '';
                                    }

                                    html.push('<p');
                                    html.push(err_class);
                                    html.push('><i class="fa ');
                                    html.push(icon_class);
                                    html.push('"></i> ');
                                    html.push(steps[i].msg);
                                    html.push('</p>')
                                }
                                ywl.dom.steps_detail.html(html.join(''));


                                if (!ret.data.running) {
                                    $('#step2').show('fast');
                                    return;
                                }

                                cb_stack
                                        .add(ywl.get_task_ret, {task_id: task_id})
                                        .add(ywl.delay_exec, {delay_ms: 500})
                                        .exec();
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
