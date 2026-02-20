==============================
backport_stock_barcode_manual_scan
==============================

Adds a manual barcode entry button to the stock barcode interface, allowing
users to type barcodes via keyboard when a hardware scanner is unavailable.

- A keyboard icon button is injected next to the mobile scanner button in the
  barcode UI.
- Clicking the button opens a prompt dialog for manual barcode input.
- The entered barcode is passed through the standard ``processBarcode()``
  pipeline, so all existing barcode logic applies.

Usage
=====

1. Open any stock barcode operation (e.g. a receipt, delivery, or inventory).
2. Click the **keyboard icon** button in the header toolbar.
3. Type the barcode and confirm.

The barcode is processed identically to one scanned by a hardware device.
