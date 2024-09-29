<?php
require 'vendor/autoload.php';
require 'config/config.php';

date_default_timezone_set('America/New_York');


use Google\Client;
use Google\Service\Calendar;

// Step 1: Set up the Google Client with a service account
$client = new Client();
$client->setAuthConfig($keyFilePath); 
$client->addScope(Calendar::CALENDAR_READONLY); // Set the appropriate scope

// Step 2: Get the Calendar Service
$service = new Calendar($client);

// Step 3: Fetch the events
$events = $service->events->listEvents($calendarId, [
    'maxResults' => 20,
    'orderBy' => 'startTime',
    'singleEvents' => true,
    'timeMin' => date('c'), // Fetch future events only
]);


if (count($events->getItems()) == 0) {
    echo "No upcoming events found.\n";
} else {
    echo "Upcoming<br />";
  
        // Track the current day to determine when to add a new heading
        $currentDay = null;

    foreach ($events->getItems() as $event) {

        
        $summary =  $event->summary ?: 'No summary';
        // Check if start and end dateTime are set before proceeding
        if (isset($event->start->dateTime) && isset($event->end->dateTime)) {
            $startDateTime = new DateTime($event->start->dateTime);
            $endDateTime = new DateTime($event->end->dateTime);

          
            
                // Format date and times
            $eventDay = $startDateTime->format('l, F j'); // e.g., "Monday, September 30"
            $startTime = $startDateTime->format('g:i'); // e.g., "4:00" (full minutes without AM/PM initially)
            $endTime = $endDateTime->format('g:i a'); // e.g., "5:15 pm"
    
                // Add AM/PM only for events that span noon
                if ($startDateTime->format('a') != $endDateTime->format('a')) {
                    $startTime .= ' ' . $startDateTime->format('a'); // Append am/pm if spans noon
                }
    
            // If this event's date is different from the current day, insert a new heading
          if ($currentDay !== $eventDay) {
            echo "<br />------------------------<br />";
            echo "<br />$eventDay<br />";
            $currentDay = $eventDay;
        }
            $timeSpan = "{$startTime} - {$endTime}";

        } else {
            $timeSpan = "All day";
        }

       // Print the event with formatted times
       echo "{$timeSpan}: {$summary}<br />";
    }
}
echo "<br />------------------------<br />";
echo "<br />(Updated " .  date('l, F j') . " at " . date('g:i a') . ")";

?>