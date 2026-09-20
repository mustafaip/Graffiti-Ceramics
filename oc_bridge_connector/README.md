# Community <-> Enterprise Bridge Connector

Syncs, in real time, over a simple authenticated HTTP/JSON endpoint:

| Direction | Data |
|---|---|
| **Enterprise → Community** | Products, UoM, Customers (`res.partner`), Pricelists |
| **Community → Enterprise** | Quotations & Sales Orders |

No third-party middleware, message broker, or hosting is required — the same
module runs inside both Odoo instances and talks directly to the other one's
web server.

## 1. Install

Copy the `oc_bridge_connector` folder into the `addons` path of **both**
databases, then:

```
Apps > Update Apps List > search "Community-Enterprise Bridge Connector" > Install
```

Do this on **both** the Community database and the Enterprise database.

## 2. Configure

Go to **Settings > Connector Bridge** (or Settings app search "Connector
Bridge") on each database:

**On the Enterprise database:**
- This instance is: `Enterprise (master data source)`
- Remote Odoo URL: the public URL of your **Community** instance
- Shared API Key: any long random string, e.g. generate with
  `python3 -c "import secrets; print(secrets.token_hex(32))"`

**On the Community database:**
- This instance is: `Community (sales source)`
- Remote Odoo URL: the public URL of your **Enterprise** instance
- Shared API Key: **the exact same value** you set on Enterprise

Both servers must be reachable from each other over HTTPS (open the
firewall/reverse-proxy for `/oc_connector/receive` on each side).

## 3. Test it

1. On Enterprise, create or edit a product, a customer, or a pricelist.
   Within a second or two it should appear on Community.
2. On Community, create a quotation and add a couple of lines. Within a
   second or two it should appear on Enterprise as a Sales Order, with the
   Community order number stored in the "Customer Reference" field so you
   can trace it back.
3. If anything fails to send (e.g. one server was briefly down), it lands
   in **Connector Bridge > Sync Queue** with the error message, and is
   retried automatically every 5 minutes. You can also open a queue record
   and re-save it, or just wait for the next cron run.
4. **Connector Bridge > Record Mapping** shows which local record
   corresponds to which remote record — useful for debugging duplicates.

## How matching works (to avoid duplicate records)

Since there's no shared database, the two sides don't share record IDs.
Matching is done by business key, then cached in the mapping table so future
updates hit the *same* remote record:

- **Products** — matched by Internal Reference (`default_code`); make sure
  every product you want synced has one.
- **Customers** — matched by VAT number, then email, then name (first match
  wins).
- **UoM** — matched by name + category.
- **Pricelists** — matched by name. Pricelist items are fully replaced on
  every sync (simplest way to keep them in lock-step).
- **Sales Orders** — matched by Community's order reference, stored in the
  "Customer Reference" field on the Enterprise order.

## Notes / things to double check for your setup

- This connector doesn't touch Odoo Enterprise licensing — Enterprise still
  needs its own valid subscription; the connector is just moving data
  between two independently-licensed databases.
- Deleting a record on the pushing side sends an `unlink`, which deletes the
  mapped record on the other side too. If you'd rather archive than delete,
  say so and the `unlink` handling can be changed to write `active = False`
  instead.
- Only the fields listed in each `_oc_*_payload()` method (in
  `models/*.py`) are synced. If you need more fields (e.g. product
  categories, customer tags, multi-currency pricelists), add them there —
  each payload builder is a short, self-contained method.
- Pricelist items are matched to products via `default_code`, so variants
  without one won't get pricelist rules synced.
