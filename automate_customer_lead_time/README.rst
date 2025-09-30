Automate Customer Lead Time
===========================
Odoo Standard Method:
* Set customer Lead Time on product
* Set vendor Lead Time on product supplier info
* Place a sales order for the product
* Regardless of stock or vendor lead time, the customer lead time is used as the expected delivery date

This Module:
* Adds a field to each product to choose how to handle vendor lead time
- Add: Customer lead time + Vendor lead time (Default)
- Replace: Use Vendor lead time only
- Max: Use the maximum of Customer lead time or Vendor lead time
- Min: Use the minimum of Customer lead time or Vendor lead time
* When placing a sales order, the customer lead time is adjusted based on the selected method and the vendor lead time from the product's supplier info
* The expected delivery date on the sales order line is updated accordingly, along with all related pickings

Vendor lead time is determined at the point of adding the product to the sales order, or
when product quantity is changed on the sale order line. If the product is in stock,
only the customer lead time is used, but if the product is out of stock, the vendor lead
time is included based on the selected method.
