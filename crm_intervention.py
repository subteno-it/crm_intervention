# -*- coding: utf-8 -*-
##############################################################################
#
#    crm_intervention module for OpenERP, Managing intervention in CRM
#    Copyright (C) 2011 SYLEAM Info Services (<http://www.Syleam.fr/>)
#              Sebastien LANGE <sebastien.lange@syleam.fr>
#
#    This file is a part of crm_intervention
#
#    crm_intervention is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    crm_intervention is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.addons.base_status.base_state import base_state
from openerp.addons.base_status.base_stage import base_stage
from openerp.addons.crm import crm
from openerp.osv import orm
from openerp.osv import fields
from openerp.tools.translate import _
import time
import datetime
import openerp.tools as tools

CRM_INTERVENTION_STATES = (
    crm.AVAILABLE_STATES[2][0],  # Cancelled
    crm.AVAILABLE_STATES[3][0],  # Done
    crm.AVAILABLE_STATES[4][0],  # Pending
)


class crm_case_section(orm.Model):
    _inherit = 'crm.case.section'

    _columns = {
        'unit_hour_id': fields.many2one('product.uom', 'Hour unit',
                                        help='Select unit represent hour'),
        'unit_day_id': fields.many2one('product.uom', 'Day unit',
                                      help='Select unit represent days'),
    }


class crm_intervention(base_state, base_stage, orm.Model):
    _name = 'crm.intervention'
    _description = 'Intervention'
    _order = "date_planned_start desc"
    _inherit = ['mail.thread']

    def _get_default_section_intervention(self, cr, uid, context=None):
        """Gives default section for intervention section
        :param self: The object pointer
        :param cr: the current row, from the database cursor,
        :param uid: the current user’s ID for security checks,
        :param context: A standard dictionary for contextual values
        """
        mod, res_id = self.pool.get('ir.model.data').get_object_reference(
            cr, uid, 'crm_intervention', 'section_interventions_department')
        if res_id:
            return res_id
        return False

    def _get_default_email_cc(self, cr, uid, context=None):
        """Gives default email address for intervention section
        :param self: The object pointer
        :param cr: the current row, from the database cursor,
        :param uid: the current user’s ID for security checks,
        :param context: A standard dictionary for contextual values
        """
        mod, res_id = self.pool.get('ir.model.data').get_object_reference(
            cr, uid, 'crm_intervention', 'section_interventions_department')
        if res_id:
            return self.pool['crm.case.section'].browse(
                cr, uid, res_id, context=context).reply_to
        return False

    _columns = {
        'id': fields.integer('ID', readonly=True),
        'name': fields.char('Name', size=128, required=True),
        'active': fields.boolean('Active', required=False),
        'date_action_last': fields.datetime('Last Action', readonly=1),
        'date_action_next': fields.datetime('Next Action', readonly=1),
        'description': fields.text('Description'),
        'create_date': fields.datetime('Creation Date', readonly=True),
        'write_date': fields.datetime('Update Date', readonly=True),
        'user_id': fields.many2one('res.users', 'Responsible'),
        'section_id': fields.many2one(
            'crm.case.section', 'Interventions Team',
            help='Interventions team to which Case belongs to.'
            'Define Responsible user and Email account for mail gateway.'),
        'company_id': fields.many2one('res.company', 'Company'),
        'date_closed': fields.datetime('Closed', readonly=True),
        'email_cc': fields.text(
            'Watchers Emails', size=252,
            help="These email addresses will be added to the CC field of all "
            "inbound and outbound emails for this record before being sent. "
            "Separate multiple email addresses with a comma"),
        'email_from': fields.char(
            'Email', size=128, help="These people will receive email."),
        'ref': fields.reference(
            'Reference', selection=crm._links_get, size=128),
        'ref2': fields.reference(
            'Reference 2', selection=crm._links_get, size=128),
        'priority': fields.selection(crm.AVAILABLE_PRIORITIES, 'Priority'),
        'categ_id': fields.many2one(
            'crm.case.categ', 'Category',
            domain="[('section_id','=',section_id), "
            "('object_id.model', '=', 'crm.intervention')]"),
        'number_request': fields.char('Number Request', size=64),
        'customer_information': fields.text('Customer_information', ),
        'intervention_todo': fields.text(
            'Intervention to do',
            help="Indicate the description of this intervention to do", ),
        'date_planned_start': fields.datetime(
            'Planned Start Date',
            help="Indicate the date of begin intervention planned", ),
        'date_planned_end': fields.datetime(
            'Planned End Date',
            help="Indicate the date of end intervention planned", ),
        'date_effective_start': fields.datetime(
            'Effective start date',
            help="Indicate the date of begin intervention",),
        'date_effective_end': fields.datetime(
            'Effective end date',
            help="Indicate the date of end intervention",),
        'duration_planned': fields.float(
            'Planned duration',
            help='Indicate estimated to do the intervention.'),
        'duration_effective': fields.float(
            'Effective duration',
            help='Indicate real time to do the intervention.'),
        'alldays_planned': fields.boolean('All day planned', help='All-day intervention planned'),
        'alldays_effective': fields.boolean('All day effective', help='All-day intervention effective'),
        'partner_id': fields.many2one(
            'res.partner', 'Customer',
            change_default=True, select=True),
        'partner_invoice_id': fields.many2one(
            'res.partner', 'Invoice Address',
            help="The name and address for the invoice",),
        'partner_order_id': fields.many2one(
            'res.partner', 'Intervention Contact',
            help="The name and address of the contact that "
            "requested the intervention."),
        'partner_shipping_id': fields.many2one(
            'res.partner', 'Intervention Address'),
        'partner_address_phone': fields.char('Phone', size=64),
        'partner_address_mobile': fields.char('Mobile', size=64),
        'state': fields.selection(
            crm.AVAILABLE_STATES, 'State', size=16, readonly=True,
            help="The state is set to 'Draft', when a case is created."
            "\nIf the case is in progress the state is set to 'Open'."
            "\nWhen the case is over, the state is set to \'Done\'."
            "\nIf the case needs to be reviewed then the state is set to"
            "'Pending'."),
        'contract_id': fields.many2one('account.analytic.account', 'Contract',
                                       help='Select analytic account to generate line on this contract'),
        'analytic_line_id': fields.many2one('account.analytic.line', 'Analytic line',
                                            help='Analytic line'),
        'product_id': fields.many2one('product.product', 'Prestation',
                                      domain=[('type', '=', 'service')],
                                      help='Product service relate with this intervention'),
        'message_ids': fields.one2many(
            'mail.message', 'res_id', 'Messages',
            domain=[('model', '=', _name)]),
    }

    _defaults = {
        'partner_invoice_id': lambda self, cr, uid,
        context: context.get('partner_id', False) and
        self.pool.get('res.partner').address_get(
            cr, uid, [context['partner_id']], ['invoice'])['invoice'],
        'partner_order_id': lambda self, cr, uid,
        context: context.get('partner_id', False) and
        self.pool.get('res.partner').address_get(
            cr, uid, [context['partner_id']], ['contact'])['contact'],
        'partner_shipping_id': lambda self, cr, uid,
        context: context.get('partner_id', False) and
        self.pool.get('res.partner').address_get(
            cr, uid, [context['partner_id']], ['delivery'])['delivery'],
        'number_request': lambda obj, cr, uid,
        context: obj.pool.get('ir.sequence').get(cr, uid, 'intervention'),
        'active': 1,
        'user_id': lambda s, cr, uid, c: s._get_default_user(cr, uid, c),
        'email_cc': _get_default_email_cc,
        'state': 'draft',
        'section_id': _get_default_section_intervention,
        'company_id': lambda s, cr, uid,
        c: s.pool.get('res.company')._company_default_get(
            cr, uid, 'crm.helpdesk', context=c),
        'priority': lambda *a: crm.AVAILABLE_PRIORITIES[2][0],
        'alldays_planned': False,
        'alldays_effective': False,
    }

    def onchange_partner_intervention_id(self, cr, uid, ids, part):
        if not part:
            return {
                'value': {
                    'partner_invoice_id': False, 'partner_shipping_id': False,
                    'partner_order_id': False, 'email_from':
                    False, 'partner_address_phone': False,
                    'partner_address_mobile': False}}
        addr = self.pool.get('res.partner').address_get(
            cr, uid, [part], ['default', 'delivery', 'invoice', 'contact'])
        part = self.pool.get('res.partner').browse(cr, uid, part)
        val = {
            'partner_invoice_id': addr['invoice'],
            'partner_order_id': addr['contact'],
            'partner_shipping_id': addr['delivery'],
        }
        val['email_from'] = self.pool.get('res.partner').browse(
            cr, uid, addr['delivery']).email
        val['partner_address_phone'] = self.pool.get('res.partner').browse(
            cr, uid, addr['delivery']).phone
        val['partner_address_mobile'] = self.pool.get('res.partner').browse(
            cr, uid, addr['delivery']).mobile
        return {'value': val}

    def onchange_planned_duration(self, cr, uid, ids, planned_duration,
                                  planned_start_date):
        if not planned_duration:
            return {'value': {'date_planned_end': False}}
        start_date = datetime.datetime.fromtimestamp(
            time.mktime(time.strptime(
                planned_start_date, "%Y-%m-%d %H:%M:%S")))
        return {'value': {
            'date_planned_end': (start_date + datetime.timedelta(
                hours=planned_duration)).strftime('%Y-%m-%d %H:%M:%S')}}

    def onchange_planned_end_date(self, cr, uid, ids, planned_end_date,
                                  planned_start_date):
        start_date = datetime.datetime.fromtimestamp(time.mktime(
            time.strptime(planned_start_date, "%Y-%m-%d %H:%M:%S")))
        end_date = datetime.datetime.fromtimestamp(time.mktime(
            time.strptime(planned_end_date, "%Y-%m-%d %H:%M:%S")))
        difference = end_date - start_date
        minutes, secondes = divmod(difference.seconds, 60)
        hours, minutes = divmod(minutes, 60)
        return {'value': {
            'duration_planned': (float(difference.days * 24) +
                                 float(hours) + float(minutes) / float(60))}}

    def onchange_effective_duration(self, cr, uid, ids, effective_duration,
                                    effective_start_date):
        if not effective_duration:
            return {'value': {'date_effective_end': False}}
        start_date = datetime.datetime.fromtimestamp(time.mktime(
            time.strptime(effective_start_date, "%Y-%m-%d %H:%M:%S")))
        return {'value': {
            'date_effective_end': (start_date + datetime.timedelta(
                hours=effective_duration)).strftime('%Y-%m-%d %H:%M:00')}}

    def onchange_effective_end_date(self, cr, uid, ids, effective_end_date,
                                    effective_start_date):
        start_date = datetime.datetime.fromtimestamp(time.mktime(
            time.strptime(effective_start_date, "%Y-%m-%d %H:%M:%S")))
        end_date = datetime.datetime.fromtimestamp(time.mktime(
            time.strptime(effective_end_date, "%Y-%m-%d %H:%M:%S")))
        difference = end_date - start_date
        minutes, secondes = divmod(difference.seconds, 60)
        hours, minutes = divmod(minutes, 60)
        return {'value': {
            'duration_effective': (float(difference.days * 24) +
                                   float(hours) + float(minutes) / float(60))}}

    def action_email_send(self, cr, uid, ids, context=None):
        """
        Send email from the form
        """
        assert len(ids) == 1, 'This option should only be used for a single id at a time.'
        ir_model_data = self.pool.get('ir.model.data')
        try:
            template_id = ir_model_data.get_object_reference(cr, uid, 'crm_intervention',
                                                             'email_template_intervention')[1]
        except ValueError:
            template_id = False

        try:
            compose_form_id = ir_model_data.get_object_reference(cr, uid, 'mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False

        ctx = dict(context)
        ctx.update({
            'default_model': 'crm.intervention',
            'default_res_id': ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'mark_so_as_sent': False
        })
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }

    def message_new(self, cr, uid, msg, custom_values=None, context=None):
        """ Override to updates the document according to the email. """
        if custom_values is None: custom_values = {}

        vals = {
            'name': msg.get('subject'),
            'email_from': msg.get('from'),
            'email_cc': msg.get('cc'),
            'description': msg.get('body'),
            'user_id': False,
        }
        if msg.get('priority', False):
            vals['priority'] = msg.get('priority')

        vals.update(custom_values)
        return super(crm_intervention, self).message_new(cr, uid, msg, custom_values=vals, context=context)

    def message_update(self, cr, uid, ids, vals={}, msg="",
                       default_act='pending', context=None):
        """
        :param self: The object pointer
        :param cr: the current row, from the database cursor,
        :param uid: the current user’s ID for security checks,
        :param ids: List of update mail’s IDs
        """
        if isinstance(ids, (str, int, long)):
            ids = [ids]

        if msg.get('priority') in dict(crm.AVAILABLE_PRIORITIES):
            vals['priority'] = msg.get('priority')

        maps = {
            'cost': 'planned_cost',
            'revenue': 'planned_revenue',
            'probability': 'probability'
        }
        vls = {}
        for line in msg['body'].split('\n'):
            line = line.strip()
            res = tools.misc.command_re.match(line)
            if res and maps.get(res.group(1).lower()):
                key = maps.get(res.group(1).lower())
                vls[key] = res.group(2).lower()
        vals.update(vls)

        # Unfortunately the API is based on lists
        # but we want to update the state based on the
        # previous state, so we have to loop:
        for case in self.browse(cr, uid, ids, context=context):
            values = dict(vals)
            if case.state in CRM_INTERVENTION_STATES:
                values.update(state=crm.AVAILABLE_STATES[1][0])  # re-open
            res = self.write(cr, uid, [case.id], values, context=context)
        return res

    def copy(self, cr, uid, id, default=None, context=None):
        """
        #TODO make doc string
        Comment this
        """
        if context is None:
            context = {}

        if default is None:
            default = {}

        default['number_request'] = self.pool.get('ir.sequence').get(
            cr, uid, 'intervention')
        default['date_effective_start'] = False
        default['date_effective_end'] = False
        default['duration_effective'] = 0.0
        default['categ_id'] = False
        default['description'] = False
        default['timesheet_ids'] = False

        return super(crm_intervention, self).copy(
            cr, uid, id, default, context=context)

    def generate_analytic_line(self, cr, uid, ids, context=None):
        """
        Generate an analytic line in the contract specified, base on product
        """
        for inter in self.browse(cr, uid, ids, context=context):
            if inter.analytic_line_id:
                raise orm.except_orm(_('Error'), _('This intervention already pre-invoiced'))
            if not inter.product_id:
                raise orm.except_orm(_('Error'), _('Product to invoice is necessary'))
            if not inter.contract_id:
                raise orm.except_orm(_('Error'), _('Contract is necessary'))
            if inter.product_id.standard_price < 0.1:
                raise orm.except_orm(_('Error'),
                                     _('Please define a cost price for the product %s') % inter.product_id.name)

            # Find the analytic journal from the employe
            emp_obj = self.pool['hr.employee']
            emp_ids = emp_obj.search(cr, uid, [('user_id', '=', uid)], context=context)
            if not emp_ids:
                raise orm.except_orm(_('Error'), _('Employee not found'))

            emp = emp_obj.browse(cr, uid, emp_ids[0], context=context)

            if inter.alldays_effective:
                q = self.pool['product.uom']._compute_price(
                    cr, uid, inter.product_id.uom_id.id, inter.product_id.standard_price,
                    inter.section_id.unit_day_id.id)
                amount = q * -1
                unit_amount = 1.0
                unit = inter.section_id.unit_day_id.id
            else:
                q = self.pool['product.uom']._compute_price(
                    cr, uid, inter.product_id.uom_id.id, inter.product_id.standard_price,
                    inter.section_id.unit_hour_id.id)
                amount = (q * inter.duration_effective) * -1
                unit_amount = inter.duration_effective
                unit = inter.section_id.unit_hour_id.id

            vals = {
                'name': _('BI Num %s') % inter.number_request,
                'account_id': inter.contract_id.id,
                'journal_id': emp.journal_id.id,
                'user_id': inter.user_id.id,
                'date': inter.date_effective_start[:10],
                'ref': inter.name[:64],
                'to_invoice': inter.contract_id.to_invoice.id,
                'product_id': inter.product_id.id,
                'unit_amount': unit_amount,
                'product_uom_id': unit,
                'amount': amount,
                'general_account_id': inter.product_id.property_account_income.id,
            }

            line_id = self.pool['account.analytic.line'].create(cr, uid, vals, context=context)
            inter.write({'analytic_line_id': line_id, 'state': 'done'}, context=context)

        return True

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
