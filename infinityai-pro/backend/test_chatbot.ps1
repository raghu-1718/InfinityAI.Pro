$headers = @{
    'Content-Type' = 'application/json'
}

$body = @{
    message = "Hello, how are you?"
    user_id = "test123"
    voice_input = $false
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri 'http://infinityai-app.agreeablemeadow-7375b1f7.eastus.azurecontainerapps.io/api/chatbot/chat' -Method POST -Headers $headers -Body $body
    Write-Output "Success:"
    Write-Output $response
} catch {
    Write-Output "Error:"
    Write-Output $_.Exception.Message
}