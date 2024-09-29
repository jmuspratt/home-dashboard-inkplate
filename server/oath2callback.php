<?php
require 'vendor/autoload.php';

use Google\Client;

$client = new Client();
$client->setAuthConfig('path/to/credentials.json'); // Path to your credentials file
$client->setRedirectUri('http://localhost:8080/oauth2callback');

if (isset($_GET['code'])) {
    // Fetch the access token using the authorization code from Google
    $accessToken = $client->fetchAccessTokenWithAuthCode($_GET['code']);
    if (array_key_exists('error', $accessToken)) {
        throw new Exception('Error while fetching access token: ' . join(', ', $accessToken));
    }
    // Save the access token to token.json
    file_put_contents('token.json', json_encode($accessToken));
    echo "Access token saved successfully. You can go back to the main page.";
} else {
    echo "Authorization code not found.";
}
?>