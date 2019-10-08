odoo.define('web.my_reference', function (require) {
    "use strict";

    var core = require('web.core');
    let _t = core._t;
    var data = require('web.data');
    var common = require('web.form_common');
    var Model = require('web.DataModel');
    var utils = require('web.utils');
    var FieldSelection = common.AbstractField.extend(common.ReinitializeFieldMixin, {
        template: 'FieldSelection',
        events: {
            'change': 'store_dom_value',
        },
        init: function (field_manager, node) {
            this._super(field_manager, node);
            this.set("value", false);
            this.set("values", []);
            this.records_orderer = new utils.DropMisordered();
            this.field_manager.on("view_content_has_changed", this, function () {
                var domain = new data.CompoundDomain(this.build_domain()).eval();
                if (!_.isEqual(domain, this.get("domain"))) {
                    this.set("domain", domain);
                }
            });
        },
        initialize_field: function () {
            common.ReinitializeFieldMixin.initialize_field.call(this);
            this.on("change:domain", this, this.query_values);
            this.set("domain", new data.CompoundDomain(this.build_domain()).eval());
            this.on("change:values", this, this.render_value);
        },
        query_values: function () {
            var self = this;
            var def;
            if (this.field.type === "many2one") {
                var model = new Model(this.field.relation);
                def = model.call("name_search", ['', this.get("domain")], {"context": this.build_context()});
            } else {
                var values = _.reject(this.field.selection, function (v) {
                    return v[0] === false && v[1] === '';
                });
                def = $.when(values);
            }
            this.records_orderer.add(def).then(function (values) {
                if (!_.isEqual(values, self.get("values"))) {
                    self.set("values", values);
                }
            });
        },
        initialize_content: function () {
            // Flag indicating whether we're in an event chain containing a change
            // event on the select, in order to know what to do on keyup[RETURN]:
            // * If the user presses [RETURN] as part of changing the value of a
            //   selection, we should just let the value change and not let the
            //   event broadcast further (e.g. to validating the current state of
            //   the form in editable list view, which would lead to saving the
            //   current row or switching to the next one)
            // * If the user presses [RETURN] with a select closed (side-effect:
            //   also if the user opened the select and pressed [RETURN] without
            //   changing the selected value), takes the action as validating the row
            if (!this.get('effective_readonly')) {
                var ischanging = false;
                this.$el
                    .change(function () {
                        ischanging = true;
                    })
                    .click(function () {
                        ischanging = false;
                    })
                    .keyup(function (e) {
                        if (e.which !== 13 || !ischanging) {
                            return;
                        }
                        e.stopPropagation();
                        ischanging = false;
                    });
                this.setupFocus(this.$el);
            }
        },
        commit_value: function () {
            this.store_dom_value();
            return this._super();
        },
        store_dom_value: function () {
            if (!this.get('effective_readonly')) {
                this.internal_set_value(JSON.parse(this.$el.val()));
            }
        },
        set_value: function (value_) {
            value_ = value_ === null ? false : value_;
            value_ = value_ instanceof Array ? value_[0] : value_;
            this._super(value_);
        },
        render_value: function () {
            var values = this.get("values");
            values = [[false, this.node.attrs.placeholder || '']].concat(values);
            var found = _.find(values, function (el) {
                return el[0] === this.get("value");
            }, this);
            if (!found) {
                found = [this.get("value"), _t('Unknown')];
                values = [found].concat(values);
            }
            if (!this.get("effective_readonly")) {
                this.$el.empty();
                for (var i = 0; i < values.length; i++) {
                    this.$el.append($('<option/>', {
                        value: JSON.stringify(values[i][0]),
                        html: values[i][1]
                    }))
                }
                this.$el.val(JSON.stringify(found[0]));
            } else {
                this.$el.text(found[1]);
            }
        },
        focus: function () {
            if (!this.get("effective_readonly")) {
                return this.$el.focus();
            }
            return false;
        },
    });


    var FieldReference = common.AbstractField.extend(common.ReinitializeFieldMixin, {
        className: 'o_row',
        init: function (field_manager, node) {
            this._super(field_manager, node);
            this.reference_ready = true;
        },
        destroy_content: function () {
            if (this.fm) {
                this.fm.destroy();
                this.fm = undefined;
            }
        },
        initialize_content: function () {
            var self = this;
            this.fm = new common.DefaultFieldManager(this);
            this.fm.extend_field_desc({
                "selection": {
                    selection: this.field_manager.get_field_desc(this.name).selection,
                    type: "selection",
                },
                "m2o": {
                    relation: null,
                    type: "many2one",
                },
            });
            this.selection = new FieldSelection(this.fm, {
                attrs: {
                    name: 'selection',
                    modifiers: JSON.stringify({readonly: this.get('effective_readonly')}),
                }
            });
            this.selection.on("change:value", this, this.on_selection_changed);
            this.selection.appendTo(this.$el);
            this.selection
                .on('focused', null, function () {
                    self.trigger('focused');
                })
                .on('blurred', null, function () {
                    self.trigger('blurred');
                });
            var FieldMany2One = core.form_widget_registry.get('many2one');
            this.m2o = new FieldMany2One(this.fm, {
                attrs: {
                    name: 'relation',
                    options: "{'no_create_edit':True}",
                    modifiers: JSON.stringify({readonly: this.get('effective_readonly')}),
                    context: this.build_context().eval(),
                }
            });
            this.m2o.on("change:value", this, this.data_changed);
            this.m2o.appendTo(this.$el);
            this.m2o
                .on('focused', null, function () {
                    self.trigger('focused');
                })
                .on('blurred', null, function () {
                    self.trigger('blurred');
                });
        },
        on_selection_changed: function () {
            if (this.reference_ready) {
                this.internal_set_value([this.selection.get_value(), false]);
                this.render_value();
            }
        },
        data_changed: function () {
            if (this.reference_ready) {
                this.internal_set_value([this.selection.get_value(), this.m2o.get_value()]);
            }
        },
        set_value: function (val) {
            if (val) {
                val = val.split(',');
                val[0] = val[0] || false;
                val[1] = val[0] ? (val[1] ? parseInt(val[1], 10) : val[1]) : false;
            }
            this._super(val || [false, false]);
        },
        get_value: function () {
            return this.get('value')[0] && this.get('value')[1] ? (this.get('value')[0] + ',' + this.get('value')[1]) : false;
        },
        render_value: function () {
            this.reference_ready = false;
            if (!this.get("effective_readonly")) {
                this.selection.set_value(this.get('value')[0]);
            }
            this.m2o.field.relation = this.get('value')[0];
            this.m2o.node.attrs.domain=this.node.attrs.domain
            this.m2o.set_value(this.get('value')[1]);
            this.m2o.do_toggle(!!this.get('value')[0]);
            this.reference_ready = true;
        },
        is_false: function () {
            return !this.get_value();
        },
    });


    core.form_widget_registry
        .add('my_selection', FieldSelection)
        .add('my_reference', FieldReference)
});
