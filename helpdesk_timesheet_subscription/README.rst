helpdesk_ticket_followup
--------------------------

Automates ticket followups for customer update stage with ability to snooze them


Setting up

Setup helpdesk items in helpdesk overview:
Helpdesk item -> Settings -> Track and bill time V Timesheets

You have to setup helpdesk team's product to time whatever will be billed when
we log team's time:
Helpdesk overview -> Settings -> Pick product time

Usage

You can see balance in contacts -> Pick any contact or company -> button balance

Also you can see balance history on balance view -> history button

Balance will be working only for companies or contacts with companies.
Whenever we create invoice for client with 'replenishment products' and make it into 'posted' state, time will be added to client's company balance.
Whenever time is logged in helpdesk or project - it will be substracted from balance of the customer

You will be able to see total time logged inside tickets, tasks, portal, etc.
