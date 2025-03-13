------------------------
helpdesk_ticket_followup
------------------------

Automates ticket followups for customer update stage with ability to snooze them

Configuration
-------------
- Go to Settings -> Helpdesk ticket followup section.
  There you can setup followups messages and automatic closure of ticket,
  allow user turn off/snooze followup email notifications.

- Go to Helpdesk -> Configuration -> Stages.
  If you want this module to work correctly - set up selection "Stage" for stages:
  > In progress - this stage will be triggered whenever client or person from same company will write message in ticket
  > Customer update - this stage will be triggered whenever ticket assignee will write message in ticket.
  After switching to this stage followups messages and automatic closure timers will
  be applied to current ticket, and will be automatically triggered in 24 48 72 hours.
  Do not forget set up (and edit according to your liking) first and second email templates
  (default examples are "Ticket: Followup email " #1 and #2)
  > Closed - this stage will be triggered whenever ticket in "customer update" stage reach automatic closure time.
  Keep in mind that you can set stage only for one helpdesk stage.
  If you want Scheduled actions that send emails being triggered more often than in one hour go to
  Settings -> Technical -> Scheduled actions -> "Helpdesk Ticket Followup: auto ticket update" and change "Execute every" field.

