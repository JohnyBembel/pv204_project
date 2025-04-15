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
  
  // Additional state for registration feedback
  const [registering, setRegistering] = useState(false);
  
  // New state for profile check popup
  const [showProfileModal, setShowProfileModal] = useState(false);
  
  // Auth context for global auth state
  const { setIsLoggedIn, setAuthToken, setUserPublicKey } = useContext(AuthContext);
  const navigate = useNavigate();
  
  // Use a default lightning address for registration.
  const defaultLightningAddress = "user@example.com";

  // ------------- REGISTRATION -------------
  const handleRegister = async () => {
    setRegistering(true);
    try {
      const response = await fetch('http://localhost:8000/users/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ lightning_address: defaultLightningAddress })
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
    } finally {
      setRegistering(false);
    }
  };

  // ------------- LOGIN -------------
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

  // ------------- REQUEST CHALLENGE -------------
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

  // ------------- AUTOMATIC CHALLENGE VERIFICATION & PROFILE CHECK -------------
  const handleVerifyChallenge = async () => {
    if (!challengeSessionId || !challenge || !regPrivateKey) return;
    try {
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
        // Before authenticating, check if a profile exists using the public key.
        const profileUrl = `http://localhost:8000/users/nostr-profile/${encodeURIComponent(publicKey)}`;
        const profileResp = await fetch(profileUrl);
        if (!profileResp.ok) {
          throw new Error("Failed to fetch profile.");
        }
        const profileData = await profileResp.json();
        
        // If no profile exists, show popup with registration keys.
        if (!profileData || Object.keys(profileData).length === 0) {
          setShowProfileModal(true);
          return; // Stop authentication until a profile is created.
        }
        
        // If profile exists, finish authentication.
        setToken(data.token);
        localStorage.setItem('authToken', data.token);
        localStorage.setItem('userPublicKey', publicKey);
        setAuthToken(data.token);
        setUserPublicKey(publicKey);
        setIsLoggedIn(true);
        setChallengeVerified(true);
        navigate('/home');
      } else {
        alert("Server failed to verify the signature.");
      }
    } catch (error) {
      alert(`Error during challenge verification: ${error.message}`);
    }
  };

  useEffect(() => {
    if (challengeRequested && challenge && challengeSessionId && !challengeVerified) {
      handleVerifyChallenge();
    }
  }, [challenge, challengeSessionId, challengeRequested, challengeVerified]);

  return (
    <div style={{ margin: '20px' }}>
      <h2>Nostr Authentication</h2>
      
      {/* Registration Section */}
      <section style={{ marginBottom: '20px' }}>
        <h3>Register</h3>
        <button onClick={handleRegister} disabled={registering}>
          {registering ? "Registering... please wait" : "Register"}
        </button>
      </section>
      
      {/* Login Section */}
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
      
      {/* Profile creation popup modal */}
      {showProfileModal && (
        <div
          onClick={() => setShowProfileModal(false)}
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            width: '100%',
            height: '100%',
            backgroundColor: 'rgba(0,0,0,0.5)',
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center'
          }}
        >
          <div
            onClick={(e) => e.stopPropagation()}
            style={{
              background: '#fff',
              padding: '20px',
              borderRadius: '8px',
              width: '400px',
              textAlign: 'center',
              position: 'relative'
            }}
          >
            <button
              onClick={() => setShowProfileModal(false)}
              style={{
                position: 'absolute',
                top: '10px',
                right: '10px',
                background: 'transparent',
                border: 'none',
                fontSize: '24px',
                cursor: 'pointer'
              }}
            >
              &times;
            </button>
            <h3>Create Profile Required</h3>
            <p>You must create a Nostr profile before proceeding.</p>
            <div style={{ marginTop: '10px', background: '#f0f0f0', padding: '10px', borderRadius: '4px', textAlign: 'left' }}>
              <p><strong>Your Public Key:</strong> {publicKey}</p>
              <p><strong>Your Private Key:</strong> {regPrivateKey}</p>
            </div>
            <p>Please navigate to the <url>www.primal.net</url></p>
            <p>Log in there with above generated private key and set up your profile.</p>
          </div>
        </div>
      )}
    </div>
  );
};

export default NostrAuth;