<?php


use Google\Client;
use Google\Service\Calendar;
use TANIOS\Airtable\Airtable;


function wrapText($string) {
    $lineLength = 63;
    if (strlen($string) > $lineLength) {
        $string = wordwrap($string, $lineLength, "<br />");
    } 
    return $string;
}


function getWeather() {
    // Arlington is 42.41194,-71.14738
    // Here's what you get for https://api.weather.gov/points/42.41194,-71.14738
    $forecastUrl = "https://api.weather.gov/gridpoints/BOX/68,92/forecast";
    // $forecastHourly = "https://api.weather.gov/gridpoints/BOX/68,92/forecast/hourly";
    // $forecastGridData = "https://api.weather.gov/gridpoints/BOX/68,92";
    // $observationStations = "https://api.weather.gov/gridpoints/BOX/68,92/stations";
   
    // Create a stream context with the User-Agent header
    $options = [
        "http" => [
            "header" => "User-Agent: MyWeatherApp/1.0 (your_email@example.com)"
        ]
    ];
    $context = stream_context_create($options);

    // Get JSON data from the API
    $jsonData = @file_get_contents($forecastUrl, false, $context);
    if ($jsonData === FALSE) {
        echo "Unable to retrieve weather data.";
        return null;
    }

    // Convert JSON data into PHP array
    $weatherData = json_decode($jsonData, true);
    if (json_last_error() !== JSON_ERROR_NONE) {
        echo "Error decoding JSON data.";
        return null;
    }

    return $weatherData;
}

function renderWeather($weatherData) {
    $output = "<br />--------------------------------------------------------------<br />";
    $output .= "Weather<br /><br />";

    if ($weatherData && isset($weatherData['properties']['periods'])) {
        $todaysWeather = $weatherData['properties']['periods'][0];
        $output .= $todaysWeather['name'] . ": " . $todaysWeather['detailedForecast'];

    } else {
        $output .= "No weather data available.";
    }
    $output .= "<br />";
    echo wrapText($output);
}


function getAirtableRecords($table, $key, $baseID) {
    
    $airtable = new Airtable(array(
        'api_key'   => $key,
        'base'      => $baseID
    ));
    
    $params = array(
        "pageSize" => 99,
        "maxRecords" => 999
    );
    
    $request = $airtable->getContent($table, $params);
    $allRecords = [];

    do {
        $response = $request->getResponse();
        if ($response):
            $allRecords = array_merge($allRecords, $response->records);
        endif;
    } while ($request = $response->next());

    return $allRecords;
}

// Loop through all records and sum up both Amount USD and Amount EUR fields, then return both
function getAllowances($records) {
    $totalUSD = 0;
    $totalEUR = 0;
    foreach ($records as $record) {
        $fields = $record->fields;
        $totalUSD += $fields->{'Amount USD'} ?? 0;
        $totalEUR += $fields->{'Amount EUR'} ?? 0;
    }
    return array($totalUSD, $totalEUR);
}



function getCalendar($keyFilePath, $calendarId) {

    // Step 1: Set up the Google Client with a service account
    $client = new Client();
    $client->setAuthConfig($keyFilePath); 
    $client->addScope(Calendar::CALENDAR_READONLY); // Set the appropriate scope

    // Step 2: Get the Calendar Service
    $service = new Calendar($client);

    // Step 3: Fetch the events
    $events = $service->events->listEvents($calendarId, [
        'maxResults' => 10,
        'orderBy' => 'startTime',
        'singleEvents' => true,
        'timeMin' => date('c'), // Fetch future events only
    ]);

    return $events;

}


function renderCalendar($events) {
    $output = "";
    if (count($events->getItems()) == 0) :
        $output .= "No upcoming events found.\n";
    else :
        $output .= "<br />--------------------------------------------------------------<br />";
        $output .= ("Calendar<br />");
        // Track the current day to determine when to add a new heading
        $currentDay = null;

        foreach ($events->getItems() as $event) :
            $summary = $event->summary ?: 'No summary';

            // Check if start and end dateTime are set before proceeding
            if (isset($event->start->dateTime) && isset($event->end->dateTime)) :
                $startDateTime = new DateTime($event->start->dateTime);
                $endDateTime = new DateTime($event->end->dateTime);

                // Format date and times
                $eventDay = $startDateTime->format('l, F j'); // e.g., "Monday, September 30"
                $startTime = $startDateTime->format('g:i a'); // e.g., "4:00 pm" 
                $endTime = $endDateTime->format('g:i a'); // e.g., "5:15 pm"

                // If this event's date is different from the current day, insert a new heading
                if ($currentDay !== $eventDay) :
                    $output .= "<br />$eventDay<br />";
                    $currentDay = $eventDay;
                endif;

                // Print the event with formatted times
                $timeSpan = "{$startTime} - {$endTime}";
                $output .= "{$timeSpan}: {$summary}<br />";
            else :
                // Handle the case where dateTime is not set (e.g., all-day events)
                if (isset($event->start->date)) :
                    $eventDay = (new DateTime($event->start->date))->format('l, F j');
                    
                    if ($currentDay !== $eventDay) :
                        $output .= "<br />$eventDay<br />";
                        $currentDay = $eventDay;
                    endif;

                    $timeSpan = "All day";
                    $output .= "{$timeSpan}: {$summary}<br />";
                endif;
            endif;
        endforeach;
    endif;
    echo wrapText($output);
}

function renderLunch($lunch) {
// Get the day number
    $todayNumber = date('j');

    // Find the record in $lunches whose Day Number field matches $todayNumber
    $todaysLunch = null;
    foreach ($lunch as $record) {
        $fields = $record->fields;
        $dayNumber = $fields->{'Day Number'};
        if ($dayNumber == $todayNumber) {
            $todaysLunch = $fields->{'Meal'};
            break;
        }
    }

    // If a lunch was found, display it
    if ($todaysLunch) {
        $output = "<br />--------------------------------------------------------------<br />";
        $output .= ("Lunch<br /><br />");
        $output .= "Today's lunch is: " . $todaysLunch;
        $output .= "<br />";
        echo wrapText($output);
    }
}

function renderAllowances($willRecords, $elizaRecords) {

    $willLastFive = array_slice($willRecords, 0, 5);
    $willBalanceUSD = getAllowances($willRecords)[0];
    $willBalanceEUR = getAllowances($willRecords)[1];

    $elizaLastFive = array_slice($elizaRecords, 0, 5);
    $elizaBalanceUSD = getAllowances($elizaRecords)[0];
    $elizaBalanceEUR = getAllowances($elizaRecords)[1];


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

    $output = "<br />--------------------------------------------------------------<br />";
    $output .= ("Allowance Balances<br /><br />");
    $output .= ("Will: $" . number_format($willBalanceUSD, 2)) . "<br />";
    $output .= ("Eliza: $" . number_format($elizaBalanceUSD, 2));
    $output .= "<br />";
    echo wrapText($output);
}


?>