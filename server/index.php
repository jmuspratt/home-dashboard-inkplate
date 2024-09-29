<?php
require 'vendor/autoload.php';
require 'config/config.php';

date_default_timezone_set('America/New_York');


use Google\Client;
use Google\Service\Calendar;
use TANIOS\Airtable\Airtable;

$airtable = new Airtable(array(
    'api_key'   => $airtableApiKey,
    'base'      => $airtableBaseID
));


function get_airtable_records($table) {
    global $airtable;
    $params = array(
        "sort" => array(
            array(
                "field" => "Created Timestamp",
                "direction" => "desc"
            )
        ),
        "pageSize" => 99,
        "maxRecords" => 999
    );
    
    $request = $airtable->getContent($table, $params);
    $allRecords = [];

    do {
        $response = $request->getResponse();
        $allRecords = array_merge($allRecords, $response->records);
    } while ($request = $response->next());

    return $allRecords;
}


// Loop through all records and sum up both Amount USD and Amount EUR fields, then return both
function getBalances($records) {
    $totalUSD = 0;
    $totalEUR = 0;
    foreach ($records as $record) {
        $fields = $record->fields;
        $totalUSD += $fields->{'Amount USD'} ?? 0;
        $totalEUR += $fields->{'Amount EUR'} ?? 0;
    }
    return array($totalUSD, $totalEUR);
}

$will_records = get_airtable_records('Will Transactions');
$willLastFive = array_slice($will_records, 0, 5);
$will_balance_usd = getBalances($will_records)[0];
$will_balance_eur = getBalances($will_records)[1];

$eliza_records = get_airtable_records('Eliza Transactions');
$elizaLastFive = array_slice($eliza_records, 0, 5);
$eliza_balance_usd = getBalances($eliza_records)[0];
$eliza_balance_eur = getBalances($eliza_records)[1];


// print_r($willLastFive);

echo "<br />------------------------<br />";
echo ("Will USD: $" . number_format($will_balance_usd, 2)) . "<br />";
echo ("Will EUR: €" . number_format($will_balance_eur, 2)) . "<br />";

echo "<br />------------------------<br />";
echo ("Eliza USD: $" . number_format($eliza_balance_usd, 2)) . "<br />";;
echo ("Eliza EUR: €" . number_format($eliza_balance_eur, 2)) . "<br />";;


// foreach ($willLastFive as $record) {
//     $fields = $record->fields;

//     $amountUSD = $fields->{'Amount USD'} ?? false;
//     $amountEUR = $fields->{'Amount EUR'} ?? false;
//     $created = $fields->{'Created Timestamp'} ?? false;
//     $description = $fields->Description ?? false;
  
//     $created_pretty = date('l, F j', strtotime($created)) ?? false;
//     $amountUSD_pretty = $amountUSD ? number_format($amountUSD, 2)  : false;
//     $amountEUR_pretty = $amountEUR ? number_format($amountEUR, 2) : false;

//     if ($created_pretty) :
//         echo "<br />" . $created_pretty ."<br />";
//     endif;
//     if ($description) :
//         echo $description ."<br />";
//     endif;
//     if ($amountUSD_pretty) :
//         echo "Amount USD:" . $amountUSD_pretty . "<br />";
//     endif;
//     if ($amountEUR_pretty) :
//         echo "Amount EUR:" . $amountEUR_pretty . "<br />";
//     endif;

// }


// Step 1: Set up the Google Client with a service account
$client = new Client();
$client->setAuthConfig($keyFilePath); 
$client->addScope(Calendar::CALENDAR_READONLY); // Set the appropriate scope

// Step 2: Get the Calendar Service
$service = new Calendar($client);

// Step 3: Fetch the events
$events = $service->events->listEvents($calendarId, [
    'maxResults' => 15,
    'orderBy' => 'startTime',
    'singleEvents' => true,
    'timeMin' => date('c'), // Fetch future events only
]);


if (count($events->getItems()) == 0) {
    echo "No upcoming events found.\n";
} else {
        echo ("<br /><br />CALENDAR<br />");
  
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