# -*- coding: utf-8 -*-
import json

import requests

from odoo import models, api, fields
import logging
_logger = logging.getLogger(__name__)


class SearchAccountMoveState(models.TransientModel):
    _name = 'oa.interface.search.move.state'
    _description = u"查询凭证状态"

    @api.multi
    def search_move_state(self):
        """查询凭证状态"""
        logging.info(u"查询凭证过账状态")
        system_name = self.env['ir.values'].get_default('oa.financial.base.config', 'system_name')
        system_code = self.env['ir.values'].get_default('oa.financial.base.config', 'system_code')
        move_state_url = self.env['ir.values'].get_default('oa.financial.base.config', 'move_state')
        out_time = self.env['ir.values'].get_default('oa.financial.base.config', 'out_time')
        move_models = self.env['oa.interface.account.move.list'].sudo().search([('state', '=', 'y')])
        search_data = {
            "syatem_name": system_name if system_name else '',
            "syatem_code": system_code if system_code else '',
        }
        moves_list = list()
        for move_model in move_models:
            # 获取每个模型下已生成凭证的单据
            model_data = self.env[move_model.model_id.model].sudo().search([('submit_state', '!=', '03'), ('submit_state', '!=', '00')])
            for data in model_data:
                # 将获取的单据封装为查询json准备发往财务系统进行查询
                moves_list.append({
                    'company_code': data.company_id.code if data.company_id else '',
                    'form_number': data.code if data.code else '',
                    'form_model': move_model.model_id.model,
                })
        search_data.update({'moves': moves_list})
        # 发送数据至ERP系统
        try:
            logging.info(search_data)
            headers = {'Content-Type': 'application/json'}
            result = requests.post(url=move_state_url, headers=headers, data=json.dumps(search_data),
                                   timeout=out_time)
            result = json.loads(result.text)
            result = json.loads(result.get('result'))
            logging.info(u">>>查询结果代码:{}".format(result.get('state')))
            for res in result.get('results'):
                logging.info(res)
                # 获取单据对象
                form_move = self.env[res.get('form_model')].search([('code', '=', res.get('form_number'))])
                if form_move:
                    if res.get('move_state') == '01':
                        self.update_model_move_state(form_move[0]._name, '02', form_move[0].id)
                        form_move[0].sudo().message_post(body=u"自动查询凭证状态结果:'未过账'", message_type='notification')
                    elif res.get('move_state') == '02':
                        self.update_model_move_state(form_move[0]._name, '03', form_move[0].id)
                        form_move[0].sudo().message_post(body=u"自动查询凭证状态结果:'已过账'", message_type='notification')
                    # else:
                    #     msg = u"自动查询凭证状态结果为'未生成正式凭证'！"
                    #     form_move[0].sudo().message_post(body=msg, message_type='notification')
        except requests.exceptions.Timeout:
            logging.info(u'>>>查询数据超时: 当前等待时间为{}秒！'.format(out_time))
        except KeyError as e:
            logging.info(u">>>KeyError异常错误：{}".format(e.message))
        except Exception as e:
            logging.info(u'>>>查询失败！原因:{}'.format(e.message))

    @api.model
    def update_model_move_state(self, model_name, value, id):
        """更新模板的付款状态"""
        sql = """UPDATE {} SET submit_state = '{}' WHERE id = {}""".format(model_name.replace('.', '_'), value, id)
        self.env.cr.execute(sql)

