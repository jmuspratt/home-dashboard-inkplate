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

// Weather
$weatherData = getWeather();
if ($weatherData) :
    renderWeather($weatherData); 
endif;


// School Lunch
$lunchData = getAirtableRecords('Lunches', $airtableApiKey, $airtableBaseID);
if ($lunchData) :
    renderLunch($lunchData);
endif;

// Allowances
$willRecords = getAirtableRecords('Will Transactions', $airtableApiKey, $airtableBaseID);
$elizaRecords = getAirtableRecords('Eliza Transactions', $airtableApiKey, $airtableBaseID);
if ($willRecords && $elizaRecords) :
    renderAllowances($willRecords, $elizaRecords);
endif;

// Calendar
$events = getCalendar($keyFilePath, $calendarId);
if ($events) :
    renderCalendar($events);
endif;

// Footer
echo "<br />(Updated " .  date('l, F j') . " at " . date('g:i a') . ")";

?>