# -*- coding: utf-8 -*-

from openerp.osv import orm
from openerp.osv import fields
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp


class ResPartner(orm.Model):
    _inherit = 'res.partner'

    _columns = {
        'inter_location_id': fields.many2one(
            'stock.location', 'Intervention location',
            help='Dedicate stock for the repairer'),
    }


class CrmIntervention(orm.Model):
    _inherit = 'crm.intervention'

    _columns = {
        'site_id': fields.many2one(
            'intervention.site', 'Site',
            help='Site to made this intervention'),
        'equipment_id': fields.many2one('intervention.equipment', 'Equipment', help='Help note'),
        'line_ids': fields.one2many('intervention.line', 'inter_id', 'Lines'),
        'src_location_id': fields.many2one(
            'stock.location', 'Location',
            help='Location where the products have been consumed'),
    }

    def onchange_user_id(self, cr, uid, ids, user):
        """
        When user change, we retrieve the mobile location
        """
        res = {'value':{}}
        if not user:
            res['value'].update({
                'src_location_id': False,
            })
        else:
            usr = self.pool['res.users'].browse(cr, uid, user)
            res['value'].update({
                'src_location_id': usr.inter_location_id and \
                    usr.inter_location_id.id or False,
            })

        return res

    def onchange_partner_intervention_id(self, cr, uid, ids, part):
        """
        If one site on the customer, we fill it automatically
        """
        res = super(CrmIntervention, self).onchange_partner_intervention_id(
            cr, uid, ids, part=part)
        if not part:
            res['value'].update({
                'site_id': False,
                'equipment_id': False,
            })
            if 'domain' not in res:
                res['domain'] = {}
            res['domain'].update({
                'site_id': [],
                'equipment_id': [],
            })

        s_args = [
            ('partner_id', '=', res['value']['partner_order_id'])
        ]
        s_ids = self.pool['intervention.site'].search(cr, uid, s_args)
        if len(s_ids) == 1:
            res['value']['site_id'] = s_ids[0]

        return res

    def onchange_site_id(self, cr, uid, ids, site_id, partner_id, context=None):
        """
        If site have an address, we replace the intervention address with
        site address
        """
        vals = {}
        domain = {
            'site_id': "[]",
            'equipment_id': "[]",
        }
        if not site_id:
            if partner_id:
                domain['site_id'] = "[('customer_id','=', %s)]" % partner_id
            return {'value': vals, 'domain': domain}

        site = self.pool['intervention.site'].browse(cr, uid, site_id, context=context)
        if site.partner_id:
            vals['partner_shipping_id'] = site.partner_id.id
        if site.contract_id:
            vals['contract_id'] = site.contract_id.id
        if site.user_id:
            vals['user_id'] = site.user_id.id

        if not partner_id and site.customer_id:
            vals['partner_id'] = site.customer_id.id or False
            domain['site_id'] = "[('customer_id','=', %s)]" % site.customer_id.id
            domain['equipment_id'] = "[('site_id','=', %s)]" % site.id

        return {'value': vals, 'domain': domain}

    def onchange_equipment_id(self, cr, uid, ids, equip_id, context=None):
        """
        If equipment have dedicate repairer, we retrieve it
        """
        vals = {}
        if not equip_id:
            return {}
        equip = self.pool['intervention.equipment'].browse(cr, uid, equip_id, context=context)
        if equip.user_id:
            vals['user_id'] = equip.user_id.id
        if equip.contract_id:
            vals['contract_id'] = equip.contract_id.id
        if equip.out_of_contract:
            vals['contract_id'] = False
        return {'value': vals}

    def create_output_move(self, cr, uid, ids, context=None):
        """
        Create moves based on lines entries
        """
        move_obj = self.pool['stock.move']
        for inter in self.browse(cr, uid, ids, context=context):
            if not inter.src_location_id:
                raise orm.except_orm(
                    _('Error'),
                    _('Missing location to made output movement'))
            for l in inter.line_ids:
                if not l.move_id and l.product_id.type != 'service':
                    m_args = {
                        'origin': inter.number_request,
                        'name': inter.number_request + '/' + l.product_id.name,
                        'product_id': l.product_id.id,
                        'product_qty': l.product_qty,
                        'product_uom': l.product_uom_id.id,
                        'state': 'draft',
                        'location_id': l.src_location_id and l.src_location_id.id or inter.src_location_id.id,
                        'location_dest_id': inter.partner_shipping_id.property_stock_customer.id,
                    }
                    if l.product_id.track_outgoing and not l.prodlot_id:
                        raise orm.except_orm(
                            _('Error'),
                            _('Lot is necessary for product "%s"') % l.product_id.name)
                    if l.prodlot_id:
                        m_args['prodlot_id'] = l.prodlot_id.id
                    mv_id = move_obj.create(cr, uid, m_args, context=context)
                    move_obj.action_done(cr, uid, [mv_id], context=context)
                    l.write({'move_id': mv_id})

        return True

    def _prepare_invoice_line(self, cr, uid, inter, lines, inv, context=None):
        """
        Add lines of products and servcies to invoice
        """
        res = super(CrmIntervention, self)._prepare_invoice_line(cr, uid, inter, lines, inv, context=context)
        line_obj = self.pool['account.invoice.line']
        ctr_id = inter.contract_id and inter.contract_id.id or False
        for l in inter.line_ids:
            if ctr_id and not l.out_of_contract:
                # if contract and not out of contract
                # we must check next line
                continue

            line = {
                'origin': inter.number_request,
                'product_id': l.product_id.id,
                'quantity': l.product_qty,
                'discount': 0.0,
            }
            line.update(line_obj.product_id_change(
                cr, uid, [], l.product_id.id, l.product_uom_id.id,
                qty=line['quantity'], partner_id=inter.partner_invoice_id.id,
                fposition_id=inv['fiscal_position'], context=context,
                company_id=inter.company_id and inter.company_id.id or
                False)['value']
            )
            line['uos_id'] = l.product_uom_id.id,
            line['invoice_line_tax_id'] = [
                (6, 0, line['invoice_line_tax_id'])
            ]
            if not l.to_invoice:
                line['discount'] = 100.0
            res.append(line)

        return res

    def _compute_standard_price(self, cr, uid, product, context=None):
        """
        Override this function, id you want to provide another
        standard price
        """
        return product.standard_price

    def generate_analytic_line(self, cr, uid, ids, context=None):
        """
        For each line, add line on contract to bill alter
        """
        res = super(CrmIntervention, self).generate_analytic_line(cr, uid, ids, context=context)
        al_obj = self.pool['account.analytic.line']
        for inter in self.browse(cr, uid, ids, context=context):
            if not inter.contract_id:
                continue
            emp = self._get_employee(cr, uid, inter, context=context)
            for line in inter.line_ids:
                if line.out_of_contract:
                    # Line out of contract must be invoice directly
                    continue
                q = self._compute_standard_price(cr, uid, line.product_id, context=context)
                amount = q * line.product_qty
                unit_amount = q
                unit = line.product_uom_id.id
                vals = {
                    'name': _('BI Num %s') % inter.number_request,
                    'account_id': inter.contract_id.id,
                    'journal_id': emp.journal_id.id,
                    'user_id': inter.user_id.id,
                    'date': inter.date_effective_start[:10],
                    'ref': inter.name[:64],
                    'to_invoice': inter.contract_id.to_invoice.id,
                    'product_id': line.product_id.id,
                    'unit_amount': unit_amount,
                    'product_uom_id': unit,
                    'amount': amount,
                    'general_account_id': inter.product_id.property_account_income.id,  # noqa
                }

                line_id = al_obj.create(
                    cr, uid, vals,  context=context)
                line.write({'analytic_line_id': line_id}, context=context)

        return res

    def copy(self, cr, uid, id, default=None, context=None):
        """
        """
        if context is None:
            context = {}

        if default is None:
            default = {}

        default.update({
            'line_ids': None
        })

        return super(CrmIntervention, self).copy(
            cr, uid, id, default, context=context)

    def write(self, cr, uid, ids, values, context=None):
        """
        If state is done, we must copy the report result to the history
        """
        if context is None:
            context = {}

        if values.get('state','') == 'done':
            hist_obj = self.pool['intervention.equipment.history']
            equi_obj = self.pool['intervention.equipment']
            for rec in self.browse(cr, uid, ids, context=context):
                if rec.equipment_id and rec.date_effective_start:
                    equi_obj.write(cr, uid, [rec.equipment_id.id], {
                        'last_int_date': rec.date_effective_start[:10]
                    }, context=context)

                    hist_args = {
                        'equipment_id': rec.equipment_id.id,
                        'hist_date': rec.date_effective_start[:10],
                        'user_id': rec.user_id.id,
                        'summary': rec.description,
                    }
                    hist_obj.create(cr, uid, hist_args, context=context)

        return super(CrmIntervention, self).write(cr, uid, ids, values, context=context)


class CrmInterventionLines(orm.Model):
    _name = 'intervention.line'
    _description = 'Line of intervention'

    _columns = {
        'inter_id': fields.many2one(
            'crm.intervention', 'Intervention', required=True,
            help='This line is link on this intervention'),
        'product_id': fields.many2one(
            'product.product', 'Product', required=True,
            help='Product use on this interevntion'),
        'product_qty': fields.float(
            'Qty', digits_compute=dp.get_precision('Account'),
            required=True, help='Quantity of product'),
        'product_uom_id': fields.many2one(
            'product.uom', 'Uom', required=True,
            help='Unit to invoice for this  product'),
        'to_invoice': fields.boolean('To invoice', help='If check , this lines must be invoiced'),
        'move_id': fields.many2one('stock.move', 'Move', help='Move related to stock output'),
        'prodlot_id': fields.many2one(
            'stock.production.lot', 'Lot',
            help='If product is manage per lot, fill this field'),
        'src_location_id': fields.many2one(
            'stock.location', 'Location',
            help='Location where the products have been consumed, if different from global one'),
        'out_of_contract': fields.boolean(
            'Out of contract',
            help='If check, this line must be invoice directly, and not in contract if present'),
        'analytic_line_id': fields.many2one(
            'account.analytic.line', 'Analytic line',
            help='Analytic line'),
    }

    _defaults = {
        'product_qty': 0.0,
        'to_invoice': True,
        'out_of_contract': False,
    }

    def onchange_product_id(self, cr, uid, ids, product_id, context=None):
        vals = {'value': {
            'product_qty': 0.0,
            'product_uom_id': False,
        }}
        if not product_id:
            return vals

        pro = self.pool['product.product'].browse(cr, uid, product_id, context=context)
        vals['value'].update({
            'product_qty': 1.0,
            'product_uom_id': pro.uom_id.id,
        })

        return vals
