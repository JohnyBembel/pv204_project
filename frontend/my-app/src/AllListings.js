import React, { useEffect, useState, useContext } from 'react';
import { AuthContext } from './AuthContext';
import LogoutButton from './LogoutButton';

const AllListings = () => {
  const [listings, setListings] = useState([]);
  const [sellerProfiles, setSellerProfiles] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedListing, setSelectedListing] = useState(null);
  
  // Payment-related states 
  const [showPayModal, setShowPayModal] = useState(false);
  const [invoiceStr, setInvoiceStr] = useState("");
  const [buyerNwc, setBuyerNwc] = useState("");
  const [profile, setProfile] = useState(null);

  const { userPublicKey } = useContext(AuthContext);

  // 1) Fetch all listings on component mount
  useEffect(() => {
    const fetchListings = async () => {
      try {
        const response = await fetch('http://localhost:8000/listings');
        if (!response.ok) {
          throw new Error("Error fetching listings");
        }
        const data = await response.json();
        setListings(data);
        setLoading(false);
      } catch (err) {
        setError(err.message);
        setLoading(false);
      }
    };
    fetchListings();
  }, []);

  // 2) Once listings are fetched, gather unique pubkeys and fetch each seller's profile.
  useEffect(() => {
    const fetchSellerProfiles = async () => {
      const profilesMap = {};
      const uniquePubkeys = Array.from(new Set(listings.map((l) => l.pubkey).filter(Boolean)));

      await Promise.all(
        uniquePubkeys.map(async (pubkey) => {
          try {
            const profileUrl = `http://localhost:8000/users/nostr-profile/${encodeURIComponent(pubkey)}`;
            const resp = await fetch(profileUrl);
            if (resp.ok) {
              const data = await resp.json();
              profilesMap[pubkey] = data;
            }
          } catch (e) {
            console.error(`Failed to fetch profile for ${pubkey}:`, e);
          }
        })
      );

      setSellerProfiles(profilesMap);
    };

    if (listings.length > 0) {
      fetchSellerProfiles();
    }
  }, [listings]);

  // 3) Open the modal for a clicked listing
  const openModal = (listing) => {
    setSelectedListing(listing);
    setProfile(null);
    setInvoiceStr("");
    setBuyerNwc("");
    setShowPayModal(false);
  };

  // 4) Close the modal
  const closeModal = () => {
    setSelectedListing(null);
    setProfile(null);
    setInvoiceStr("");
    setBuyerNwc("");
    setShowPayModal(false);
  };

  // 5) Payment-related logic
  const handlePay = async (listing) => {
    try {
      if (!listing.pubkey) {
        throw new Error("No public key available for this listing.");
      }
      // Fetch seller profile to retrieve LN address (lud16)
      const profileUrl = `http://localhost:8000/users/nostr-profile/${encodeURIComponent(listing.pubkey)}`;
      const profileResp = await fetch(profileUrl);
      if (!profileResp.ok) {
        throw new Error("Failed to fetch seller profile.");
      }
      const profileData = await profileResp.json();
      const sellerLnAddress = profileData.lud16;
      if (!sellerLnAddress) {
        throw new Error("Seller's LN address (lud16) not found in profile.");
      }
      // Create invoice
      const invoiceUrl = `http://localhost:8000/invoices/create_invoice/?seller_ln_address=${encodeURIComponent(sellerLnAddress)}&amount=${encodeURIComponent(listing.price)}&description=${encodeURIComponent(listing.title)}`;
      const invoiceResponse = await fetch(invoiceUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
      });
      if (!invoiceResponse.ok) {
        throw new Error("Failed to create invoice.");
      }
      const invoiceData = await invoiceResponse.json();
      const invStr = typeof invoiceData === "string" ? invoiceData : invoiceData.invoice;
      if (!invStr) {
        throw new Error("No invoice string returned.");
      }
      setInvoiceStr(invStr);
      setShowPayModal(true);
    } catch (err) {
      alert("Error in pay process: " + err.message);
    }
  };

  const handleSubmitPay = async () => {
    try {
      if (!buyerNwc || !invoiceStr) {
        alert("Please enter your buyer NWC string.");
        return;
      }
      // Pay invoice
      const payUrl = `http://localhost:8000/invoices/pay_invoice/?nwc_buyer_string=${encodeURIComponent(buyerNwc)}&invoicestr=${encodeURIComponent(invoiceStr)}`;
      const payResp = await fetch(payUrl);
      if (!payResp.ok) {
        throw new Error("Failed to pay invoice");
      }
      const paymentResult = await payResp.json();
      alert("Payment result: " + JSON.stringify(paymentResult));

      // Update listing to ended and set paid_by
      if (selectedListing && userPublicKey) {
        const listingId = selectedListing.id;
        const updateUrl = `http://localhost:8000/listings/${listingId}`;
        const updatePayload = {
          status: "ended",
          paid_by: userPublicKey,
        };
        const updateResp = await fetch(updateUrl, {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(updatePayload),
        });
        if (!updateResp.ok) {
          throw new Error("Failed to update listing after payment.");
        }
        const updatedListing = await updateResp.json();
        console.log("Listing updated:", updatedListing);
        alert(`Listing status updated to "ended" and paid_by set to ${userPublicKey}.`);
      }

      setShowPayModal(false);
      setSelectedListing(null);
    } catch (error) {
      alert("Error paying invoice or updating listing: " + error.message);
    }
  };

  return (
    <>
      <header style={{ display: 'flex', justifyContent: 'space-between', padding: '10px', background: '#eee' }}>
        <h1>Nostr Marketplace</h1>
        <LogoutButton />
      </header>
      
      <div style={{ padding: '20px' }}>
        <h2>All Listings</h2>
        {loading && <p>Loading listings...</p>}
        {error && <p style={{ color: 'red' }}>Error: {error}</p>}
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '20px' }}>
          {listings.map((listing) => (
            <div
              key={listing.id}
              onClick={() => openModal(listing)}
              style={{
                border: '1px solid #ccc',
                borderRadius: '8px',
                padding: '16px',
                width: '300px',
                cursor: 'pointer',
                boxShadow: '2px 2px 5px rgba(0,0,0,0.1)',
                backgroundColor: listing.status === "ended" ? "#ffcccc" : "#fff"
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
            {/* Display seller profile info if available */}
                {listing.pubkey && sellerProfiles[listing.pubkey] && (
                <div style={{ fontStyle: 'italic', fontSize: '0.9em', marginTop: '6px' }}>
                  Seller: {sellerProfiles[listing.pubkey].display_name || sellerProfiles[listing.pubkey].name || listing.pubkey}
                </div>
              )}
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
              {selectedListing.category_id && (
                <p><strong>Category ID:</strong> {selectedListing.category_id}</p>
              )}
              {selectedListing.quantity && (
                <p><strong>Quantity:</strong> {selectedListing.quantity}</p>
              )}
              {selectedListing.shipping_price !== undefined && (
                <p><strong>Shipping Price:</strong> {selectedListing.shipping_price} SATs</p>
              )}
              {selectedListing.tags && selectedListing.tags.length > 0 && (
                <p><strong>Tags:</strong> {selectedListing.tags.join(', ')}</p>
              )}
              
              {/* Show seller info in modal if we have a profile. */}
              {selectedListing.pubkey && sellerProfiles[selectedListing.pubkey] && (
                <div style={{ marginTop: '20px', padding: '10px', background: '#f9f9f9', borderRadius: '4px' }}>
                  <h4>Seller Info</h4>
                  <p>
                    <strong>Display Name: </strong>
                    {sellerProfiles[selectedListing.pubkey].display_name 
                      || sellerProfiles[selectedListing.pubkey].name 
                      || selectedListing.pubkey}
                  </p>
                  {sellerProfiles[selectedListing.pubkey].lud16 && (
                    <p>
                      <strong>Lightning Address: </strong>
                      {sellerProfiles[selectedListing.pubkey].lud16}
                    </p>
                  )}
                </div>
              )}
              
              {selectedListing.status !== "ended" && (
                <div style={{ marginTop: '20px', display: 'flex', justifyContent: 'center' }}>
                  <button onClick={() => handlePay(selectedListing)}>
                    Pay
                  </button>
                </div>
              )}
              
              {selectedListing.status === "ended" && selectedListing.paid_by && (
                <p style={{ color: "green" }}>
                  <strong>Paid by:</strong> {selectedListing.paid_by}
                </p>
              )}
            </div>
          </div>
        )}

        {showPayModal && (
          <div
            onClick={() => setShowPayModal(false)}
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
                onClick={() => setShowPayModal(false)}
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
              <h3>Enter Buyer NWC String</h3>
              <input
                type="text"
                value={buyerNwc}
                onChange={(e) => setBuyerNwc(e.target.value)}
                placeholder="Buyer NWC String"
                style={{ width: '100%', padding: '8px', marginBottom: '20px' }}
              />
              <button onClick={handleSubmitPay}>Pay</button>
            </div>
          </div>
        )}
      </div>
    </>
  );
};

export default AllListings;
