======================
stock_pre_reserve
======================

Allows users to manually link stock.moves together using move_dest_ids and
move_src_ids. A record is kept of the manually linked items.

This is intended to allow users to "pre-reserve" stock from an inbound receipt
(stock.move), for an outbound delivery (stock.move), giving it preferential
treatment over any other features within the reservation system (i.e. dates,
etc.).

Usage
=====

1. Create an inbound receipt for widgetA
2. Create an outbound delivery for widgetA
3. A `link` icon will appear in the outbound delivery for widgetA, prompting the
   user to select the availableinbound receipt(s).
4. User selects the line and links the two together
5. An `Unlink` icon will now appear in the outbound delivery, and the inbound
   receipt allowing this to be undone.

Usage case
==========

* If purchasing a large quantity of a product on a regular basis, in containers
* It is common practise for users to promise an amount of goods from one of
  these containers
* It is unacceptable for that stock to be "stolen" by another stock.move
* This is acheived through this module by abusing the move_dest_ids and
  move_src_ids fields.

