#run az login before running this script

$ACR="acrklainvagent"
$IMAGE_NAME="webapp-kla-inv-agent"
$TAG="latest"
$ACR_REPO="$IMAGE_NAME"

Write-Host ">>> Fetch login server for ACR name..."
$LOGIN_SERVER = (az acr show -n $ACR --query loginServer -o tsv)
$LOGIN_SERVER

Write-Host ">>> Building the Container image..."
podman build -t "${IMAGE_NAME}:${TAG}" .

# tag the image with the full ACR path

Write-Host ">>> Tagging image..."
$FULL_IMAGE="${LOGIN_SERVER}/${ACR_REPO}:${TAG}"
podman tag "${IMAGE_NAME}:${TAG}" "$FULL_IMAGE"

# Get an ACR access token and log in with Podman

Write-Host ">>> Login to Azure Container Registry..."
$TOKEN = az acr login --name $ACR --expose-token --output tsv --query accessToken
podman login $LOGIN_SERVER --username 00000000-0000-0000-0000-000000000000 --password $TOKEN

# Write-Host ">>> Push the image to the container registry..."
podman push "$FULL_IMAGE"