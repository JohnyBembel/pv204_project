import React, { useEffect, useState, useContext } from 'react';
import { AuthContext } from './AuthContext';
import LogoutButton from './LogoutButton';

const MyPurchases = () => {
  const [listings, setListings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedListing, setSelectedListing] = useState(null);
  const [reviewModal, setReviewModal] = useState({ open: false, listing: null });
  const [reviewData, setReviewData] = useState({ rating: 1, comment: '' });

  const { userPublicKey } = useContext(AuthContext);

  useEffect(() => {
    if (!userPublicKey) {
      setError('No public key available.');
      setLoading(false);
      return;
    }

    const fetchPurchasedListings = async () => {
      try {
        const response = await fetch(`http://localhost:8000/listings/paid_by/${encodeURIComponent(userPublicKey)}`);
        if (!response.ok) {
          throw new Error('Error fetching purchased listings');
        }
        const data = await response.json();
        setListings(data);
        setLoading(false);
      } catch (err) {
        setError(err.message);
        setLoading(false);
      }
    };

    fetchPurchasedListings();
  }, [userPublicKey]);

  const openModal = (listing) => {
    setSelectedListing(listing);
  };

  const closeModal = () => {
    setSelectedListing(null);
  };

  const openReviewModal = (listing) => {
    setReviewModal({ open: true, listing });
  };

  const closeReviewModal = () => {
    setReviewModal({ open: false, listing: null });
    setReviewData({ rating: 1, comment: '' });
  };

  const submitReview = async () => {
    if (!reviewData.comment.trim()) {
      alert('Please provide a comment.');
      return;
    }

    try {
      const token = localStorage.getItem('authToken'); // Retrieve the token from local storage or another source
      if (!token) {
        alert('Session token is missing. Please log in again.');
        return;
      }

      const url = `http://localhost:8000/reviews?session-token=${encodeURIComponent(token)}`;
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          transaction_id: reviewModal.listing.id,
          rating: reviewData.rating,
          comment: reviewData.comment,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to submit review');
      }

      alert('Review submitted successfully!');
      closeReviewModal();
    } catch (err) {
      alert(`Error: ${err.message}`);
    }
  };

  return (
    <>
    <header style={{ display: 'flex', justifyContent: 'space-between', padding: '10px', background: '#eee' }}>
    <h1>Nostr-based marketplace</h1>
    <LogoutButton />
  </header>
    <div style={{ padding: '20px' }}>
      <h2>My Purchases</h2>
      {loading && <p>Loading your purchased listings...</p>}
      {error && <p style={{ color: 'red' }}>Error: {error}</p>}
      {(!loading && listings.length === 0) && <p>You haven’t bought anything yet.</p>}

      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '20px' }}>
        {listings.map((listing) => (
          <div
            key={listing.id}
            style={{
              border: '1px solid #ccc',
              borderRadius: '8px',
              padding: '16px',
              width: '300px',
              boxShadow: '2px 2px 5px rgba(0,0,0,0.1)',
              backgroundColor: listing.status === "ended" ? "#ffd6d6" : "#fff"
            }}
          >
            {listing.image && listing.image.url && (
              <img
                src={listing.image.url}
                alt="Listing"
                style={{ width: '100%', borderRadius: '4px', marginBottom: '8px' }}
              />
            )}
            <h3>{listing.title}</h3>
            <p style={{ fontWeight: 'bold' }}>{listing.price} SATs</p>
            <p>{(listing.description || "").substring(0, 100)}...</p>
            <button onClick={() => openModal(listing)}>View Details</button>
            <button onClick={() => openReviewModal(listing)} style={{ marginTop: '10px' }}>
              Leave Review
            </button>
          </div>
        ))}
      </div>

      {selectedListing && (
        <div
          onClick={closeModal}
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
            {selectedListing.image && selectedListing.image.url && (
              <img
                src={selectedListing.image.url}
                alt="Listing"
                style={{ width: '100%', borderRadius: '4px', marginBottom: '16px' }}
              />
            )}
            <h2>{selectedListing.title}</h2>
            <p><strong>Price:</strong> {selectedListing.price} SATs</p>
            <p><strong>Description:</strong> {selectedListing.description}</p>
            <p><strong>Condition:</strong> {selectedListing.condition}</p>
            <p><strong>Status:</strong> {selectedListing.status}</p>
          </div>
        </div>
      )}

      {reviewModal.open && (
        <div
          onClick={closeReviewModal}
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
              position: 'relative'
            }}
          >
            <button
              onClick={closeReviewModal}
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
            <h3>Leave a Review for {reviewModal.listing.title}</h3>
            <label>
              Rating:
              <select
                value={reviewData.rating}
                onChange={(e) => setReviewData({ ...reviewData, rating: parseInt(e.target.value) })}
              >
                {[1, 2, 3, 4, 5].map((rating) => (
                  <option key={rating} value={rating}>{rating}</option>
                ))}
              </select>
            </label>
            <br />
            <label>
              Comment:
              <textarea
                value={reviewData.comment}
                onChange={(e) => setReviewData({ ...reviewData, comment: e.target.value })}
                style={{ width: '100%', height: '100px', marginTop: '10px' }}
              />
            </label>
            <br />
            <button onClick={submitReview} style={{ marginTop: '10px' }}>Submit Review</button>
          </div>
        </div>
      )}
    </div>
    </>
  );
};

export default MyPurchases;