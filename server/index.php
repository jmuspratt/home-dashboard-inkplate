<?php
require 'vendor/autoload.php';
require 'config/config.php';
require 'functions.php';

// Set the timezone
date_default_timezone_set('America/New_York');

// Check for the ?simple query parameter
$simple =  isset($_GET['simple']);


// Date
echo "Today is " .  date('l, F j') . "<br />";

// School Lunch
$lunches = get_airtable_records('Lunches', $airtableApiKey, $airtableBaseID);
if ($lunches) :
    renderLunch($lunches);
endif;

// Allowances
$will_records = get_airtable_records('Will Transactions', $airtableApiKey, $airtableBaseID);
$eliza_records = get_airtable_records('Eliza Transactions', $airtableApiKey, $airtableBaseID);
if ($will_records && $eliza_records) :
    renderAllowances($will_records, $eliza_records);
endif;

// Calendar
$events = getCalendar($keyFilePath, $calendarId);
if ($events) :
    renderCalendar($events);
endif;

// Footer
echo "<br />(Updated " .  date('l, F j') . " at " . date('g:i a') . ")";

?>