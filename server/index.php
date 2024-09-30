<?php
require 'vendor/autoload.php';
require 'config/config.php';
require 'functions.php';

// Set the timezone
date_default_timezone_set('America/New_York');

// Date
echo "Today is " .  date('l, F j') . "<br />";

// Allowances
$will_records = get_airtable_records('Will Transactions', $airtableApiKey, $airtableBaseID);
$eliza_records = get_airtable_records('Eliza Transactions', $airtableApiKey, $airtableBaseID);
renderAllowances($will_records, $eliza_records);

// Calendar
$events = getCalendar($keyFilePath, $calendarId);
renderCalendar($events);

// Footer
echo "<br />------------------------------------------------<br />";
echo "<br />(Updated " .  date('l, F j') . " at " . date('g:i a') . ")";

?>