<?php
require 'vendor/autoload.php';

use Google\Client;
use Google\Service\Calendar;

// Step 1: Set up the Google Client
$client = new Client();
$client->setAuthConfig('creds/client_secret_314667442939-h3908d95g5l3k36ttlt1vf8l0uf73ob7.apps.googleusercontent.com.json'); // Replace with the actual path to your downloaded credentials file
$client->setRedirectUri('http://localhost:8080/oauth2callback'); // Set the redirect URI
$client->setAccessType('offline'); // Offline access allows the app to refresh tokens when they expire
$client->setPrompt('select_account consent');
$client->addScope(Calendar::CALENDAR_READONLY); // Use appropriate scope

// Step 2: Check if access token exists
$tokenPath = 'token.json';
if (file_exists($tokenPath)) {
    $accessToken = json_decode(file_get_contents($tokenPath), true);
    $client->setAccessToken($accessToken);

    // Refresh token if it's expired
    if ($client->isAccessTokenExpired()) {
        $client->fetchAccessTokenWithRefreshToken($client->getRefreshToken());
        file_put_contents($tokenPath, json_encode($client->getAccessToken()));
    }
} else {
    // Step 3: Obtain a new token if none exists
    $authUrl = $client->createAuthUrl();
    // Redirect the user to the Google authorization page
    header('Location: ' . filter_var($authUrl, FILTER_SANITIZE_URL));
    exit();
}
?>