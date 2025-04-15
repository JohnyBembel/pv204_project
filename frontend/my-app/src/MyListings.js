import React, { useEffect, useState, useContext } from 'react';
import { AuthContext } from './AuthContext';

const MyListings = () => {
  const [listings, setListings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedListing, setSelectedListing] = useState(null);

  // Get current user's public key from AuthContext
  const { userPublicKey } = useContext(AuthContext);

  // Fetch all listings and filter them for the logged-in user
  useEffect(() => {
    const fetchListings = async () => {
      try {
        const response = await fetch('http://localhost:8000/listings');
        if (!response.ok) {
          throw new Error('Error fetching listings');
        }
        const data = await response.json();
        // Filter listings by comparing seller info with the logged-in user's public key
        const myListings = data.filter(listing => 
          userPublicKey &&
          listing.seller &&
          listing.seller.nostr_public_key === userPublicKey
        );
        setListings(myListings);
        setLoading(false);
      } catch (err) {
        setError(err.message);
        setLoading(false);
      }
    };

    fetchListings();
  }, [userPublicKey]);

  // Open modal with detailed info
  const openModal = (listing) => {
    setSelectedListing(listing);
  };

  // Close modal
  const closeModal = () => {
    setSelectedListing(null);
  };

  return (
    <div style={{ padding: '20px' }}>
      <h2>My Listings</h2>
      {loading && <p>Loading your listings...</p>}
      {error && <p style={{ color: 'red' }}>Error: {error}</p>}
      {(!loading && listings.length === 0) && <p>No listings found for you.</p>}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '20px' }}>
        {listings.map(listing => (
          <div
            key={listing.id}
            onClick={() => openModal(listing)}
            style={{
              border: '1px solid #ccc',
              borderRadius: '8px',
              padding: '16px',
              width: '300px',
              cursor: 'pointer',
              boxShadow: '2px 2px 5px rgba(0,0,0,0.1)'
            }}
          >
            {listing.images && listing.images.length > 0 && (
              <img
                src={listing.images[0].url}
                alt="Listing"
                style={{ width: '100%', borderRadius: '4px', marginBottom: '8px' }}
              />
            )}
            <h3>{listing.title}</h3>
            <p style={{ fontWeight: 'bold' }}>${listing.price}</p>
            <p>{listing.description.substring(0, 100)}...</p>
          </div>
        ))}
      </div>

      {/* Modal for listing details */}
      {selectedListing && (
        <div
          onClick={closeModal}  // Clicking on the overlay will close the modal
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
            onClick={(e) => e.stopPropagation()} // Prevent clicks inside the modal from closing it
            style={{
              background: '#fff',
              padding: '20px',
              borderRadius: '8px',
              width: '80%',
              maxHeight: '90%',
              overflowY: 'auto',
              position: 'relative'
            }}
          >
            <button
              onClick={closeModal}
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
            {selectedListing.images && selectedListing.images.length > 0 && (
              <img
                src={selectedListing.images[0].url}
                alt="Listing"
                style={{ width: '100%', borderRadius: '4px', marginBottom: '16px' }}
              />
            )}
            <h2>{selectedListing.title}</h2>
            <p><strong>Price:</strong> ${selectedListing.price}</p>
            <p><strong>Description:</strong> {selectedListing.description}</p>
            <p><strong>Condition:</strong> {selectedListing.condition}</p>
            <p><strong>Category ID:</strong> {selectedListing.category_id}</p>
            <p><strong>Quantity:</strong> {selectedListing.quantity}</p>
            <p><strong>Shipping Price:</strong> ${selectedListing.shipping_price}</p>
            {selectedListing.tags && selectedListing.tags.length > 0 && (
              <p><strong>Tags:</strong> {selectedListing.tags.join(', ')}</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default MyListings;
