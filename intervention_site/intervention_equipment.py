# -*- coding: utf-8 -*-

from openerp.osv import orm
from openerp.osv import fields


class InterventionEquipmentType(orm.Model):
    _name = 'intervention.equipment.type'
    _description = 'Type of equipment'

    _columns = {
        'name': fields.char(
            'Name', size=64, required=True,
            help='Name of equipment type'),
        'code': fields.char(
            'Code', size=32,
            help='Code of equipment type'),
        'active': fields.boolean(
            'Active', help='if check, this object is always available'),
        'company_id': fields.many2one(
            'res.company', 'Company'),
        'equipment_ids': fields.one2many(
            'intervention.equipment', 'type_id', 'Equipment',
            help='List of equipement link to this type'),
    }

    _defaults = {
        'active': True,
        'company_id': lambda s, cr, uid,c:
            s.pool.get('res.company')._company_default_get(
                cr, uid, 'intervention.equipment.type', context=c),
    }


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
        'next_date': fields.date(
            'Next visit date',
            help='Indicate the next visite date'),
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
        'type_id': fields.many2one(
            'intervention.equipment.type', 'Type',
            help='Select type of the equipment'),
        'user_id': fields.many2one(
            'res.users', 'Repairer',
            help='Choose dedicate repairer for this equipment'),
        'company_id': fields.many2one(
            'res.company', 'Company'),
        'contract_id': fields.many2one(
            'account.analytic.account', 'Contract',
            help='Contract relate to this equipment'),
        'out_of_contract': fields.boolean(
            'Out of contract', help='This equipment'),
        'notes': fields.text('Notes', help='Notes'),
    }

    _defaults = {
        'name': '/',
        'active': True,
        'company_id': lambda s, cr, uid,c:
            s.pool.get('res.company')._company_default_get(
                cr, uid, 'intervention.equipment', context=c),
    }

    def name_get(self, cr, uid, ids, context=None):
        """
        For each equipment, add site and serial number
        """
        if context is None:
            context = {}
        if not len(ids):
            return []
        equips = self.browse(cr, uid, ids, context=context)
        res = []
        for equip in equips:
            name = equip.name
            e = equip.site_id
            if e:
                name += ' (%s)' % (e.name or '',)
            if equip.serial_number:
                name += ' [%s]' % (equip.serial_number or '',)
            res.append((equip.id, name))
        return res

    def create(self, cr, uid, values, context=None):
        """
        Generate site code
        """
        if context is None:
            context = {}

        if values.get('name', '') == '/':
            values['name'] = self.pool.get('ir.sequence').get(cr, uid, 'intervention.equip') or '/'

        return super(InterventionEquipment, self).create(cr, uid, values, context=context)


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
        'comapnyd_id': fields.related(
            'equipment_id', 'company_id', type='many2one', store=True,
            relation='intervention.equipment', string='Company'),
    }

    _defaults = {
        'hist_date': fields.date.context_today,
        'user_id': lambda self, cr, uid, ctx: uid,
        'summary': False,
    }
