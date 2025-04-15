import React from 'react';
import { useNavigate } from 'react-router-dom';
import LogoutButton from './LogoutButton';

const HomePage = () => {
  const navigate = useNavigate();

  const handleCreateListing = () => navigate('/listings/create');
  const handleBoughtListings = () => navigate('/listings/bought');
  const handleMyListings = () => navigate('/listings/mine');
  const handleAllListings = () => navigate('/listings/all');
  const handleInvoices= () => navigate('/invoices');
  const handleAllSellers = () => navigate('/sellers/all');

  return (
    <>
    <header style={{ display: 'flex', justifyContent: 'space-between', padding: '10px', background: '#eee' }}>
    <h1>Nostr-based marketplace</h1>
    <LogoutButton />
  </header>
    <div style={{ margin: '20px' }}>
      <h2>Welcome Home</h2>
      <p>Choose an action:</p>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', maxWidth: '200px' }}>
        <button onClick={handleCreateListing}>Create a Listing</button>
        <button onClick={handleBoughtListings}>My bought listings</button>
        <button onClick={handleMyListings}>My Listings</button>
        <button onClick={handleAllListings}>All Listings</button>
        <button onClick={handleAllSellers}>All sellers</button>
      </div>
    </div>
    </>
  );
};

export default HomePage;