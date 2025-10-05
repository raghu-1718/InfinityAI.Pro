$uri = 'http://infinityai-app.agreeablemeadow-7375b1f7.eastus.azurecontainerapps.io/api/chatbot/chat'

$headers = @{
    'Content-Type' = 'application/json'
}

$bodyJson = @{
    message = "Hello, how are you?"
    user_id = "test123"
    voice_input = $false
} | ConvertTo-Json -Depth 3

Write-Host "URI: $uri"
Write-Host "Headers: $($headers | ConvertTo-Json)"
Write-Host "Body: $bodyJson"

try {
    $response = Invoke-RestMethod -Uri $uri -Method 'POST' -Headers $headers -Body $bodyJson -ContentType 'application/json'
    Write-Host "Success:"
    $response | ConvertTo-Json -Depth 5
} catch {
    Write-Host "Error occurred:"
    Write-Host "Status Code: $($_.Exception.Response.StatusCode)"
    Write-Host "Status Description: $($_.Exception.Response.StatusDescription)"
    Write-Host "Exception Message: $($_.Exception.Message)"
    
    if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $responseBody = $reader.ReadToEnd()
        Write-Host "Response Body: $responseBody"
    }
}