import React, { useState, useContext, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import nacl from 'tweetnacl';
import { nip19 } from 'nostr-tools';
import { Buffer } from 'buffer';
import { loadWasmSync } from '@rust-nostr/nostr-sdk';
import { AuthContext } from './AuthContext';

window.Buffer = Buffer;
loadWasmSync();

/**
 * Helper function to decode a Nostr nsec key to a raw seed byte array.
 */
function decodeNsecToRawSeedFallback(nsec) {
  try {
    const decoded = nip19.decode(nsec);
    if (decoded.type !== 'nsec') {
      throw new Error(`Not a valid nsec key. Got type: ${decoded.type}`);
    }
    return decoded.data;
  } catch (e) {
    throw e;
  }
}

const NostrAuth = () => {
  // Registration states
  const [lightningAddress, setLightningAddress] = useState('');
  const [publicKey, setPublicKey] = useState('');
  const [regPrivateKey, setRegPrivateKey] = useState('');
  const [rawSeed, setRawSeed] = useState('');
  
  // Login state (for text input)
  const [loginPrivateKey, setLoginPrivateKey] = useState('');
  
  // Challenge & session states
  const [challengeSessionId, setChallengeSessionId] = useState('');
  const [challenge, setChallenge] = useState('');
  const [token, setToken] = useState('');
  
  // Flags for controlling the automatic flow
  const [challengeRequested, setChallengeRequested] = useState(false);
  const [challengeVerified, setChallengeVerified] = useState(false);
  
  // Auth context for global auth state
  const { setIsLoggedIn, setAuthToken, setUserPublicKey } = useContext(AuthContext);
  const navigate = useNavigate();
  
  // ------------- REGISTRATION ------------- //
  const handleRegister = async () => {
    if (!lightningAddress) {
      alert("Please enter a lightning address before registering.");
      return;
    }
    try {
      const response = await fetch('http://localhost:8000/users/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ lightning_address: lightningAddress })
      });
      if (!response.ok) throw new Error(response.statusText);
      const data = await response.json();
      setPublicKey(data.nostr_public_key);
      setRegPrivateKey(data.nostr_private_key);
      setRawSeed(data.raw_seed); // Save raw seed as hex
      
      // Automatically request a challenge once registered
      handleGetChallenge(data.nostr_public_key);
    } catch (error) {
      alert(`Error during registration: ${error.message}`);
    }
  };

  // ------------- LOGIN ------------- //
  const handleLogin = async (privateKey) => {
    if (!privateKey) {
      alert("Please enter your nsec key to log in.");
      return;
    }
    try {
      const response = await fetch('http://localhost:8000/users/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ private_key: privateKey })
      });
      if (!response.ok) throw new Error(response.statusText);
      const data = await response.json();
      setPublicKey(data.nostr_public_key);
      setRegPrivateKey(privateKey);
      
      // Automatically request a challenge after login
      handleGetChallenge(data.nostr_public_key);
    } catch (error) {
      alert(`Login error: ${error.message}`);
    }
  };

  // ------------- REQUEST CHALLENGE ------------- //
  const handleGetChallenge = async (pubKey) => {
    if (!pubKey) {
      alert("Public key is not available.");
      return;
    }
    try {
      const url = `http://localhost:8000/auth/challenge?public_key=${pubKey}`;
      const response = await fetch(url);
      if (!response.ok) throw new Error(response.statusText);
      const data = await response.json();
      setChallengeSessionId(data.session_id);
      setChallenge(data.challenge);
      setChallengeRequested(true);
    } catch (error) {
      alert(`Error requesting challenge: ${error.message}`);
    }
  };

  // ------------- AUTOMATIC CHALLENGE VERIFICATION ------------- //
  const handleVerifyChallenge = async () => {
    if (!challengeSessionId || !challenge || !regPrivateKey) return;
    try {
      // Use rawSeed if available; otherwise decode the private key to get the seed
      const rawSeedArray = rawSeed
        ? Buffer.from(rawSeed, 'hex')
        : Buffer.from(decodeNsecToRawSeedFallback(regPrivateKey));
      
      const keyPair = nacl.sign.keyPair.fromSeed(new Uint8Array(rawSeedArray));
      const challengeBytes = new TextEncoder().encode(challenge);
      const signature = nacl.sign.detached(challengeBytes, keyPair.secretKey);
      const signatureB64 = Buffer.from(signature).toString('base64');

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
      
      if (data.authenticated) {
        setToken(data.token);
        localStorage.setItem('authToken', data.token);
        localStorage.setItem('userPublicKey', publicKey);
        setAuthToken(data.token);
        setUserPublicKey(publicKey);
        setIsLoggedIn(true);
        setChallengeVerified(true);
        
        // Redirect automatically to the home page after successful authentication
        navigate('/home');
      } else {
        alert("Server failed to verify the signature.");
      }
    } catch (error) {
      alert(`Error during challenge verification: ${error.message}`);
    }
  };

  // Automatically verify the challenge once it is requested and available
  useEffect(() => {
    if (challengeRequested && challenge && challengeSessionId && !challengeVerified) {
      handleVerifyChallenge();
    }
    // Note: handleVerifyChallenge is not included in dependencies intentionally to avoid repeated calls.
  }, [challenge, challengeSessionId, challengeRequested, challengeVerified]);

  return (
    <div style={{ margin: '20px' }}>
      <h2>Nostr Authentication</h2>
      
      {/* Registration Section */}
      <section style={{ marginBottom: '20px' }}>
        <h3>Register</h3>
        <input
          type="text"
          value={lightningAddress}
          onChange={(e) => setLightningAddress(e.target.value)}
          placeholder="Lightning address (user@example.com)"
          style={{ marginRight: '10px' }}
        />
        <button onClick={handleRegister}>Register</button>
      </section>
      
      {/* Login Section with Text Field */}
      <section style={{ marginBottom: '20px' }}>
        <h3>Login</h3>
        <p>Enter your private key (nsec1):</p>
        <input
          type="text"
          value={loginPrivateKey}
          onChange={(e) => setLoginPrivateKey(e.target.value)}
          placeholder="nsec1..."
          style={{ width: '100%', marginBottom: '10px' }}
        />
        <button onClick={() => handleLogin(loginPrivateKey)}>Login</button>
      </section>
      
      {/* Debugging information (optional) */}
      <div>
        <p>Public Key: {publicKey}</p>
        <p>Challenge: {challenge}</p>
        <p>Token: {token}</p>
      </div>
    </div>
  );
};

export default NostrAuth;
