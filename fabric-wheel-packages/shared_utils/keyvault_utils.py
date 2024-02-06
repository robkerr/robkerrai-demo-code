def get_keyvault_secret(key_vault_name, key_name):
  from notebookutils import mssparkutils
  from trident_token_library_wrapper import PyTridentTokenLibrary as tl

  # Get access token to key vault for current session ID
  access_token = mssparkutils.credentials.getToken("keyvault")

  secret = tl.get_secret_with_token( \
    f"https://{key_vault_name}.vault.azure.net/", \
    key_name, \
    access_token)
  
  # Print this for demo purposes (not recommended in production code)
  print(f"Got a secret with {len(secret)} bytes length.")
  return secret