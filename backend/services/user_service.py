from nostr_sdk import Keys
from timeit import default_timer as timer


# This script generates a Nostr keypair and prints the private key and public key
def generate_nostr_key_pair(prefix):
    # Generate a new Nostr private key
    while (True):
        keys = Keys.generate()
        private_key = keys.secret_key()
        public_key = keys.public_key()
        print(f"Generated Public Key: {public_key.to_bech32()}")
        print(f"Generated Private Key: {private_key.to_bech32()}")
        if public_key.to_bech32().startswith(prefix):
            print(f"Public key starts with '{prefix}'")
            return private_key, public_key


# Example usage
prefix = "npub1mrkt"
starttime = timer()
print("Generating Nostr key pair...")
private_key, public_key = generate_nostr_key_pair(prefix)
endtime = timer()

print(f"Key generation took {endtime - starttime:.2f} seconds")
print(f"Private Key: {private_key.to_bech32()}")
print(f"Public Key: {public_key.to_bech32()}")