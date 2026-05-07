# -*- coding: utf-8 -*-
# stock_move.py — intentionally minimal.
#
# We do NOT add Many2many back-relations on stock.move because:
#   1. The relation tables are owned by intercompany.flow.log already.
#   2. Adding inverse Many2many fields here causes ORM relation-table
#      conflicts when the module is re-installed after a failed attempt.
#   3. Odoo 19 view validation checks all fields in inline <list> views
#      against the model at load time; a corrupt registry from a prior
#      failed install can make even real fields appear missing.
#
# Traceability is fully available via the log model's own fields:
#   log.stock_move_out_ids  and  log.stock_move_in_ids
