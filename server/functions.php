<?php


use Google\Client;
use Google\Service\Calendar;
use TANIOS\Airtable\Airtable;


function wrapText($string) {
    $lineLength = 62;
    if (strlen($string) > $lineLength) {
        // First, replace any existing <br /> with a temporary marker
        $string = str_replace('<br />', '||BR||', $string);
        // Do the word wrap
        $string = wordwrap($string, $lineLength, '<br />');
        // Restore any original <br /> tags
        $string = str_replace('||BR||', '<br />', $string);
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
        $output .= wrapText($todaysWeather['name'] . ": " . $todaysWeather['detailedForecast']);
    } else {
        $output .= "No weather data available.";
    }
    $output .= "<br />";
    echo $output;
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
    // Set the timezone to match your local timezone
    date_default_timezone_set('America/New_York');

    $client = new Client();
    $client->setAuthConfig($keyFilePath); 
    $client->addScope(Calendar::CALENDAR_READONLY);

    $service = new Calendar($client);

    // Set up date range for the query
    $today = new DateTime();
    $today->setTime(0, 0); // Start of today
    
    $endDate = new DateTime();
    $endDate->modify('+7 days'); // Look ahead 7 days
    $endDate->setTime(23, 59, 59); // End of the day

    // Format dates for the API
    $timeMin = $today->format('Y-m-d\TH:i:sP'); // RFC3339 format
    $timeMax = $endDate->format('Y-m-d\TH:i:sP'); // RFC3339 format

    $events = $service->events->listEvents($calendarId, [
        'maxResults' => 10,
        'orderBy' => 'startTime',
        'singleEvents' => true,
        'timeMin' => $timeMin,
        'timeMax' => $timeMax,
    ]);

    return $events;
}


function renderCalendar($events) {
    $output = "";
    if (count($events->getItems()) == 0) {
        $output .= "No upcoming events found.<br />";
    } else {
        $output .= "<br />--------------------------------------------------------------<br />";
        $output .= "Calendar<br />";
        
        // Get today's date for filtering
        $today = new DateTime();
        $today->setTime(0, 0);
        
        // Group events by day
        $eventsByDay = [];
        
        foreach ($events->getItems() as $event) {
            $summary = $event->summary ?: 'No summary';

            // Handle all-day events
            if (isset($event->start->date)) {
                $startDate = new DateTime($event->start->date);
                $endDate = new DateTime($event->end->date);
                
                // Create date range (end date is exclusive in Google Calendar)
                $dateRange = new DatePeriod($startDate, new DateInterval('P1D'), $endDate);

                // Add event to each day in range
                foreach ($dateRange as $date) {
                    if ($date->format('Y-m-d') >= $today->format('Y-m-d')) {
                        $eventDay = $date->format('Y-m-d'); // Use Y-m-d for sorting
                        if (!isset($eventsByDay[$eventDay])) {
                            $eventsByDay[$eventDay] = [
                                'display' => $date->format('l, F j'),
                                'events' => []
                            ];
                        }
                        $eventsByDay[$eventDay]['events'][] = "All day: " . wrapText($summary);
                    }
                }
            }
            // Handle regular events
            else if (isset($event->start->dateTime)) {
                $startDateTime = new DateTime($event->start->dateTime);
                
                if ($startDateTime->format('Y-m-d') >= $today->format('Y-m-d')) {
                    $eventDay = $startDateTime->format('Y-m-d'); // Use Y-m-d for sorting
                    if (!isset($eventsByDay[$eventDay])) {
                        $eventsByDay[$eventDay] = [
                            'display' => $startDateTime->format('l, F j'),
                            'events' => []
                        ];
                    }
                    $startTime = $startDateTime->format('g:i a');
                    $endTime = (new DateTime($event->end->dateTime))->format('g:i a');
                    $eventText = "{$startTime} - {$endTime}: " . $summary;
                    $eventsByDay[$eventDay]['events'][] = wrapText($eventText);
                }
            }
        }
        
        // Sort by date (Y-m-d format ensures chronological order)
        ksort($eventsByDay);
        
        // Output events by day
        foreach ($eventsByDay as $day => $dayData) {
            $output .= "<br />" . $dayData['display'] . "<br />" . implode("<br />", $dayData['events']) . "<br />";
        }
    }
    echo $output;
}

function renderLunch($lunch) {
    // Get the day number
    $todayNumber = date('j');

    // Find the record in $lunch whose Day Number field matches $todayNumber
    $todaysLunch = null;
    foreach ($lunch as $record) {
        if (!isset($record->fields) || !isset($record->fields->{'Day Number'})) {
            continue;
        }
        $fields = $record->fields;
        $dayNumber = $fields->{'Day Number'};
        if ($dayNumber == $todayNumber && isset($fields->{'Meal'})) {
            $todaysLunch = $fields->{'Meal'};
            break;
        }
    }

    // If a lunch was found, display it
    if ($todaysLunch) {
        $output = "<br />--------------------------------------------------------------<br />";
        $output .= "Lunch<br /><br />";
        $output .= wrapText($todaysLunch);
        $output .= "<br />";
        echo $output;
    }
    
    echo ""; // Return empty string if no lunch found
}

function renderAllowances($willRecords, $elizaRecords) {
    $willBalanceUSD = getAllowances($willRecords)[0];
    $willBalanceEUR = getAllowances($willRecords)[1];
    $elizaBalanceUSD = getAllowances($elizaRecords)[0];
    $elizaBalanceEUR = getAllowances($elizaRecords)[1];

    $output = "<br />--------------------------------------------------------------<br />";
    $output .= "Allowance Balances<br /><br />";
    $output .= "Will: $" . number_format($willBalanceUSD, 2) . "<br />";
    $output .= "Eliza: $" . number_format($elizaBalanceUSD, 2);
    $output .= "<br />";
    echo $output;
}


?>