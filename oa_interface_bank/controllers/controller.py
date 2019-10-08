# -*- coding: utf-8 -*-
import datetime
import json
import logging
from odoo.http import Controller, route, request

logger = logging.getLogger(__name__)
import sys

reload(sys)
sys.setdefaultencoding('utf-8')


class OaInterfaceController(Controller):
    """
    OA向外部提供的接口
    包括修改付款单的单据状态
    """

    @route('/oa/interface/payment/update/state', type='json', auth='none', methods=['get', 'post'], csrf=False)
    def oa_interface_payment_update_state(self):
        """
        本接口用于外部系统调用时根据传递的单据编号修改付款单的状态
        数据传递格式：json
        json_data = {
            "source_number": "单据编号",
            "state": "单据状态",
            "paied_money": "已付款金额",
        }
        返回数据格式：
        {"code": 返回编号， "message": "消息"}
        :return:
        """
        logging.info(u"-----检测到外部系统正在请求修改付款单状态-----")
        json_str = request.jsonrequest
        if not json_str:
            return json.dumps({"state": '1001', "message": u"未接收到任何JSON数据"}, ensure_ascii=False)
        try:
            # source_code = json_str['source_code']
            # payment_state = json_str['payment_state']
            source_number = json_str['source_number']
            state = json_str['state']
            paied_money = json_str['paied_money']
        except KeyError:
            return json.dumps(({"state": '1001', "message": u"没有正确传递参数"}), ensure_ascii=False)
        except Exception as e:
            msg = u"Exception:'{}'".format(e.message)
            return json.dumps(({"state": '1002', "message": msg}), ensure_ascii=False)
        # payment = request.env['oa.interface.bank'].sudo().search([('source_number', '=', source_code)], limit=1)
        # if not payment:
        #     return json.dumps({"state": '1001', "message": u"没有找到编号{}的付款单".format(source_code)}, ensure_ascii=False)
        # payment.sudo().write({'state': payment_state})
        payment = request.env['oa.interface.bank'].sudo().search([('source_number', '=', source_number)], limit=1)
        if not payment:
            return json.dumps({"state": '1003', "message": u"没有找到编号{}的付款单".format(source_number)}, ensure_ascii=False)
        # 如果全部支付完，则将OA付款单状态更新为02交易成功
        # 每一次支付成功后，反写OA付款单的“已付款金额”字段
        # 每一次操作以后，反写OA付款单的每条明细的状态
        # @author: fengjiqiang@inspur.com
        if "payment_state" in json_str:
            payment.write({'state': '02'})
        payment.write({"paied_money": paied_money})
        for line in range(len(state)):
            payment.payment_line_ids[line].write({'state': state[line]})
        return json.dumps({"code": '0000', "message": u"执行成功！"})












    # @route('/interface/bank/create/payment', type='json', auth='none', methods=['get', 'post'], csrf=False)
    # def bank_create_payment(self):
    #     """
    #     外部系统传递付款单至erp系统外部接口；数据格式为json
    #     json格式为：   (payments部分支持多条记录传递， 可为dict或list)
    #     json_data = {
    #     "system_name": "接入系统名称",
    #     "system_code": "接入系统代码",
    #     "create_date": "上传日期yyyy-MM-dd<",
    #     "create_time": "上传时间HH:mm:ss",
    #     "payments": [
    #         {
    #         "source_number":"付款单据编号",
    #         "source_model":"单据模型",
    #         "company_code":"公司编码",
    #         "public_signs":"公私标识",
    #         "payment_model":"付款模式",
    #         "cross_row_identi":"跨行标识",
    #         "off_site_identi":"异地标识",
    #         "payee_identi":"收款方标识",
    #         "debit_identi":"借贷标识",
    #         "payee_bank":"收款方归属银行名称",
    #         "payee_bank_code":"收款方归属银行代码",
    #         "payee_opening_bank":"收款方开户行名称",
    #         "payee_opening_bank_code":"收款方开户行代码",
    #         "payee_opening_province":"收款方省份名称",
    #         "payee_opening_province":"收款方省份名称",
    #         "abc_provincial_code":"收款方省份代码（农行",
    #         "payee_opening_city":"收款方城市名称",
    #         "payee_opening_city_code":"收款方城市代码",
    #         "abc_city_code":"收款方城市代码（农行）",
    #         "currency_type":"币种",
    #         "partner_id":"收款户名",
    #         "partner_bank_number":"收款账号",
    #         "partner_number":"客户编号",
    #         "partner_contact":"收款联系人",
    #         "partner_contact_phone":"联系人电话",
    #         "partner_contact_add":"联系人地址",
    #         "pay_money":"付款金额",
    #         "pay_summary":"摘要",
    #         "pay_use":"付款用途",
    #         }
    #     ]
    #     }
    #     :return: {"state": "状态码", "message":"状态消息"}
    #     """
    #     # 检查配置项是否允许传递
    #     logging.info(u"外部系统正在传递银行付款单...")
    #     open_interface = request.env['ir.values'].get_default('interface.bank.settings', 'open_interface')
    #     if open_interface != 'y':
    #         return json.dumps(self.create_result_json_data(state='1010', message=u"财务ERP系统已设置不允许上传付款单据"),
    #                           ensure_ascii=False)
    #     json_str = request.jsonrequest
    #     if not json_str:
    #         return json.dumps(self.create_result_json_data(state='1001', message=u"未接收到任何JSON数据"), ensure_ascii=False)
    #     try:
    #         logging.info("interface/bank/create/payment-json:{}".format(json_str))
    #         # 获取传入日期和时间
    #         datetime.datetime.strptime(json_str.get('create_time'), '%H:%M:%S')
    #         datetime.datetime.strptime(json_str.get('create_date'), '%Y-%m-%d')
    #         # 检查单据是否重复
    #         logging.info(u"检查单据是否重复..")
    #         result = self.check_is_redundant(json_str['payments'])
    #         if not result['state']:
    #             return json.dumps(self.create_result_json_data(state='1002', message=result['message']),
    #                               ensure_ascii=False)
    #         # 检查单据字段是否正确
    #         logging.info(u"检查单据字段是否正确..")
    #         result = self.check_form_values(json_str['payments'])
    #         if not result['state']:
    #             return json.dumps(self.create_result_json_data(state='1003', message=result['message']),
    #                               ensure_ascii=False)
    #         # 写入付款单
    #         logging.info(u"写入付款单..")
    #         payment_len = self.create_payment_by_data(json_str)
    #         msg = u"ERP已接受'{}'条记录".format(payment_len)
    #         return json.dumps(self.create_result_json_data(state='0000', message=msg), ensure_ascii=False)
    #     except KeyError as e:
    #         msg = u"KeyError:字段'{}'不存在!".format(e.message)
    #         logging.info(msg)
    #         return json.dumps(self.create_result_json_data(state='1012', message=msg), ensure_ascii=False)
    #     except ValueError as e:
    #         msg = u"ValueError:'{}'".format(e.message)
    #         logging.info(msg)
    #         return json.dumps(self.create_result_json_data(state='1013', message=msg), ensure_ascii=False)
    #     except Exception as e:
    #         msg = u"Exception:'{}'".format(e.message)
    #         logging.info(msg)
    #         return json.dumps(self.create_result_json_data(state='999', message=msg), ensure_ascii=False)


