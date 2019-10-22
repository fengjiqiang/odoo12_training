odoo.define('treeview', function (require) {
    "use strict";
    var core = require('web.core');
    var ajax = require('web.ajax');
    var ListController = require('web.ListController');
    var ListRenderer = require('web.ListRenderer');
    var FormController = require('web.FormController');
    var FormRenderer = require('web.FormRenderer');
    var KanbanController = require('web.KanbanController');
    var KanbanRenderer = require('web.KanbanRenderer');
    var qweb = core.qweb;

    var controller;
    var renderer;

    var treeObj;
    var node_id_selected = 0;
    var treejson = [];
    var last_view_type;

    ListController.include({
        renderPager: function () {
            controller = this;
            return this._super.apply(this, arguments);
        }
    });

    ListRenderer.include({
        _renderView: function () {
            renderer = this;
            var result = this._super.apply(this, arguments);
            if (this.arch.attrs.categ_property && this.arch.attrs.categ_model) {
                // 给list添加class，添加样式为相对布局
                this.getParent().$('.table-responsive').addClass('o_list_view_width_withcateg');
                // 修改responsive的样式
                this.getParent().$('.table-responsive').css("width", 'auto');
                this.getParent().$('.table-responsive').css("overflow-x", "auto");
                // 创建树
                buildTree();
            } else {
                this.getParent().$('.o_list_view_categ').remove();
            }
            return result;
        },

        // 行点击
        _onRowClicked: function (event) {
            if (!$(event.target).prop('special_click')) {
                var id = $(event.currentTarget).data('id');
                if (id) {
                    this.trigger_up('open_record', {id: id, target: event.current});
                }
            }
        },
    });

    KanbanController.include({
        renderPager: function () {
            controller = this;
            return this._super.apply(this, arguments);
        }
    });

    KanbanRenderer.include({
        _renderView: function () {
            renderer = this;
            var result = this._super.apply(this, arguments);
            if (this.arch.attrs.categ_property && this.arch.attrs.categ_model) {
                buildTree();
            } else {
                this.getParent().$('.o_list_view_categ').remove();
            }
            return result;
        }
    });

    FormController.include({
        renderPager: function () {
            controller = this;
            return this._super.apply(this, arguments);
        }
    });

    FormRenderer.include({
        _renderView: function () {
            var result = this._super.apply(this, arguments);
            renderer = this;
            if (this.arch.attrs.categ_property && this.arch.attrs.categ_model) {
                this.getParent().$('.o_form_view').addClass("o_list_view_width_withcateg");
                this.getParent().$('.o_form_view').css("width", 'auto');
                this.getParent().$('.o_form_view').css("overflow-x", "auto");
                buildTree();
            } else {
                this.getParent().$('.o_list_view_categ').remove();
            }
            return result;
        }
    });

    var buildTree = function () {
        // 模块名称
        var categ_model = renderer.arch.attrs.categ_model;

        // domain的 key值
        var categ_property = renderer.arch.attrs.categ_property;

        // 父节点对应的key
        var categ_parent_key = renderer.arch.attrs.categ_parent_key;

        // 根节点的key
        var categ_root_key = renderer.arch.attrs.categ_root_key;

        var setting = {
            view: {
                showLine: true,
                showIcon: false,
                selectedMulti: false,
                dblClickExpand: false,
            },
            data: {
                simpleData: {
                    enable: true,
                }
            },
            edit: {
                enable: false,
                editNameSelectAll: true,
            },
            callback: {
                onClick: function (event, treeId, treeNode) {
                    node_id_selected = treeNode.id;
                    var search_view = controller.searchView;
                    var search_data = search_view.build_search_data();
                    var domains = search_data.domains;
                    if (categ_property && categ_model) {
                        if (node_id_selected != null && node_id_selected > 0) {
                            var include_children = renderer.getParent().$('#include_children').get(0).checked;
                            var oparetion = include_children ? 'child_of' : '=';
                            domains[domains.length] = [[categ_property, oparetion, node_id_selected]];
                        }
                    }
                    search_view.trigger_up('search', search_data);
                },
                beforeRemove: zTreeBeforeRemove,
                onRemove: zTreeOnRemove,
                beforeRename: zTreeBeforeRename
            },
        };

        // 添加增加按钮
        var newCount = 1;

        // 添加增加按钮
        function addHoverDom(treeId, treeNode) {
            var sObj = $("#" + treeNode.tId + "_span");
            if (treeNode.editNameFlag || $("#" + treeNode.tId + "_add").length > 0) return;
            var addStr = "<span class='button add' id='" + treeNode.tId + "_add"
                + "' title='add' onfocus='this.blur()'/>";
            sObj.after(addStr);
            var btn = $("#" + treeNode.tId + "_add");
            if (btn) btn.bind("click", function () {
                // 静态增加节点
                var zTree = $.fn.zTree.getZTreeObj(treeId);
                zTree.addNodes(treeNode, {id: (100 + newCount), pId: treeNode.id, name: "new node" + (newCount++)});
                return false;
            });
        }

        // 取消增加按钮
        function removeHoverDom(treeId, treeNode) {
            $("#" + treeNode.tId + "_add").unbind().remove();
        }

        // 设置删除按钮
        function setRemoveBtn(treeId, treeNode) {
            return !treeNode.isParent;
        }

        // 删除前校验
        function zTreeBeforeRemove(treeId, treeNode) {
            var zTree = $.fn.zTree.getZTreeObj(treeId);
            zTree.selectNode(treeNode);
            return confirm("确认删除 节点 -- " + treeNode.name + " 吗？");
        }

        // 删除节点 RPC
        function zTreeOnRemove(e, treeId, treeNode) {
            // showLog("[ "+getTime()+" onRemove ]&nbsp;&nbsp;&nbsp;&nbsp; " + treeNode.name);
        }

        function zTreeBeforeRename(treeId, treeNode, newName, isCancel) {
            console.log('treeId,treeNode, newName, isCancel', treeId, treeNode, newName, isCancel);
            // return newName.length > 5;
        }

        var fields = ['id', 'name'];
        if (categ_parent_key !== null) {
            fields.push(categ_parent_key);
        }

        var ctx = renderer.state.getContext();
        ajax.jsonRpc('/web/dataset/call_kw', 'call', {
            model: categ_model,
            method: 'search_read',
            args: [],
            kwargs: {
                domain: [],
                fields: fields,
                order: 'id asc',
                context: ctx
            }
        }).then(function (res) {
            if (res.length > 0) {
                // 组织tree数据格式
                var treejson_cur = [];
                for (var index = 0; index < res.length; index++) {
                    var obj = res[index];
                    var parent_id = 0;
                    if (obj.hasOwnProperty(categ_parent_key)) {
                        parent_id = obj[categ_parent_key];
                        if (parent_id) {
                            parent_id = parent_id[0];
                        }
                    }
                    treejson_cur.push({id: obj['id'], pId: parent_id, name: obj['name'], open: true});
                }

                if (renderer.getParent().$('.o_list_view_categ').length === 0
                    || last_view_type !== renderer.viewType
                    || (JSON.stringify(treejson) !== JSON.stringify(treejson_cur))) {
                    last_view_type = renderer.viewType;
                    renderer.getParent().$('.o_list_view_categ').remove();
                    treejson = treejson_cur;
                    var fragment = document.createDocumentFragment();
                    var content = qweb.render('Treeview');
                    // 在tree的结尾加入视图
                    $(content).appendTo(fragment);
                    renderer.getParent().$el.prepend(fragment);
                    // 初始化 Ztree
                    treeObj = $.fn.zTree.init(renderer.getParent().$('.ztree'), setting, treejson);

                    //显示指定子节点数据
                    if (categ_root_key && categ_root_key !== null) {
                        var zTreeMenu = $.fn.zTree.getZTreeObj("ztree");
                        var nodes = zTreeMenu.getNodesByParam("id", categ_root_key, null);
                        if (nodes.isParent) {
                            nodes[0].children.push({
                                id: nodes[0].id, pId: nodes[0].pId, name: nodes[0].name, open: true
                            });
                            treeObj = $.fn.zTree.init(renderer.getParent().$('.ztree'), setting, nodes[0].children);
                        } else {
                            treeObj = $.fn.zTree.init(renderer.getParent().$('.ztree'), setting, nodes[0]);
                        }
                    }

                    // 折叠树状图
                    renderer.getParent().$(".handle_menu_arrow").on('click', function (e) {
                        if (renderer.getParent().$('.handle_menu_arrow').hasClass("handle_menu_arrow_left")) {
                            renderer.getParent().$('.odtree_control_panel').css("display", "none");
                            renderer.getParent().$('.o_list_view_categ').css("border-right", "0px");
                            renderer.getParent().$('.handle_menu_arrow').removeClass("handle_menu_arrow_left");
                            renderer.getParent().$('.handle_menu_arrow').addClass("handle_menu_arrow_right");
                            renderer.getParent().$('.ztree').css("display", "none");
                            renderer.getParent().$('.o_list_view_categ').addClass('o_list_view_categ_hidden');
                        } else {
                            renderer.getParent().$('.o_list_view_categ').css({"border-right": "1px solid #b9b9b9"});
                            renderer.getParent().$('.handle_menu_arrow').removeClass("handle_menu_arrow_right");
                            renderer.getParent().$('.handle_menu_arrow').addClass("handle_menu_arrow_left");
                            renderer.getParent().$('.ztree').css("display", "block");
                            renderer.getParent().$('.o_list_view_categ').removeClass('o_list_view_categ_hidden');
                        }
                    });
                    renderer.getParent().$(".o_list_view_categ").resizable({
                        handles: 'e, s',
                        minWidth: 200,
                        maxWidth: 1500,
                    });
                }
                // 获取选中节点
                if (node_id_selected != null && node_id_selected > 0) {
                    var node = treeObj.getNodeByParam('id', node_id_selected, null);
                    treeObj.selectNode(node);
                }
            }
        });
    };
});
