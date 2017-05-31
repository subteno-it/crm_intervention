# -*- coding: utf-8 -*-

from openerp.osv import orm
from openerp.osv import fields


class InterventionEquipment(orm.Model):
    _name = 'intervention.equipment'
    _description = 'Equipment per site'

    _columns = {
        'name': fields.char(
            'Name', required=True, size=64, help='Name of the equipment'),
        'site_id': fields.many2one(
            'intervention.site', 'Site',
            help='Site where the equipment is visible'),
        'partner_id': fields.related(
            'site_id', 'partner_id', type='many2one', relation='res.partner',
            string='Customer', store=True, help='Customer link to the site'),
        'active': fields.boolean(
            'Active', help='if check, this object is always available'),
        'buy_date': fields.date(
            'Buying date', help='Date when the equipment have been buy'),
        'starting_date': fields.date(
            'Commissioning', help='Date of the Commissioning'),
        'eow_date': fields.date(
            'End of warranty', help='End of the warranty'),
        'last_int_date': fields.date(
            'Last Intervention', help='Last intervention date'),
        'replace_date': fields.date(
            'Replacement', help='Date when this equipment must be replace'),
        'product_number': fields.char(
            'Product Number', size=64, help='Product Number of the equipment'),
        'serial_number': fields.char(
            'Serial Number', size=64, help='Serial number'),
        'supplier_id': fields.many2one(
            'res.partner', 'Supplier',
            help='Select supplier for this equipment'),
        'history_ids': fields.one2many(
            'intervention.equipment.history', 'equipment_id',
            'Histories', help='Histories for this equipment'),
    }

    _defaults = {
        'active': True,
    }


class InterventionEquipmentHistory(orm.Model):
    _name = 'intervention.equipment.history'
    _description = 'Equipment history'
    _order = 'hist_date desc'

    _columns = {
        'equipment_id': fields.many2one(
            'intervention.equipment', 'equipment',
            help='Equipement link to this history'),
        'hist_date': fields.date('Date', required=True, help='History date'),
        'user_id': fields.many2one('res.users', 'Users', required=True, help='Users that made this entry'),
        'summary': fields.text('Summary', help='Summary from this note'),
    }

    _defaults = {
        'hist_date': fields.date.context_today,
        'user_id': lambda self, cr, uid, ctx: uid,
        'summary': False,
    }
