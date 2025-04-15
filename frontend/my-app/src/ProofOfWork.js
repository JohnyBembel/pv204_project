async function hashString(message) {
    const encoder = new TextEncoder();
    const data = encoder.encode(message);
    const hashBuffer = await crypto.subtle.digest('SHA-256', data);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    // Convert bytes to hex string
    const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
    return hashHex;
  }
  
  // Function to check if a hash meets the difficulty target
  function isValidHash(hash, difficulty) {
    const requiredPrefix = '0'.repeat(difficulty);
    return hash.startsWith(requiredPrefix);
  }
  
  // The main function that performs the proof of work
  // listingData: an object containing listing info
  // difficulty: the number of leading zeros required in the hash
  export async function computeProofOfWork(listingData, difficulty = 4) {
    // Serialize listing data. Adjust the serialization if your data structure is more complex.
    const baseData = JSON.stringify(listingData);
    let nonce = 0;
    let hash = "";
    
    // Loop until a valid hash is found
    while (true) {
      // Combine the base data with the nonce
      const trialData = baseData + nonce;
      
      // Compute the hash of the combined data
      hash = await hashString(trialData);
      
      // Check if the hash meets the difficulty requirement
      if (isValidHash(hash, difficulty)) {
        // Return both the valid nonce and the hash
        return { nonce, hash };
      }
      
      // Increment the nonce and try again
      nonce++;
    }
  }