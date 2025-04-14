import React, { useState, useContext, useEffect } from 'react';
import './App.css';
import nacl from 'tweetnacl';
import { nip19 } from 'nostr-tools';
import { Buffer } from 'buffer';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
// Import WASM loader and other necessary items from @rust-nostr/nostr-sdk
import { loadWasmSync } from '@rust-nostr/nostr-sdk';
import { AuthProvider, AuthContext } from './AuthContext';
import ProtectedRoute from './ProtectedRoute';

window.Buffer = Buffer;
loadWasmSync();

function NostrAuth() {
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

  // Auth context
  const { setIsLoggedIn, setAuthToken, setUserPublicKey } = useContext(AuthContext);
  
  // Function to validate stored tokens
  const validateToken = async (token) => {
    try {
      const response = await fetch('http://localhost:8000/auth/validate', {
        headers: { 'session-token': token }
      });
      
      if (!response.ok) {
        // Token is invalid or expired, clear localStorage
        localStorage.removeItem('authToken');
        localStorage.removeItem('userPublicKey');
        setToken('');
        setPublicKey('');
        setAuthToken('');
        setUserPublicKey('');
        setIsLoggedIn(false);
        setStatus('Your session has expired. Please login again.');
      } else {
        setStatus('You are authenticated. Token is valid.');
      }
    } catch (error) {
      setStatus('Error validating token. Please try again.');
    }
  };

  // Check for existing authentication on component mount
  useEffect(() => {
    const savedToken = localStorage.getItem('authToken');
    const savedPublicKey = localStorage.getItem('userPublicKey');
    
    if (savedToken && savedPublicKey) {
      setToken(savedToken);
      setPublicKey(savedPublicKey);
      
      setAuthToken(savedToken);
      setUserPublicKey(savedPublicKey);
      setIsLoggedIn(true);
      
      validateToken(savedToken);
    }
  }, [setAuthToken, setUserPublicKey, setIsLoggedIn]);

  /**
   * Decode a Nostr private key (nsec format) to raw seed bytes
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
      // Get raw seed from either stored seed or private key
      let rawSeedArray;
      if (rawSeed) {
        rawSeedArray = Buffer.from(rawSeed, "hex");
      } else {
        rawSeedArray = decodeNsecToRawSeedFallback(regPrivateKey);
      }
      
      // Generate key pair from raw seed using tweetnacl
      const keyPair = nacl.sign.keyPair.fromSeed(new Uint8Array(rawSeedArray));
      
      // Get the challenge bytes and sign them
      const challengeBytes = new TextEncoder().encode(challenge);
      const signature = nacl.sign.detached(challengeBytes, keyPair.secretKey);
      const signatureB64 = Buffer.from(signature).toString('base64');

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
      
      if (data.authenticated) {
        setToken(data.token);
        
        localStorage.setItem('authToken', data.token);
        localStorage.setItem('userPublicKey', publicKey);
        
        // Set login state in the context
        setAuthToken(data.token);
        setUserPublicKey(publicKey);
        setIsLoggedIn(true);
        
        setStatus(`Authentication successful! You're now logged in.`);
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
      setPublicKey(data.nostr_public_key);
      setRegPrivateKey(loginPrivateKey);
      setLoginToken(data.id);
      setStatus(`Login successful! User ID: ${data.id}`);
      
      // After successful login, request a challenge to get an auth token
      handleGetChallenge();
    } catch (error) {
      setStatus(`Error during login: ${error.message}`);
    }
  };

  return (
    <div className="App" style={{ margin: 20 }}>
      <h2>Ayou Lightning Network Test</h2>
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

// Dashboard component that will be protected
function Dashboard() {
  const { userPublicKey, logout } = useContext(AuthContext);
  
  return (
    <div style={{ margin: 20 }}>
      <h2>Welcome to Your Dashboard</h2>
      <p>You are logged in with public key: {userPublicKey}</p>
      <button onClick={logout}>Logout</button>
    </div>
  );
}

// Home component
function Home() {
  const { isLoggedIn } = useContext(AuthContext);
  
  return (
    <div style={{ margin: 20 }}>
      <h1>Welcome to Ayou Lightning Network</h1>
      {isLoggedIn ? (
        <div>
          <p>You are logged in. Go to your <a href="/dashboard">dashboard</a>.</p>
        </div>
      ) : (
        <div>
          <p>Please <a href="/auth">log in or register</a> to continue.</p>
        </div>
      )}
    </div>
  );
}

function App() {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/auth" element={<NostrAuth />} />
          <Route 
            path="/dashboard" 
            element={
              <ProtectedRoute element={<Dashboard />} />
            } 
          />
          <Route path="*" element={<Navigate to="/" />} />
        </Routes>
      </Router>
    </AuthProvider>
  );
}

export default App;