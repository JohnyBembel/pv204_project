import React, { useState } from 'react';
import './App.css';
import nacl from 'tweetnacl';
import { nip19 } from 'nostr-tools';
import { Buffer } from 'buffer';
// Import WASM loader and other necessary items from @rust-nostr/nostr-sdk
import { loadWasmSync, Keys, SecretKey } from '@rust-nostr/nostr-sdk';

window.Buffer = Buffer;
loadWasmSync();

function App() {
  // Registration state
  const [lightningAddress, setLightningAddress] = useState('');
  const [publicKey, setPublicKey] = useState('');
  const [regPrivateKey, setRegPrivateKey] = useState(''); // Private key (nsec) from registration or login
  const [rawSeed, setRawSeed] = useState(''); // Raw seed from registration (hex)

  // Challenge auth state
  const [challengeSessionId, setChallengeSessionId] = useState('');
  const [challenge, setChallenge] = useState('');
  const [token, setToken] = useState('');

  // Login state
  const [loginPrivateKey, setLoginPrivateKey] = useState('');
  const [loginToken, setLoginToken] = useState('');

  // UI / status state
  const [status, setStatus] = useState('');

  /**
   * decodeNsecToRawSeedFallback:
   * Fallback: decode an nsec string using nip19.decode.
   * Only used if no raw seed is present from registration.
   */
  function decodeNsecToRawSeedFallback(nsec) {
    try {
      const decoded = nip19.decode(nsec);
      if (decoded.type !== 'nsec') {
        throw new Error(`Not a valid nsec key. Got type: ${decoded.type}`);
      }
      console.debug("DEBUG: Fallback raw seed (uint8):", decoded.data);
      console.debug("DEBUG: Fallback raw seed (hex):", Buffer.from(decoded.data).toString("hex"));
      return decoded.data;
    } catch (e) {
      console.error("Failed to decode nsec key using nip19 fallback", e);
      throw e;
    }
  }

  // --- 1) REGISTER ---
  const handleRegister = async () => {
    if (!lightningAddress) {
      setStatus("Please enter a lightning address before registering.");
      return;
    }
    setStatus('Registering user...');
    try {
      const response = await fetch('http://localhost:8000/users/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ lightning_address: lightningAddress })
      });
      if (!response.ok) throw new Error(response.statusText);
      const data = await response.json();
      console.debug("DEBUG (Register): Response data:", data);
      setPublicKey(data.nostr_public_key);
      setRegPrivateKey(data.nostr_private_key);
      setRawSeed(data.raw_seed); // Store the raw seed (hex) from registration
      setStatus('User registered successfully!');
    } catch (error) {
      setStatus(`Error registering user: ${error.message}`);
    }
  };

  // --- 2) REQUEST CHALLENGE ---
  const handleGetChallenge = async () => {
    if (!publicKey) {
      setStatus("No public key available. Please register first.");
      return;
    }
    setStatus('Requesting challenge...');
    try {
      const url = `http://localhost:8000/auth/challenge?public_key=${publicKey}`;
      const response = await fetch(url);
      if (!response.ok) throw new Error(response.statusText);
      const data = await response.json();
      console.debug("DEBUG (Challenge): Response data:", data);
      setChallengeSessionId(data.session_id);
      setChallenge(data.challenge);
      setStatus(`Challenge received: ${data.challenge}`);
    } catch (error) {
      setStatus(`Error requesting challenge: ${error.message}`);
    }
  };

  // --- 3) SIGN & VERIFY CHALLENGE ---
  const handleVerifyChallenge = async () => {
    if (!challengeSessionId || !challenge) {
      setStatus("No challenge data available.");
      return;
    }
    if (!regPrivateKey) {
      setStatus("No private key available from registration or login.");
      return;
    }
    setStatus('Signing and verifying challenge...');
    try {
      // IMPORTANT: Use the raw seed to create a nacl signing key
      // Since we're having trouble with the SDK's signing method
      let rawSeedArray;
      if (rawSeed) {
        rawSeedArray = Buffer.from(rawSeed, "hex");
        console.debug("DEBUG: Using rawSeed from registration:", rawSeedArray.toString("hex"));
      } else {
        // Fall back to the private key
        rawSeedArray = decodeNsecToRawSeedFallback(regPrivateKey);
      }
      console.debug("DEBUG: Raw seed length =", rawSeedArray.length);
      
      // Generate key pair from raw seed using tweetnacl
      const keyPair = nacl.sign.keyPair.fromSeed(new Uint8Array(rawSeedArray));
      
      // Get the challenge bytes
      const challengeBytes = new TextEncoder().encode(challenge);
      console.debug("DEBUG: Challenge bytes:", challengeBytes);
      
      // Sign the challenge using tweetnacl
      const signature = nacl.sign.detached(challengeBytes, keyPair.secretKey);
      const signatureB64 = Buffer.from(signature).toString('base64');
      
      console.debug("DEBUG: signature (hex) =", Buffer.from(signature).toString("hex"));
      console.debug("DEBUG: signature (b64) =", signatureB64);

      // Send signature to backend for verification
      const response = await fetch('http://localhost:8000/auth/verify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: challengeSessionId,
          signature_b64: signatureB64
        }),
      });
      if (!response.ok) throw new Error(response.statusText);
      const data = await response.json();
      console.debug("DEBUG (Verify): Response data:", data);
      if (data.authenticated) {
        setToken(data.token);
        setStatus(`Signature verified! Token: ${data.token}`);
      } else {
        setStatus("Signature verification failed on server.");
      }
    } catch (error) {
      setStatus(`Error verifying challenge: ${error.message}`);
    }
  };

  // --- 4) LOGIN ---
  const handleLogin = async () => {
    if (!loginPrivateKey) {
      setStatus("Please enter your private key (nsec1...) to log in.");
      return;
    }
    setStatus("Logging in...");
    try {
      const response = await fetch('http://localhost:8000/users/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ private_key: loginPrivateKey })
      });
      if (!response.ok) throw new Error(response.statusText);
      const data = await response.json();
      console.debug("DEBUG (Login): Response data:", data);
      setPublicKey(data.nostr_public_key);
      setRegPrivateKey(loginPrivateKey);
      setLoginToken(data.id);
      setStatus(`Login successful! User ID: ${data.id}`);
    } catch (error) {
      setStatus(`Error during login: ${error.message}`);
    }
  };

  return (
    <div className="App" style={{ margin: 20 }}>
      <h2>Ayou Lighting Network Test</h2>
      <p style={{ color: 'gray' }}>Status: {status}</p>
      
      {/* Registration Section */}
      <section style={{ marginBottom: 20 }}>
        <h3>Register a User</h3>
        <label>Lightning Address: </label>
        <input
          type="text"
          value={lightningAddress}
          onChange={(e) => setLightningAddress(e.target.value)}
          placeholder="user@example.com"
          style={{ marginRight: '10px' }}
        />
        <button onClick={handleRegister}>Register User</button>
        <p>Public Key (from register): {publicKey || 'N/A'}</p>
        <p>Private Key (nsec1 from register): {regPrivateKey || 'N/A'}</p>
      </section>

      {/* Challenge Authentication Section */}
      <section style={{ marginBottom: 20 }}>
        <h3>Authenticate to Post Listing</h3>
        <button onClick={handleGetChallenge}>Request Challenge</button>
        <p>Session ID: {challengeSessionId || 'N/A'}</p>
        <p>Challenge: {challenge || 'N/A'}</p>
        <br />
        <button onClick={handleVerifyChallenge}>Sign & Verify Challenge</button>
        <p>Token (session): {token || 'N/A'}</p>
      </section>

      {/* Login Section */}
      <section style={{ marginBottom: 20 }}>
        <h3>Login</h3>
        <p>Enter your private key (nsec1) to log in:</p>
        <input
          type="text"
          value={loginPrivateKey}
          onChange={(e) => setLoginPrivateKey(e.target.value)}
          placeholder="nsec1..."
          style={{ width: '100%', marginBottom: '10px' }}
        />
        <button onClick={handleLogin}>Login</button>
        <p>User Token (ID from login): {loginToken || 'N/A'}</p>
      </section>
    </div>
  );
}

export default App;