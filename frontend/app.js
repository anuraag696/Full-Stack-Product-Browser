const API_BASE_URL = 'https://full-stack-product-browser.onrender.com/api/products';
const LIMIT = 24;

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

// Fetch products from backend API
async function fetchProducts(resetGrid = false) {
    if (resetGrid) {
        productGrid.innerHTML = '';
        nextCursor = null;
        setVisible(loadMoreBtn, false);
        setVisible(noMoreContainer, false);
    }

    setVisible(loadingSpinner, true);
    setVisible(loadMoreBtn, false);

    try {
        const url = buildApiUrl(API_BASE_URL, {
            limit: LIMIT,
            category: currentCategory,
            cursor: nextCursor
        });

        const response = await fetch(url);
        if (!response.ok) throw new Error('Network response failed.');

        const result = await response.json();

        renderProducts(result.data);

        nextCursor = result.next_cursor;

        if (result.has_more && nextCursor) {
            setVisible(loadMoreBtn, true);
        } else if (result.data.length > 0) {
            setVisible(noMoreContainer, true);
        } else {
            productGrid.innerHTML = `
                <div class="col-span-full text-center py-12 text-gray-400 italic">
                    No products found matching this filter combo.
                </div>
            `;
        }
    } catch (error) {
        console.error('Error fetching data:', error);
        productGrid.innerHTML += `
            <div class="col-span-full text-center py-4 text-red-500 font-medium">
                Failed to communicate with local backend API. Ensure Uvicorn is running.
            </div>
        `;
    } finally {
        setVisible(loadingSpinner, false);
    }
}

// Render products into grid
function renderProducts(products) {
    products.forEach(product => {
        const formattedDate = formatDate(product.created_at);
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

        card.querySelector('.view-details-btn').addEventListener('click', () => {
            openModal(product, formattedDate, pricingString);
        });

        productGrid.appendChild(card);
    });
}

// Open modal with product details
function openModal(product, dateStr, priceStr) {
    document.getElementById('modalCategory').innerText = product.category;
    document.getElementById('modalName').innerText = product.name;
    document.getElementById('modalId').innerText = `#${product.id}`;
    document.getElementById('modalDate').innerText = dateStr;
    document.getElementById('modalPrice').innerText = priceStr;

    setVisible(detailsModal, true);

    setTimeout(() => {
        setModalAnimationState(modalContent, true);
    }, 20);
}

// Close modal with animation
function closeModal() {
    setModalAnimationState(modalContent, false);

    setTimeout(() => {
        setVisible(detailsModal, false);
    }, 150);
}

// Event listeners
loadMoreBtn.addEventListener('click', () => fetchProducts(false));

categoryFilter.addEventListener('change', (e) => {
    currentCategory = e.target.value;
    fetchProducts(true);
});

closeModalBtn.addEventListener('click', closeModal);

detailsModal.addEventListener('click', (e) => {
    if (e.target === detailsModal) closeModal();
});

// App initialization
fetchProducts(true);
