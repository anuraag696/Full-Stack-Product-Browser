const API_BASE_URL = 'https://full-stack-product-browser.onrender.com/api/products';
const LIMIT = 24; // Fetching clean multiples of 4 for a perfect grid layout

let nextCursor = null;
let currentCategory = '';

// Core DOM Elements
const productGrid = document.getElementById('productGrid');
const loadMoreBtn = document.getElementById('loadMoreBtn');
const loadingSpinner = document.getElementById('loadingSpinner');
const noMoreContainer = document.getElementById('noMoreContainer');
const categoryFilter = document.getElementById('categoryFilter');

// Modal DOM Elements
const detailsModal = document.getElementById('detailsModal');
const modalContent = document.getElementById('modalContent');
const closeModalBtn = document.getElementById('closeModalBtn');

// Helper to structure currency display format cleanly
const formatPrice = (price) => {
    return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(price);
};

// Fetch products from backend API
async function fetchProducts(resetGrid = false) {
    if (resetGrid) {
        productGrid.innerHTML = '';
        nextCursor = null;
        loadMoreBtn.classList.add('hidden');
        noMoreContainer.classList.add('hidden');
    }

    loadingSpinner.classList.remove('hidden');
    loadMoreBtn.classList.add('hidden');

    try {
        // Build dynamic query parameters
        let url = `${API_BASE_URL}?limit=${LIMIT}`;
        if (currentCategory) {
            url += `&category=${encodeURIComponent(currentCategory)}`;
        }
        if (nextCursor) {
            url += `&cursor=${encodeURIComponent(nextCursor)}`;
        }

        let response;
        try {
            response = await fetch(url);
        } catch (networkError) {
            throw new Error(
                'Network error: Unable to reach the backend API. Check your connection or ensure the server is running.'
            );
        }

        if (!response.ok) {
            let errorDetail = `HTTP ${response.status}`;
            try {
                const errorBody = await response.json();
                if (errorBody.detail) {
                    errorDetail += `: ${errorBody.detail}`;
                }
            } catch (_) {
                errorDetail += `: ${response.statusText || 'Unknown error'}`;
            }
            throw new Error(errorDetail);
        }

        let result;
        try {
            result = await response.json();
        } catch (parseError) {
            throw new Error('Failed to parse server response. The API returned invalid JSON.');
        }

        if (!result.data || !Array.isArray(result.data)) {
            throw new Error('Unexpected API response format: missing or invalid "data" field.');
        }

        // Render current page batch
        renderProducts(result.data);

        // Track the cursor for the next batch segment
        nextCursor = result.next_cursor;

        // Toggle interface states based on payload presence
        if (result.has_more && nextCursor) {
            loadMoreBtn.classList.remove('hidden');
        } else if (result.data.length > 0) {
            noMoreContainer.classList.remove('hidden');
        } else if (resetGrid) {
            productGrid.innerHTML = `
                <div class="col-span-full text-center py-12 text-gray-400 italic">
                    No products found matching this filter combo.
                </div>
            `;
        }
    } catch (error) {
        console.error('Product fetch failed:', error);
        const errorMessage = error.message || 'An unexpected error occurred.';
        productGrid.innerHTML += `
            <div class="col-span-full text-center py-4 text-red-500 font-medium">
                ${errorMessage}
            </div>
        `;
        // Keep the Load More button visible for retry if this was a pagination fetch
        if (!resetGrid && nextCursor) {
            loadMoreBtn.classList.remove('hidden');
        }
    } finally {
        loadingSpinner.classList.add('hidden');
    }
}

// Render products into clean grid elements dynamically
function renderProducts(products) {
    products.forEach(product => {
        const dateObj = new Date(product.created_at);
        const formattedDate = dateObj.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
        const pricingString = formatPrice(product.price);

        const card = document.createElement('div');
        card.className = 'bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden hover:shadow-md transition duration-200 flex flex-col justify-between';

        card.innerHTML = `
            <div class="p-5">
                <div class="flex justify-between items-start gap-2 mb-2">
                    <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-50 text-blue-800">
                        ${product.category}
                    </span>
                    <span class="text-xs text-gray-400 font-mono">#${product.id}</span>
                </div>
                <h3 class="font-semibold text-gray-800 text-base mb-1 line-clamp-2">${product.name}</h3>
                <p class="text-xs text-gray-400">Added ${formattedDate}</p>
            </div>
            <div class="px-5 py-4 bg-gray-50 border-t border-gray-100 flex items-center justify-between">
                <span class="text-lg font-bold text-gray-900">${pricingString}</span>
                <button class="view-details-btn text-xs font-medium text-blue-600 hover:text-blue-700 transition">View Details &rarr;</button>
            </div>
        `;

        // Direct event attachment ensures each distinct card points to its metadata scope
        card.querySelector('.view-details-btn').addEventListener('click', () => {
            openModal(product, formattedDate, pricingString);
        });

        productGrid.appendChild(card);
    });
}

// Open active modal window with subtle scale & opacity ease transition
function openModal(product, dateStr, priceStr) {
    document.getElementById('modalCategory').innerText = product.category;
    document.getElementById('modalName').innerText = product.name;
    document.getElementById('modalId').innerText = `#${product.id}`;
    document.getElementById('modalDate').innerText = dateStr;
    document.getElementById('modalPrice').innerText = priceStr;

    // Reveal container layout overlay frame
    detailsModal.classList.remove('hidden');

    // Tiny timeout enables the browser to catch CSS animation entry frames smoothly
    setTimeout(() => {
        modalContent.classList.remove('scale-95', 'opacity-0');
        modalContent.classList.add('scale-100', 'opacity-100');
    }, 20);
}

// Smoothly retract active modal elements 
function closeModal() {
    modalContent.classList.remove('scale-100', 'opacity-100');
    modalContent.classList.add('scale-95', 'opacity-0');

    // Hide structure out of visibility index entirely after transition completes
    setTimeout(() => {
        detailsModal.classList.add('hidden');
    }, 150);
}

// Global Interaction Triggers
loadMoreBtn.addEventListener('click', () => fetchProducts(false));

categoryFilter.addEventListener('change', (e) => {
    currentCategory = e.target.value;
    fetchProducts(true);
});

closeModalBtn.addEventListener('click', closeModal);

// Clicking anywhere on the blurred backdrop background closes it down too
detailsModal.addEventListener('click', (e) => {
    if (e.target === detailsModal) closeModal();
});

// App Initialization entrypoint
fetchProducts(true);